"""
FiltersCardComponent - Displays active search filters as a styled card with badges.

This component renders when LangGraph returns selected_filters in the response.
"""

from typing import Any

from chatkit.widgets import Badge, Box, Card, Col, Row, Spacer, Text, Title

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

        # Build individual filter badges
        filter_badges = []
        for f in selected_filters:
            field_name = f.get("field_name", "")
            value = f.get("value", "")
            operator = f.get("operator", "eq")

            # Format the field name for display
            label = self._format_field_name(field_name)

            # Format the value with operator
            formatted_value = self._format_value(value, field_name, operator)

            filter_badges.append(
                Badge(
                    label=f"{label}: {formatted_value}",
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

    def _format_field_name(self, field_name: str) -> str:
        """
        Format field name for display.

        Converts database field names to human-readable labels.

        Args:
            field_name: Raw field name (e.g., "address.prefecture")

        Returns:
            Formatted label (e.g., "Location")
        """
        field_mapping = {
            "price": "Price",
            "type": "Type",
            "address.prefecture": "Location",
            "address.city": "City",
            "propertyArea": "Size",
            "numberOfRooms": "Bedrooms",
            "numberOfBathrooms": "Bathrooms",
            "floor": "Floor",
            "constructionYear": "Built",
            "energyClass": "Energy Class",
            "hasElevator": "Elevator",
            "hasPool": "Pool",
            "hasGarden": "Garden",
            "parkingType": "Parking",
        }

        return field_mapping.get(field_name, field_name.replace("_", " ").title())

    def _format_value(self, value: str, field_name: str, operator: str) -> str:
        """
        Format filter value with operator.

        Adds currency symbols, comparison operators, etc.

        Args:
            value: Raw filter value
            field_name: Field being filtered
            operator: Comparison operator (eq, lte, gte, etc.)

        Returns:
            Formatted value string
        """
        # Price formatting
        if field_name == "price":
            try:
                price_val = int(value)
                formatted_price = f"€{price_val:,}"

                if operator == "lte":
                    return f"≤{formatted_price}"
                elif operator == "gte":
                    return f"≥{formatted_price}"
                else:
                    return formatted_price
            except (ValueError, TypeError):
                return value

        # Area formatting
        if field_name == "propertyArea":
            try:
                area_val = int(value)
                if operator == "lte":
                    return f"≤{area_val}m²"
                elif operator == "gte":
                    return f"≥{area_val}m²"
                else:
                    return f"{area_val}m²"
            except (ValueError, TypeError):
                return value

        # Numeric fields
        if field_name in ["numberOfRooms", "numberOfBathrooms", "floor"]:
            if operator == "gte":
                return f"{value}+"
            elif operator == "lte":
                return f"≤{value}"

        # Default: return value as-is
        return value
