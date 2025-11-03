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
        # Global description cache (property_code -> description) - shared across all users
        self._global_description_cache: Dict[str, str] = {}
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
    def get_preferences(self, user_id: str, thread_id: str) -> Dict[str, Any]:
        """
        Get thread-specific user preferences (favorites, hidden properties).

        Args:
            user_id: The user ID from session
            thread_id: The thread ID (conversation ID)

        Returns:
            Dictionary with favorites and hidden dicts for this thread
        """
        # Ensure user exists in preferences
        if user_id not in self._preferences:
            self._preferences[user_id] = {}

        # Return thread-specific preferences, or default empty structure
        return self._preferences[user_id].get(thread_id, {
            'favorites': {},
            'hidden': {},
            'version': 3  # v3 = thread-specific schema
        })

    def update_preferences(self, user_id: str, thread_id: str, preferences: Dict[str, Any]) -> None:
        """
        Update entire thread-specific preferences dictionary.

        Args:
            user_id: The user ID from session
            thread_id: The thread ID (conversation ID)
            preferences: Complete preferences dictionary for this thread
        """
        if user_id not in self._preferences:
            self._preferences[user_id] = {}
        self._preferences[user_id][thread_id] = preferences

    def add_favorite(self, user_id: str, property_code: str, property_data: Dict[str, Any], thread_id: str) -> None:
        """
        Add a property to thread-specific favorites with full property data.

        Args:
            user_id: The user ID from session
            property_code: Property code to favorite
            property_data: Complete property object (title, price, image, etc.)
            thread_id: The thread ID (conversation ID)
        """
        prefs = self.get_preferences(user_id, thread_id)
        prefs['favorites'][property_code] = property_data
        self.update_preferences(user_id, thread_id, prefs)

    def remove_favorite(self, user_id: str, property_code: str, thread_id: str) -> None:
        """
        Remove a property from thread-specific favorites.

        Args:
            user_id: The user ID from session
            property_code: Property code to unfavorite
            thread_id: The thread ID (conversation ID)
        """
        prefs = self.get_preferences(user_id, thread_id)
        if property_code in prefs['favorites']:
            del prefs['favorites'][property_code]
        self.update_preferences(user_id, thread_id, prefs)

    def hide_property(self, user_id: str, property_code: str, property_data: Dict[str, Any], thread_id: str) -> None:
        """
        Add a property to thread-specific hidden list with full property data.

        Args:
            user_id: The user ID from session
            property_code: Property code to hide
            property_data: Complete property object (title, price, image, etc.)
            thread_id: The thread ID (conversation ID)
        """
        prefs = self.get_preferences(user_id, thread_id)
        prefs['hidden'][property_code] = property_data
        self.update_preferences(user_id, thread_id, prefs)

    def unhide_property(self, user_id: str, property_code: str, thread_id: str) -> None:
        """
        Remove a property from thread-specific hidden list.

        Args:
            user_id: The user ID from session
            property_code: Property code to unhide
            thread_id: The thread ID (conversation ID)
        """
        prefs = self.get_preferences(user_id, thread_id)
        if property_code in prefs['hidden']:
            del prefs['hidden'][property_code]
        self.update_preferences(user_id, thread_id, prefs)

    # -- Global Description Cache ----------------------------------------
    def get_global_description(self, property_code: str) -> str | None:
        """
        Get cached AI-generated description for a property (global, shared across all users).

        Args:
            property_code: Property code (e.g., "00000527")

        Returns:
            Cached description text, or None if not cached
        """
        return self._global_description_cache.get(property_code)

    def cache_global_description(self, property_code: str, description: str) -> None:
        """
        Cache an AI-generated description globally (shared across all users).

        Args:
            property_code: Property code (e.g., "00000527")
            description: Generated description text
        """
        self._global_description_cache[property_code] = description

    def clear_global_description_cache(self) -> None:
        """
        Clear the entire global description cache.

        Useful for testing or admin operations.
        """
        self._global_description_cache.clear()

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
