"""
Custom Components - Rule-based widget system for LangGraph responses.

This module provides a registry-based system for automatically rendering
widgets based on LangGraph response data.

Usage:
    >>> from custom_components import ComponentRegistry
    >>> from custom_components.property_carousel import PropertyCarouselComponent
    >>>
    >>> registry = ComponentRegistry()
    >>> registry.register(PropertyCarouselComponent())
    >>>
    >>> # Get widgets for a response
    >>> widgets = registry.get_widgets(langgraph_response_data)
    >>> for widget in widgets:
    ...     yield ThreadItemDoneEvent(item=WidgetItem(..., widget=widget))
"""

from __future__ import annotations

import logging
from typing import Any

from chatkit.widgets import Card

from .base import CustomComponent

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """
    Registry for managing and executing custom components.

    Components are checked in priority order (lowest priority number first).
    Multiple components can render from the same response data.
    """

    def __init__(self):
        """Initialize the component registry."""
        self.components: list[CustomComponent] = []

    def register(self, component: CustomComponent) -> None:
        """
        Register a component in the registry.

        Components are sorted by priority after registration.

        Args:
            component: The component instance to register

        Example:
            >>> registry = ComponentRegistry()
            >>> registry.register(PropertyCarouselComponent())
            >>> registry.register(SummaryTextComponent())
        """
        self.components.append(component)
        # Sort by priority (lower priority number = higher priority)
        self.components.sort(key=lambda c: c.get_priority())
        logger.info(f"Registered component: {component.__class__.__name__}")

    def get_widgets(self, response_data: dict[str, Any], user_preferences: dict[str, Any] | None = None) -> list[Card]:
        """
        Get all widgets that should render for the given response data.

        Checks each registered component's rules and renders matching widgets.

        Args:
            response_data: Full response dictionary from LangGraph
            user_preferences: Optional user preferences (favorites, hidden) from backend store

        Returns:
            List of widgets to display (may be empty)

        Example:
            >>> widgets = registry.get_widgets({
            ...     "query_results": [...],
            ...     "sql_query": {...}
            ... }, user_preferences={'favorites': ['P123'], 'hidden': ['P456']})
            >>> # widgets = [PropertyCarousel(...)]
        """
        widgets = []

        for component in self.components:
            try:
                # Check if component rules match
                if component.check_rules(response_data):
                    logger.debug(
                        f"Component {component.__class__.__name__} rules matched"
                    )

                    # Render the widget with user preferences
                    widget = component.render(response_data, user_preferences=user_preferences)

                    if widget is not None:
                        widgets.append(widget)
                        logger.info(
                            f"Component {component.__class__.__name__} rendered widget"
                        )
                    else:
                        logger.warning(
                            f"Component {component.__class__.__name__} returned None"
                        )

            except Exception as e:
                logger.error(
                    f"Error in component {component.__class__.__name__}: {e}",
                    exc_info=True,
                )
                # Continue processing other components
                continue

        logger.info(f"Generated {len(widgets)} widgets from {len(self.components)} components")
        return widgets


__all__ = ["ComponentRegistry", "CustomComponent"]
