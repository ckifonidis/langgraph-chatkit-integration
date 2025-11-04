# custom_components

## Purpose
Extensible rule-based widget rendering system that automatically generates ChatKit UI components based on LangGraph response structure, enabling rich interactive visualizations without hardcoding widget logic.

## Key Files
- **`__init__.py`**: Exports `ComponentRegistry` (component manager) and `CustomComponent` (base class)
- **`base.py`**: Abstract base class defining component lifecycle: `check_rules()` (when to render) and `render()` (how to render)
- **`property_carousel.py`**: `PropertyCarouselComponent` - Auto-renders property ListView when `query_results` exists, includes hidden property filtering
- **`filters_card.py`**: `FiltersCardComponent` - Displays active search filters as badges when `selected_filters` exists
- **`widgets.py`**: Reusable widget builder functions (`create_property_listview`, `create_favorite_button`, `create_hide_button`)

## Dependencies

### External
- `chatkit.widgets` - ChatKit widget primitives (Card, ListView, Button, Badge, Row, Col, etc.)
- `chatkit.actions` - ActionConfig for button click handlers

### Internal
- `../chatkit_langgraph` - Server integration via `ComponentRegistry.get_widgets()` called from `LangGraphChatKitServer.respond()`

## Architecture Notes

### Component Lifecycle
1. **Registration**: Components added to registry in `app/main.py` via `registry.register(MyComponent())`
2. **Rule Checking**: After LangGraph responds, registry calls `check_rules(response_data)` on each component
3. **Rendering**: Matching components call `render(response_data, user_preferences)` to create widgets
4. **Yielding**: Server wraps widgets in `ThreadItemDoneEvent` and streams to frontend

### Priority System
- Components sorted by `get_priority()` (lower = higher priority, default: 100)
- Multiple components can render from same response (not mutually exclusive)
- Rendering order: Filters card → Property carousel → Custom components

### User Preferences Integration
- Components receive `user_preferences` dict with `{'favorites': {code: {...}}, 'hidden': {code: {...}}}`
- PropertyCarousel filters out hidden properties before rendering
- Widget buttons (favorite/hide) emit server-side actions handled by `LangGraphChatKitServer.action()`

### Widget Builder Pattern
- `widgets.py` provides reusable functions (not classes) for common UI patterns
- Builders accept structured data + user preferences, return ChatKit widget instances
- Example: `create_property_listview(items, limit, favorites)` → `ListView`

## Usage

### Creating a Custom Component
```python
from custom_components.base import CustomComponent
from chatkit.widgets import Card, Text

class SummaryComponent(CustomComponent):
    def check_rules(self, response_data):
        return "summary" in response_data

    def render(self, response_data, user_preferences=None):
        return Card(children=[
            Text(text=response_data["summary"])
        ])

    def get_priority(self):
        return 50  # Render before default (100)
```

### Registering Components
```python
# In app/main.py
from custom_components import ComponentRegistry
from custom_components.property_carousel import PropertyCarouselComponent

registry = ComponentRegistry()
registry.register(PropertyCarouselComponent(max_items=20))
registry.register(SummaryComponent())

server = create_server_from_env(component_registry=registry)
```

### Server Integration Flow
```python
# In chatkit_langgraph/server.py respond() method
widgets = self.component_registry.get_widgets(
    final_event,
    user_preferences=user_preferences
)

for widget in widgets:
    yield ThreadItemDoneEvent(
        item=WidgetItem(id=_gen_id("wi"), widget=widget)
    )
```

## Component Design Best Practices

### Rule Design
- **Specific**: Check for exact field presence (e.g., `"query_results" in response_data`)
- **Type Safe**: Validate types (`isinstance(data, list)`)
- **Non-Empty**: Ensure data has content (`len(query_results) > 0`)

### Rendering Guidelines
- **Null Safety**: Return `None` if rendering fails (registry continues processing others)
- **User Preferences**: Always accept `user_preferences` parameter (may be `None`)
- **Filtering**: Apply hidden/favorite logic before creating widgets
- **Logging**: Use `logger.debug()` for rule matches, `logger.error()` for failures

### Widget Structure
- **Semantic HTML**: Use Row/Col for layout, Card for containers
- **Accessibility**: Include icons (`Icon(icon="location")`) with meaningful labels
- **Actions**: Specify server-side actions (`handler` not specified → defaults to server)
- **Drilldown**: Use `onClickDetails` for item details, `onClickAction` for mutations

## Example Response Structures

### Property Search Response
```python
{
    "messages": [...],
    "query_results": [
        {
            "code": "PROP001",
            "title": "Maisonette 224sqm",
            "price": 115000,
            "propertyArea": 224,
            "defaultImagePath": "https://...",
            "address": {"prefecture": "Chalkidiki", "geoPoint": {...}}
        }
    ],
    "selected_filters": [
        "Prefecture: Chalkidiki",
        "Type: Maisonette"
    ]
}
```

### Component Activation
- `PropertyCarouselComponent`: Activates if `query_results` is non-empty list
- `FiltersCardComponent`: Activates if `selected_filters` is non-empty list

## Production Considerations
- **Component Registration Order**: Use priority system, not registration order
- **Error Isolation**: Registry catches exceptions per-component (one failure doesn't break others)
- **Performance**: Avoid expensive operations in `check_rules()` (called for every response)
- **Widget Limits**: Use `max_items` parameter to prevent massive ListViews (default: 20)
