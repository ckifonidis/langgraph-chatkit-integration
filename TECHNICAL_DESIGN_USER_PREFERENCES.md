# Technical Design: User Preferences System (Favorites & Hidden Properties)

**Document Version:** 1.0
**Date:** 2025-10-30
**Status:** Proposed Design

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Requirements](#requirements)
3. [Current Architecture Analysis](#current-architecture-analysis)
4. [Solution Architecture](#solution-architecture)
5. [Implementation Approaches](#implementation-approaches)
6. [Recommended Solution](#recommended-solution)
7. [Data Models](#data-models)
8. [Component Specifications](#component-specifications)
9. [Integration Points](#integration-points)
10. [Migration Path](#migration-path)
11. [Security Considerations](#security-considerations)
12. [Testing Strategy](#testing-strategy)

---

## Executive Summary

This document proposes a **localStorage-based user preferences system** for managing favorite and hidden properties in the Uniko Property Assistant application. The solution prioritizes simplicity, fast iteration, and maintainability while providing a clear upgrade path to backend persistence.

**Key Decisions:**
- ✅ **localStorage** for persistence (browser-only)
- ✅ **Client-side action handlers** for favorite/hide buttons
- ✅ **Replace `useFacts`** with `useUserPreferences` hook
- ✅ **Filter hidden properties** in frontend rendering
- ✅ **No new npm dependencies** required

---

## Requirements

### Functional Requirements

1. **Favorite Properties**
   - Users can favorite/unfavorite properties from carousel and detail modal
   - Favorited properties appear in "Saved Properties" section (replacing current implementation)
   - Favorites persist across browser sessions
   - Visual indicator shows favorited status

2. **Hide Properties**
   - Users can hide properties from carousel and detail modal
   - Hidden properties are completely filtered from future search results
   - Users can view and unhide properties from a "Hidden Properties" list
   - Hidden status persists across browser sessions

3. **UI Integration**
   - Favorite/hide buttons appear on property carousel cards
   - Favorite/hide buttons appear in property detail modal
   - "Saved Properties" section shows favorited properties (Home component)

### Non-Functional Requirements

1. **Performance:** Preference reads/writes must be < 10ms
2. **Persistence:** Preferences survive browser refresh (not cleared on logout)
3. **Capacity:** Support up to 1000 favorites + 1000 hidden properties per user
4. **Compatibility:** Work with existing session-based architecture
5. **Maintainability:** Easy to upgrade to backend storage later

---

## Current Architecture Analysis

### Frontend State Management

**Current Pattern:**
```typescript
// frontend/src/hooks/useColorScheme.ts
export function useColorScheme() {
  const [scheme, setScheme] = useState<ColorScheme>(getInitialScheme);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, scheme);
  }, [scheme]);

  return { scheme, toggle, setScheme };
}
```

**Key Findings:**
- ✅ No state management library (Redux, Zustand, etc.)
- ✅ Pattern: `useState` + `useEffect` + `localStorage`
- ✅ Existing implementation: `useColorScheme` (theme), `useFacts` (saved properties)
- ❌ `useFacts` is **in-memory only** (data lost on refresh)

### Backend Architecture

**Session Management:**
```python
# backend/app/main.py
@app.post("/langgraph/chatkit")
async def chatkit_endpoint(request: Request):
    if "user_id" not in request.session:
        request.session["user_id"] = str(uuid.uuid4())

    user_id = request.session["user_id"]
    # user_id available in context for all handlers
```

**Action Handling:**
```python
# backend/chatkit_langgraph/server.py
async def action(
    self,
    thread: ThreadMetadata,
    action: Any,
    sender: WidgetItem | None,
    context: dict[str, Any],
) -> AsyncIterator[ThreadStreamEvent]:
    """Handle widget actions (currently: view_item_details)"""

    if action.type == "view_item_details":
        # Renders property detail card
        yield ThreadItemDoneEvent(item=widget_item)
```

**Key Findings:**
- ✅ Backend can handle widget actions via `action()` method
- ✅ Session-based `user_id` available in all handlers
- ✅ Actions can be client-side (`handler="client"`) or server-side
- ✅ Current storage: `MemoryStore` (in-memory, marked for replacement)

### ChatKit Widget Action System

**Client-Side Actions:**
```typescript
// frontend/src/components/ChatKitPanel.tsx
const { control } = useChatKit({
  widgets: {
    onAction: async (action, widgetItem) => {
      if (action.type === 'view_property_modal') {
        // Handle in frontend
        setSelectedProperty(action.payload.property);
      }
    }
  }
});
```

**Server-Side Actions:**
```python
# backend/custom_components/property_carousel.py
Button(
    label="View",
    onClickAction=ActionConfig(
        type="view_item_details",
        payload={"item_data": property_data},
        handler="server"  # Send to backend action() handler
    )
)
```

**Key Findings:**
- ✅ Actions can be routed to client (`handler="client"`) or server (`handler="server"`)
- ✅ Client actions handled in `widgets.onAction` callback
- ✅ Server actions handled in `server.action()` method
- ✅ Actions can update widgets, show modals, or fetch data

---

## Solution Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ useUserPreferences Hook                              │  │
│  │ ┌────────────────────────────────────────────────┐   │  │
│  │ │ State: favorites[], hidden[]                   │   │  │
│  │ │ Methods: toggleFavorite, hideProperty          │   │  │
│  │ │ Storage: localStorage (uniko_preferences)      │   │  │
│  │ └────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│         ┌───────────────┴───────────────┐                   │
│         ▼                               ▼                   │
│  ┌─────────────┐                 ┌─────────────┐           │
│  │ ChatKitPanel│                 │    Home     │           │
│  │  (Widget    │                 │ (Saved Props│           │
│  │   Actions)  │                 │   Display)  │           │
│  └─────────────┘                 └─────────────┘           │
│         │                                                   │
│         │ Client-side action handling                      │
│         │ (toggle_favorite, hide_property)                 │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ localStorage: uniko_preferences                       │  │
│  │ { favorites: ["code1", "code2"], hidden: ["code3"] } │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Backend (ChatKit Server)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PropertyCarouselComponent                            │  │
│  │ - Renders property cards with favorite/hide buttons  │  │
│  │ - Buttons configured as client-side actions          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  NOTE: Backend does NOT filter hidden properties          │
│        Filtering happens in frontend before rendering      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Favorite Property Flow:**
```
1. User clicks favorite button on property card
   └─> Button has: onClickAction={type: "toggle_favorite", handler: "client"}

2. ChatKit routes to client-side handler
   └─> widgets.onAction(action: {type: "toggle_favorite", payload: {code: "ABC123"}})

3. Handler calls useUserPreferences hook
   └─> toggleFavorite("ABC123")

4. Hook updates state and localStorage
   └─> favorites: ["ABC123", ...]
   └─> localStorage.setItem("uniko_preferences", JSON.stringify({favorites, hidden}))

5. UI re-renders with updated favorite status
   └─> Button icon changes to filled heart
   └─> Property appears in "Saved Properties" section
```

**Hide Property Flow:**
```
1. User clicks hide button on property card
   └─> Button has: onClickAction={type: "hide_property", handler: "client"}

2. ChatKit routes to client-side handler
   └─> widgets.onAction(action: {type: "hide_property", payload: {code: "ABC123"}})

3. Handler calls useUserPreferences hook
   └─> hideProperty("ABC123")

4. Hook updates state and localStorage
   └─> hidden: ["ABC123", ...]

5. Frontend filters hidden properties
   └─> Property carousel component filters out hidden codes
   └─> Future search results exclude hidden properties
```

---

## Implementation Approaches

### Option A: localStorage Only (Frontend) ⭐ **RECOMMENDED**

**Architecture:**
- Custom React hook: `useUserPreferences`
- Storage: `localStorage` (key: `uniko_preferences`)
- Action handling: Client-side via `widgets.onAction`
- Widget updates: Backend adds favorite/hide buttons to property cards

**Pros:**
- ✅ Simplest implementation (~2-3 hours)
- ✅ No backend changes required (only widget button additions)
- ✅ Fast read/write (< 1ms)
- ✅ Works offline
- ✅ Follows existing pattern (`useColorScheme`)
- ✅ Easy to upgrade to backend storage later

**Cons:**
- ❌ Data tied to single browser (not synced across devices)
- ❌ Lost if user clears browser data
- ❌ Limited to ~5-10MB storage
- ❌ No analytics on user preferences

**Implementation Complexity:** Low (5/10)

---

### Option B: Backend Storage (Session-Based)

**Architecture:**
- Backend endpoints: `GET/POST /api/user/preferences`
- Storage: PostgreSQL/Redis (keyed by session `user_id`)
- Action handling: Server-side via `server.action()`
- React hook fetches/updates via API calls

**Pros:**
- ✅ Persists across browsers (tied to session)
- ✅ Can add analytics/insights
- ✅ Enables future user accounts
- ✅ Backup/restore capabilities

**Cons:**
- ❌ Requires backend changes (endpoints, database)
- ❌ Requires persistent storage (PostgreSQL/Redis)
- ❌ Network latency on reads/writes (50-200ms)
- ❌ More complex error handling
- ❌ Still session-based (not true multi-device until login added)

**Implementation Complexity:** High (8/10)

---

### Option C: Client Tools (ChatKit Feature)

**Architecture:**
- Backend defines client tools via LangGraph
- Frontend implements tool handlers
- Tools can read/write localStorage and send results to server

**Example:**
```python
# Backend defines tool
{
  "name": "toggle_favorite",
  "description": "Toggle favorite status for a property",
  "parameters": {"code": "string"}
}
```

```typescript
// Frontend implements handler
onClientTool: async ({name, params}) => {
  if (name === "toggle_favorite") {
    toggleFavorite(params.code);
    return {success: true};
  }
}
```

**Pros:**
- ✅ Declarative tool definitions
- ✅ Backend can trigger client-side actions
- ✅ Good for AI-driven workflows

**Cons:**
- ❌ Overkill for simple preference management
- ❌ Adds complexity to debugging
- ❌ Tightly couples backend and frontend

**Implementation Complexity:** Medium (6/10)

---

### Option D: Hybrid (localStorage + Backend Sync)

**Architecture:**
- Primary storage: `localStorage` (fast reads)
- Background sync: POST to backend every 30s or on change
- Conflict resolution: Last-write-wins

**Pros:**
- ✅ Fast local reads (< 1ms)
- ✅ Works offline
- ✅ Backend backup

**Cons:**
- ❌ Most complex implementation
- ❌ Sync conflict resolution needed
- ❌ Eventual consistency issues

**Implementation Complexity:** Very High (9/10)

---

## Recommended Solution

### ✅ **Option A: localStorage Only**

**Rationale:**
1. **Fastest time-to-market:** 2-3 hours vs 1-2 days for backend storage
2. **Consistent with existing patterns:** Follows `useColorScheme` implementation
3. **No infrastructure changes:** Works with current setup (no database needed)
4. **Easy migration path:** Hook interface stays same when upgrading to backend
5. **Current context:** Backend `MemoryStore` already marked for replacement in CLAUDE.md
   - Wait until backend storage is implemented for both threads AND preferences
   - Avoids doing storage migration twice

**When to Upgrade:**
- User accounts are added (need cross-device sync)
- Analytics on preferences are required
- Backend storage (PostgreSQL/Redis) is implemented for thread persistence

---

## Data Models

### Frontend Data Model

```typescript
// frontend/src/types/preferences.ts

export interface UserPreferences {
  favorites: string[];  // Array of property codes
  hidden: string[];     // Array of property codes
  version: number;      // Schema version for future migrations
}

export const DEFAULT_PREFERENCES: UserPreferences = {
  favorites: [],
  hidden: [],
  version: 1,
};

// localStorage key
export const PREFERENCES_STORAGE_KEY = "uniko_preferences";
```

### localStorage Structure

```json
{
  "favorites": ["PROP001", "PROP042", "PROP137"],
  "hidden": ["PROP999"],
  "version": 1
}
```

**Size Estimate:**
- Average property code: 7 chars
- 1000 favorites: ~7KB
- 1000 hidden: ~7KB
- **Total: ~14KB** (well under 5MB localStorage limit)

---

## Component Specifications

### 1. useUserPreferences Hook

**Location:** `frontend/src/hooks/useUserPreferences.ts`

**Interface:**
```typescript
export interface UseUserPreferencesReturn {
  // State
  favorites: string[];
  hidden: string[];
  loading: boolean;

  // Computed
  isFavorite: (code: string) => boolean;
  isHidden: (code: string) => boolean;

  // Actions
  toggleFavorite: (code: string) => void;
  addFavorite: (code: string) => void;
  removeFavorite: (code: string) => void;
  hideProperty: (code: string) => void;
  unhideProperty: (code: string) => void;
  clearHidden: () => void;
}

export function useUserPreferences(): UseUserPreferencesReturn;
```

**Implementation Pattern:**
```typescript
export function useUserPreferences() {
  const [preferences, setPreferences] = useState<UserPreferences>(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem(PREFERENCES_STORAGE_KEY);
    return stored ? JSON.parse(stored) : DEFAULT_PREFERENCES;
  });

  // Persist to localStorage on change
  useEffect(() => {
    localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
  }, [preferences]);

  const toggleFavorite = useCallback((code: string) => {
    setPreferences(prev => ({
      ...prev,
      favorites: prev.favorites.includes(code)
        ? prev.favorites.filter(c => c !== code)
        : [...prev.favorites, code]
    }));
  }, []);

  const isFavorite = useCallback(
    (code: string) => preferences.favorites.includes(code),
    [preferences.favorites]
  );

  // ... other methods

  return { favorites, hidden, isFavorite, isHidden, toggleFavorite, ... };
}
```

---

### 2. ChatKitPanel Action Handler

**Location:** `frontend/src/components/ChatKitPanel.tsx`

**Changes:**
```typescript
import { useUserPreferences } from '../hooks/useUserPreferences';

export function ChatKitPanel() {
  const preferences = useUserPreferences();

  const { control } = useChatKit({
    widgets: {
      onAction: async (action, widgetItem) => {
        // Existing handlers
        if (action.type === 'view_property_modal') { ... }

        // NEW: Handle favorite toggle
        if (action.type === 'toggle_favorite') {
          const code = action.payload?.propertyCode;
          if (code) {
            preferences.toggleFavorite(code);
          }
          return;
        }

        // NEW: Handle hide property
        if (action.type === 'hide_property') {
          const code = action.payload?.propertyCode;
          if (code) {
            preferences.hideProperty(code);
          }
          return;
        }
      }
    }
  });

  // Pass preferences to PropertyDetailModal
  return (
    <>
      <ChatKit control={control} />
      {selectedProperty && (
        <PropertyDetailModal
          property={selectedProperty}
          isFavorite={preferences.isFavorite(selectedProperty.code)}
          onToggleFavorite={() => preferences.toggleFavorite(selectedProperty.code)}
          onHide={() => {
            preferences.hideProperty(selectedProperty.code);
            setSelectedProperty(null);
          }}
          onClose={() => setSelectedProperty(null)}
        />
      )}
    </>
  );
}
```

---

### 3. Home Component (Saved Properties)

**Location:** `frontend/src/components/Home.tsx`

**Changes:**
```typescript
import { useUserPreferences } from '../hooks/useUserPreferences';

export function Home() {
  const preferences = useUserPreferences();

  // OLD: const { facts } = useFacts();
  // NEW: Use preferences.favorites

  return (
    <div>
      {/* Saved Properties Section */}
      <section>
        <h2>Saved Properties ({preferences.favorites.length})</h2>
        {preferences.favorites.length === 0 ? (
          <p>No saved properties yet. Click the heart icon on any property to save it.</p>
        ) : (
          <ul>
            {preferences.favorites.map(code => (
              <PropertyCard
                key={code}
                code={code}
                isFavorite={true}
                onToggleFavorite={() => preferences.toggleFavorite(code)}
              />
            ))}
          </ul>
        )}
      </section>

      {/* Hidden Properties Section (Optional) */}
      {preferences.hidden.length > 0 && (
        <section>
          <h2>Hidden Properties ({preferences.hidden.length})</h2>
          <button onClick={preferences.clearHidden}>Unhide All</button>
          {/* ... list hidden properties ... */}
        </section>
      )}
    </div>
  );
}
```

---

### 4. PropertyDetailModal Updates

**Location:** `frontend/src/components/PropertyDetailModal.tsx`

**Changes:**
```typescript
interface PropertyDetailModalProps {
  property: Property;
  isFavorite: boolean;
  onToggleFavorite: () => void;
  onHide: () => void;
  onClose: () => void;
}

export function PropertyDetailModal({
  property,
  isFavorite,
  onToggleFavorite,
  onHide,
  onClose
}: PropertyDetailModalProps) {
  return (
    <div className="modal">
      <div className="modal-header">
        <h2>{property.title}</h2>

        {/* NEW: Favorite Button */}
        <button onClick={onToggleFavorite} className="favorite-btn">
          {isFavorite ? (
            <HeartIconFilled className="text-red-500" />
          ) : (
            <HeartIcon className="text-gray-400" />
          )}
        </button>

        {/* Existing close button */}
        <button onClick={onClose}>
          <XMarkIcon />
        </button>
      </div>

      <div className="modal-content">
        {/* ... existing content ... */}

        {/* NEW: Hide Property Button */}
        <button onClick={onHide} className="hide-btn">
          Hide this property
        </button>
      </div>
    </div>
  );
}
```

---

### 5. Backend Widget Updates

**Location:** `backend/examples/custom_widgets.py`

**New Helper Functions:**
```python
from chatkit.widgets import Button
from chatkit.actions import ActionConfig

def create_favorite_button(property_code: str, is_favorited: bool = False) -> Button:
    """
    Create a favorite button for property cards.

    Args:
        property_code: Property code (e.g., "PROP001")
        is_favorited: Whether property is currently favorited

    Returns:
        Button widget configured as client-side action
    """
    return Button(
        label="",  # Icon only
        iconStart="heart-filled" if is_favorited else "heart",
        size="xs",
        variant="ghost",
        color="danger" if is_favorited else "secondary",
        onClickAction=ActionConfig(
            type="toggle_favorite",
            handler="client",  # Handle in frontend
            payload={"propertyCode": property_code}
        )
    )

def create_hide_button(property_code: str) -> Button:
    """
    Create a hide button for property cards.

    Args:
        property_code: Property code

    Returns:
        Button widget configured as client-side action
    """
    return Button(
        label="",  # Icon only
        iconStart="eye-slash",  # Note: Check available icons in WIDGETS.md
        size="xs",
        variant="ghost",
        color="secondary",
        onClickAction=ActionConfig(
            type="hide_property",
            handler="client",
            payload={"propertyCode": property_code}
        )
    )
```

**Update Property Card Creation:**
```python
# In create_property_listview() function

ListViewItem(
    key=item["id"],
    gap=3,
    onClickAction=ActionConfig(
        type="view_item_details",
        handler="server",
        payload={"item_data": item["item_data"]}
    ),
    children=[
        Image(src=item["image_url"], ...),
        Col(...),  # Property details

        # NEW: Action buttons (favorite + hide)
        Row(
            gap=1,
            children=[
                create_favorite_button(item["id"]),
                create_hide_button(item["id"]),
            ]
        )
    ]
)
```

---

## Integration Points

### Frontend Integration Points

1. **ChatKitPanel.tsx (Line ~58-91)**
   - Add `useUserPreferences` hook
   - Add action handlers for `toggle_favorite` and `hide_property`
   - Pass preferences to PropertyDetailModal

2. **Home.tsx (Line ~84-98)**
   - Replace `useFacts` with `useUserPreferences`
   - Update "Saved Properties" section to use `preferences.favorites`
   - Add "Hidden Properties" section (optional)

3. **PropertyDetailModal.tsx (Line ~253)**
   - Add favorite button to modal header
   - Add hide button to action row
   - Accept `isFavorite`, `onToggleFavorite`, `onHide` props

### Backend Integration Points

1. **custom_widgets.py**
   - Add `create_favorite_button()` helper
   - Add `create_hide_button()` helper
   - Update `create_property_listview()` to include buttons

2. **property_carousel.py**
   - Update `render()` to pass favorite/hide buttons to card builder
   - No filtering logic needed (frontend handles filtering)

---

## Migration Path

### Phase 1: Implement localStorage Solution (This PR)

**Timeline:** 2-3 hours

1. Create `useUserPreferences` hook
2. Update ChatKitPanel action handlers
3. Update Home component (replace useFacts)
4. Update PropertyDetailModal
5. Add backend widget buttons
6. Test favorite/hide flows

**Deliverables:**
- Working favorite/hide functionality
- Data persists in localStorage
- "Saved Properties" shows favorites

---

### Phase 2: Add Backend Persistence (Future)

**Trigger Conditions:**
- User accounts are implemented
- Backend storage (PostgreSQL/Redis) is added for thread persistence
- Analytics on user preferences are needed

**Implementation:**
1. Add database tables:
   ```sql
   CREATE TABLE user_preferences (
     user_id UUID PRIMARY KEY,
     favorites TEXT[],
     hidden TEXT[],
     created_at TIMESTAMP,
     updated_at TIMESTAMP
   );
   ```

2. Add backend endpoints:
   ```python
   @app.get("/api/user/preferences")
   async def get_preferences(request: Request):
       user_id = request.session["user_id"]
       return await store.load_preferences(user_id)

   @app.post("/api/user/preferences")
   async def update_preferences(request: Request, prefs: UserPreferences):
       user_id = request.session["user_id"]
       await store.save_preferences(user_id, prefs)
   ```

3. Update `useUserPreferences` hook:
   ```typescript
   export function useUserPreferences() {
     // CHANGE: Load from API instead of localStorage
     useEffect(() => {
       fetch('/api/user/preferences')
         .then(r => r.json())
         .then(setPreferences);
     }, []);

     // CHANGE: Save to API instead of localStorage
     const updatePreferences = async (newPrefs) => {
       await fetch('/api/user/preferences', {
         method: 'POST',
         body: JSON.stringify(newPrefs)
       });
       setPreferences(newPrefs);
     };

     // Hook interface STAYS THE SAME
     return { favorites, hidden, toggleFavorite, ... };
   }
   ```

**Migration Strategy:**
- Hook interface unchanged → No component updates needed
- One-time data migration: Read localStorage, POST to backend
- Gradual rollout: Feature flag to enable backend storage

---

## Security Considerations

### localStorage Security

**Threats:**
1. **XSS Attacks:** Malicious scripts can read localStorage
2. **Local Storage Exposure:** Anyone with physical access can view data

**Mitigations:**
1. ✅ No sensitive data stored (only property codes)
2. ✅ CSP headers prevent XSS (if configured)
3. ✅ HTTPS prevents network sniffing
4. ⚠️ Property codes are not secret (already visible in UI)

**Verdict:** Low risk for this use case (preferences are non-sensitive)

---

### Future Backend Storage Security

**Threats:**
1. **CSRF Attacks:** Unauthorized preference updates
2. **Session Hijacking:** Attacker gains access to user session

**Mitigations:**
1. ✅ CSRF tokens on POST requests
2. ✅ Secure session cookies (`https_only=True`, `same_site="strict"`)
3. ✅ Rate limiting on preference endpoints
4. ✅ Input validation (property codes match pattern)

---

## Testing Strategy

### Unit Tests

**Frontend:**
```typescript
// frontend/src/hooks/useUserPreferences.test.ts

describe('useUserPreferences', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('loads preferences from localStorage on mount', () => {
    localStorage.setItem('uniko_preferences', JSON.stringify({
      favorites: ['PROP001'],
      hidden: [],
      version: 1
    }));

    const { result } = renderHook(() => useUserPreferences());
    expect(result.current.favorites).toEqual(['PROP001']);
  });

  it('toggles favorite status', () => {
    const { result } = renderHook(() => useUserPreferences());

    act(() => result.current.toggleFavorite('PROP001'));
    expect(result.current.isFavorite('PROP001')).toBe(true);

    act(() => result.current.toggleFavorite('PROP001'));
    expect(result.current.isFavorite('PROP001')).toBe(false);
  });

  it('hides property', () => {
    const { result } = renderHook(() => useUserPreferences());

    act(() => result.current.hideProperty('PROP001'));
    expect(result.current.isHidden('PROP001')).toBe(true);
  });

  it('persists to localStorage', () => {
    const { result } = renderHook(() => useUserPreferences());

    act(() => result.current.toggleFavorite('PROP001'));

    const stored = JSON.parse(localStorage.getItem('uniko_preferences')!);
    expect(stored.favorites).toContain('PROP001');
  });
});
```

### Integration Tests

**Action Handler Flow:**
```typescript
describe('ChatKitPanel favorite actions', () => {
  it('handles toggle_favorite action', async () => {
    const { user } = render(<ChatKitPanel />);

    // Simulate action from widget
    await act(async () => {
      widgets.onAction({
        type: 'toggle_favorite',
        payload: { propertyCode: 'PROP001' }
      });
    });

    // Verify localStorage updated
    const stored = JSON.parse(localStorage.getItem('uniko_preferences')!);
    expect(stored.favorites).toContain('PROP001');
  });
});
```

### Manual Testing Checklist

- [ ] Favorite property from carousel → appears in Saved Properties
- [ ] Unfavorite property → disappears from Saved Properties
- [ ] Hide property → disappears from future searches
- [ ] Refresh browser → preferences persist
- [ ] Clear localStorage → preferences reset to defaults
- [ ] 1000 favorites → performance acceptable (<100ms)
- [ ] Favorite button shows correct state (filled vs outline)
- [ ] Hidden properties section displays correctly

---

## Appendix A: Alternative Icon Options

**Favorite Button Icons:**
- `heart` / `heart-filled` ⭐ **RECOMMENDED**
- `star` / `star-filled`
- `bookmark` / `bookmark-filled`

**Hide Button Icons:**
- `eye-slash` (if available)
- `x-circle`
- `minus-circle`

**Note:** Check WIDGETS.md line 2208-2263 for available icons. If `eye-slash` is not available, use `x-circle` or add custom icon.

---

## Appendix B: Future Enhancements

**Phase 3+ (Beyond Initial Implementation):**

1. **Collections/Tags:**
   - Group favorites into collections ("Dream Homes", "Investment Properties")
   - Data model: `{collections: [{id, name, propertyCodes}]}`

2. **Notes on Properties:**
   - Add private notes to favorites
   - Data model: `{notes: {[code]: string}}`

3. **Search Filters:**
   - Save search criteria as presets
   - Data model: `{savedSearches: [{name, filters}]}`

4. **Comparison Tool:**
   - Compare up to 4 favorited properties side-by-side
   - Uses existing favorites data

5. **Export Favorites:**
   - Export to PDF/CSV for sharing with real estate agents
   - Server-side generation (requires backend endpoint)

---

## Document Revision History

| Version | Date       | Author | Changes                          |
|---------|------------|--------|----------------------------------|
| 1.0     | 2025-10-30 | Claude | Initial design document          |

---

**Document Status:** ✅ Ready for Review
**Next Steps:** Review with team → Approve approach → Implement Phase 1
