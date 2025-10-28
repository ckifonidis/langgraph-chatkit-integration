"""
Base classes for rule-based custom components.

Components are reusable widgets that automatically render based on rules
applied to LangGraph response data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from chatkit.widgets import Card


class CustomComponent(ABC):
    """
    Abstract base class for rule-based components.

    Components define:
    1. Rules - When the component should render (check_rules)
    2. Rendering - How to create the widget (render)

    Example:
        >>> class MyComponent(CustomComponent):
        ...     def check_rules(self, response_data):
        ...         return "special_data" in response_data
        ...
        ...     def render(self, response_data):
        ...         return Card(children=[...])
    """

    @abstractmethod
    def check_rules(self, response_data: dict[str, Any]) -> bool:
        """
        Determine if this component should be rendered.

        Args:
            response_data: Full response dictionary from LangGraph.
                          Typically contains: messages, query_results, sql_query, etc.

        Returns:
            True if this component should render, False otherwise.

        Example:
            >>> def check_rules(self, response_data):
            ...     # Only render if we have query results
            ...     return len(response_data.get("query_results", [])) > 0
        """
        pass

    @abstractmethod
    def render(self, response_data: dict[str, Any]) -> Card | None:
        """
        Create the widget from response data.

        Args:
            response_data: Full response dictionary from LangGraph

        Returns:
            A ChatKit widget (typically Card), or None if rendering fails.

        Example:
            >>> def render(self, response_data):
            ...     data = response_data["query_results"]
            ...     return create_carousel(items=data)
        """
        pass

    def get_priority(self) -> int:
        """
        Get the priority of this component (lower = higher priority).

        Components with lower priority values render first.
        Default priority is 100.

        Returns:
            Integer priority value (0-1000)
        """
        return 100
