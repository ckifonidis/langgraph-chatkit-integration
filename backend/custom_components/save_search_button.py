"""
Save Search Button Component - Display a button to save the current search query.

This component automatically renders when LangGraph returns property query results.
"""

from __future__ import annotations

import uuid
from typing import Any

from chatkit.actions import ActionConfig
from chatkit.widgets import Button, Card, Row

from .base import CustomComponent


class SaveSearchButtonComponent(CustomComponent):
    """
    Renders a "Save This Search" button when query results are present.

    Rules:
    - Activates when response_data contains "query_results" and "_user_query"
    - query_results must be a non-empty list

    Rendering:
    - Creates a Button widget that saves the search query
    - Server-side action handler stores the query in user preferences
    """

    def check_rules(self, response_data: dict[str, Any]) -> bool:
        """
        Check if this component should render.

        Args:
            response_data: LangGraph response containing query_results and _user_query

        Returns:
            True if query_results exists and has items, and user query is present
        """
        query_results = response_data.get("query_results", [])
        user_query = response_data.get("_user_query", "")
        return (
            isinstance(query_results, list)
            and len(query_results) > 0
            and isinstance(user_query, str)
            and len(user_query.strip()) > 0
        )

    def render(self, response_data: dict[str, Any], user_preferences: dict[str, Any] | None = None) -> Card | None:
        """
        Create a Card with "Save This Search" button.

        Args:
            response_data: LangGraph response with query_results and _user_query fields
            user_preferences: Optional user preferences (not used by this component)

        Returns:
            Card widget with save button, or None if rendering fails
        """
        try:
            user_query = response_data.get("_user_query", "")

            # Generate unique search ID
            search_id = f"search_{uuid.uuid4().hex[:8]}"

            # Create save button
            save_button = Button(
                label="Save This Search",
                iconStart="star",
                size="sm",
                variant="outline",
                color="primary",
                onClickAction=ActionConfig(
                    type="save_search",
                    payload={
                        "query": user_query,
                        "searchId": search_id
                    }
                    # No handler specified - defaults to server-side
                )
            )

            # Wrap in Card for clean presentation
            return Card(
                children=[
                    Row(
                        gap=2,
                        align="center",
                        children=[save_button]
                    )
                ]
            )

        except Exception as e:
            # Log error but don't crash - return None to skip this component
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to render save search button: {e}", exc_info=True)
            return None

    def get_priority(self) -> int:
        """Save search button has lower priority than property carousel."""
        return 60  # Render after property carousel (priority 50)
