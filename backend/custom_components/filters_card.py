"""
FiltersCardComponent - Displays active search filters as pill-shaped chips.

This component renders when LangGraph returns selected_filters in the response.
"""

from typing import Any

from chatkit.actions import ActionConfig
from chatkit.widgets import Box, Button, Card, Row, Text

from .base import CustomComponent


class FiltersCardComponent(CustomComponent):
    """
    Renders a card displaying active search filters as pill-shaped chips.

    Each filter appears as a rounded pill with a remove button.
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
        Render the filters card with pill-shaped chips.

        Args:
            response_data: LangGraph response containing selected_filters
            user_preferences: User preferences (not used)

        Returns:
            Card widget with filter pills, or None if no filters
        """
        selected_filters = response_data.get("selected_filters", [])

        if not selected_filters:
            return None

        # Build individual filter pills with X buttons
        filter_pills = []
        for f in selected_filters:
            explanation = f.get("filter_explanation", "Unknown filter")
            filter_pills.append(
                Box(
                    border=1,
                    radius="full",
                    padding={"x": 2, "y": 1},
                    background="surface",
                    children=[
                        Row(
                            gap=2,
                            align="center",
                            children=[
                                Text(value=explanation, size="sm"),
                                Button(
                                    label="×",
                                    size="sm",
                                    variant="soft",
                                    color="secondary",
                                    uniform=True,
                                    onClickAction=ActionConfig(
                                        type="remove_filter",
                                        payload={"filter_name": explanation},
                                    ),
                                ),
                            ],
                        )
                    ],
                )
            )

        return Card(
            size="sm",
            padding=2,
            children=[Box(direction="row", wrap="wrap", gap=2, children=filter_pills)],
        )

    def get_priority(self) -> int:
        """
        Return component priority.

        Priority 45 ensures this renders before property carousel (priority 50).
        Lower number = higher priority.
        """
        return 45
