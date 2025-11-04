"""
FiltersCardComponent - Displays active search filters as a styled card with badges.

This component renders when LangGraph returns selected_filters in the response.
"""

from typing import Any

from chatkit.widgets import Badge, Box, Card, Col, Row, Spacer, Title

from .base import CustomComponent


class FiltersCardComponent(CustomComponent):
    """
    Renders a card displaying active search filters with badges.

    Shows a summary line plus individual filter badges for each criterion.
    Activates when selected_filters array exists in the response.
    """

    def check_rules(self, response_data: dict[str, Any]) -> bool:
        """
        Check if this component should render.

        Activates when:
        - selected_filters exists
        - selected_filters is non-empty

        Args:
            response_data: LangGraph response data

        Returns:
            True if filters exist and should be displayed
        """
        selected_filters = response_data.get("selected_filters", [])
        return isinstance(selected_filters, list) and len(selected_filters) > 0

    def render(
        self,
        response_data: dict[str, Any],
        user_preferences: dict[str, Any] | None = None,
    ) -> Card | None:
        """
        Render the filters card with badges.

        Args:
            response_data: LangGraph response containing selected_filters
            user_preferences: User preferences (not used)

        Returns:
            Card widget with filter badges, or None if no filters
        """
        selected_filters = response_data.get("selected_filters", [])

        if not selected_filters:
            return None

        # Build individual filter badges using filter_explanation from LangGraph
        filter_badges = []
        for f in selected_filters:
            explanation = f.get("filter_explanation", "Unknown filter")
            filter_badges.append(
                Badge(
                    label=explanation,
                    color="secondary",
                    variant="soft",
                )
            )

        # Build card content
        children = [
            # Header row with title and count badge
            Row(
                align="center",
                children=[
                    Title(value="Filters applied", size="sm"),
                    Spacer(),
                    Badge(
                        label=str(len(selected_filters)),
                        color="info",
                        variant="soft",
                    ),
                ],
            ),
        ]

        # Add filter badges in wrapped row
        children.append(
            Box(direction="row", wrap="wrap", gap=2, children=filter_badges)
        )

        return Card(size="sm", children=[Col(gap=3, children=children)])

    def get_priority(self) -> int:
        """
        Return component priority.

        Priority 45 ensures this renders before property carousel (priority 50).
        Lower number = higher priority.
        """
        return 45
