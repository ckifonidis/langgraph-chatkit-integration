from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, Thread, ThreadItem, ThreadMetadata


@dataclass
class _ThreadState:
    thread: ThreadMetadata
    items: List[ThreadItem]


class MemoryStore(Store[dict[str, Any]]):
    """Simple in-memory store compatible with the ChatKit server interface."""

    def __init__(self) -> None:
        self._threads: Dict[str, _ThreadState] = {}
        # Map user_id -> set of thread_ids
        self._user_threads: Dict[str, set[str]] = {}
        # Map user_id -> user preferences (favorites, hidden)
        self._preferences: Dict[str, Dict[str, Any]] = {}
        # Attachments intentionally unsupported; use a real store that enforces auth.

    @staticmethod
    def _coerce_thread_metadata(thread: ThreadMetadata | Thread) -> ThreadMetadata:
        """Return thread metadata without any embedded items (openai-chatkit>=1.0)."""
        has_items = isinstance(thread, Thread) or "items" in getattr(
            thread, "model_fields_set", set()
        )
        if not has_items:
            return thread.model_copy(deep=True)

        data = thread.model_dump()
        data.pop("items", None)
        return ThreadMetadata(**data).model_copy(deep=True)

    # -- Thread metadata -------------------------------------------------
    async def load_thread(self, thread_id: str, context: dict[str, Any]) -> ThreadMetadata:
        state = self._threads.get(thread_id)
        if not state:
            # Auto-create thread if it doesn't exist (prevents race conditions)
            new_thread = ThreadMetadata(
                id=thread_id,
                created_at=datetime.now(),
                status={"type": "active"},
                metadata={},
            )
            await self.save_thread(new_thread, context)
            return new_thread
        return self._coerce_thread_metadata(state.thread)

    async def save_thread(self, thread: ThreadMetadata, context: dict[str, Any]) -> None:
        metadata = self._coerce_thread_metadata(thread)
        state = self._threads.get(thread.id)
        if state:
            state.thread = metadata
        else:
            self._threads[thread.id] = _ThreadState(
                thread=metadata,
                items=[],
            )

        # Associate thread with user
        user_id = context.get("user_id", "anonymous")
        if user_id not in self._user_threads:
            self._user_threads[user_id] = set()
        self._user_threads[user_id].add(thread.id)

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadMetadata]:
        # Filter threads by user
        user_id = context.get("user_id", "anonymous")
        user_thread_ids = self._user_threads.get(user_id, set())

        # Only include threads that belong to this user
        threads = sorted(
            (
                self._coerce_thread_metadata(state.thread)
                for thread_id, state in self._threads.items()
                if thread_id in user_thread_ids
            ),
            key=lambda t: t.created_at or datetime.min,
            reverse=(order == "desc"),
        )

        if after:
            index_map = {thread.id: idx for idx, thread in enumerate(threads)}
            start = index_map.get(after, -1) + 1
        else:
            start = 0

        slice_threads = threads[start : start + limit + 1]
        has_more = len(slice_threads) > limit
        slice_threads = slice_threads[:limit]
        next_after = slice_threads[-1].id if has_more and slice_threads else None
        return Page(
            data=slice_threads,
            has_more=has_more,
            after=next_after,
        )

    async def delete_thread(self, thread_id: str, context: dict[str, Any]) -> None:
        self._threads.pop(thread_id, None)

        # Remove from user mapping
        user_id = context.get("user_id", "anonymous")
        if user_id in self._user_threads:
            self._user_threads[user_id].discard(thread_id)

    # -- Thread items ----------------------------------------------------
    def _items(self, thread_id: str) -> List[ThreadItem]:
        state = self._threads.get(thread_id)
        if state is None:
            state = _ThreadState(
                thread=ThreadMetadata(id=thread_id, created_at=datetime.utcnow()),
                items=[],
            )
            self._threads[thread_id] = state
        return state.items

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadItem]:
        items = [item.model_copy(deep=True) for item in self._items(thread_id)]
        items.sort(
            key=lambda item: getattr(item, "created_at", datetime.utcnow()),
            reverse=(order == "desc"),
        )

        if after:
            index_map = {item.id: idx for idx, item in enumerate(items)}
            start = index_map.get(after, -1) + 1
        else:
            start = 0

        slice_items = items[start : start + limit + 1]
        has_more = len(slice_items) > limit
        slice_items = slice_items[:limit]
        next_after = slice_items[-1].id if has_more and slice_items else None
        return Page(data=slice_items, has_more=has_more, after=next_after)

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        self._items(thread_id).append(item.model_copy(deep=True))

    async def save_item(self, thread_id: str, item: ThreadItem, context: dict[str, Any]) -> None:
        items = self._items(thread_id)
        for idx, existing in enumerate(items):
            if existing.id == item.id:
                items[idx] = item.model_copy(deep=True)
                return
        items.append(item.model_copy(deep=True))

    async def load_item(self, thread_id: str, item_id: str, context: dict[str, Any]) -> ThreadItem:
        for item in self._items(thread_id):
            if item.id == item_id:
                return item.model_copy(deep=True)
        raise NotFoundError(f"Item {item_id} not found")

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> None:
        items = self._items(thread_id)
        self._threads[thread_id].items = [item for item in items if item.id != item_id]

    # -- User Preferences ------------------------------------------------
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences (favorites, hidden properties, saved searches).

        Args:
            user_id: The user ID from session

        Returns:
            Dictionary with favorites, hidden, and saved_searches dicts
        """
        return self._preferences.get(user_id, {
            'favorites': {},
            'hidden': {},
            'saved_searches': {},
            'version': 2
        })

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """
        Update entire user preferences dictionary.

        Args:
            user_id: The user ID from session
            preferences: Complete preferences dictionary
        """
        self._preferences[user_id] = preferences

    def add_favorite(self, user_id: str, property_code: str, property_data: Dict[str, Any]) -> None:
        """
        Add a property to user's favorites with full property data.

        Args:
            user_id: The user ID from session
            property_code: Property code to favorite
            property_data: Complete property object (title, price, image, etc.)
        """
        prefs = self.get_preferences(user_id)
        prefs['favorites'][property_code] = property_data
        self._preferences[user_id] = prefs

    def remove_favorite(self, user_id: str, property_code: str) -> None:
        """
        Remove a property from user's favorites.

        Args:
            user_id: The user ID from session
            property_code: Property code to unfavorite
        """
        prefs = self.get_preferences(user_id)
        if property_code in prefs['favorites']:
            del prefs['favorites'][property_code]
        self._preferences[user_id] = prefs

    def hide_property(self, user_id: str, property_code: str, property_data: Dict[str, Any]) -> None:
        """
        Add a property to user's hidden list with full property data.

        Args:
            user_id: The user ID from session
            property_code: Property code to hide
            property_data: Complete property object (title, price, image, etc.)
        """
        prefs = self.get_preferences(user_id)
        prefs['hidden'][property_code] = property_data
        self._preferences[user_id] = prefs

    def unhide_property(self, user_id: str, property_code: str) -> None:
        """
        Remove a property from user's hidden list.

        Args:
            user_id: The user ID from session
            property_code: Property code to unhide
        """
        prefs = self.get_preferences(user_id)
        if property_code in prefs['hidden']:
            del prefs['hidden'][property_code]
        self._preferences[user_id] = prefs

    def save_search(self, user_id: str, search_id: str, query: str, metadata: Dict[str, Any] = None) -> None:
        """
        Save a search query for quick re-running later.

        Args:
            user_id: The user ID from session
            search_id: Unique identifier for this saved search
            query: The search query text
            metadata: Optional metadata (filters, etc.)
        """
        prefs = self.get_preferences(user_id)
        if 'saved_searches' not in prefs:
            prefs['saved_searches'] = {}

        prefs['saved_searches'][search_id] = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self._preferences[user_id] = prefs

    def delete_saved_search(self, user_id: str, search_id: str) -> None:
        """
        Delete a saved search.

        Args:
            user_id: The user ID from session
            search_id: Unique identifier of the saved search to delete
        """
        prefs = self.get_preferences(user_id)
        if 'saved_searches' in prefs and search_id in prefs['saved_searches']:
            del prefs['saved_searches'][search_id]
        self._preferences[user_id] = prefs

    def get_saved_searches(self, user_id: str) -> Dict[str, Any]:
        """
        Get all saved searches for a user.

        Args:
            user_id: The user ID from session

        Returns:
            Dictionary of search_id -> search_data
        """
        prefs = self.get_preferences(user_id)
        return prefs.get('saved_searches', {})

    # -- Files -----------------------------------------------------------
    # These methods are not currently used but required to be compatible with the Store interface.

    async def save_attachment(
        self,
        attachment: Attachment,
        context: dict[str, Any],
    ) -> None:
        raise NotImplementedError(
            "MemoryStore does not persist attachments. Provide a Store implementation "
            "that enforces authentication and authorization before enabling uploads."
        )

    async def load_attachment(
        self,
        attachment_id: str,
        context: dict[str, Any],
    ) -> Attachment:
        raise NotImplementedError(
            "MemoryStore does not load attachments. Provide a Store implementation "
            "that enforces authentication and authorization before enabling uploads."
        )

    async def delete_attachment(self, attachment_id: str, context: dict[str, Any]) -> None:
        raise NotImplementedError(
            "MemoryStore does not delete attachments because they are never stored."
        )
