# contexts

## Purpose
React Context providers for global state management, specifically managing thread-specific user preferences (favorites and hidden properties) with automatic synchronization.

## Key Files
- **`PreferencesContext.tsx`**: React Context provider managing thread-specific favorites/hidden properties with API integration and helper utilities

## Dependencies

### External
- `react` - Context API (`createContext`, `useContext`, `useState`, `useEffect`)

### Internal
- Backend API: `GET /langgraph/preferences?thread_id=X` for fetching thread-specific preferences

## Architecture Notes

### Context Structure
```tsx
interface PreferencesContextType {
  preferences: Preferences;          // Current thread's favorites/hidden
  loading: boolean;                  // Initial fetch state
  error: string | null;              // Error messages
  currentThreadId: string | null;    // Active thread ID
  setCurrentThreadId: (id) => void;  // Update active thread
  refreshPreferences: () => Promise<void>;  // Manual refresh
}
```

### Preferences Schema (v3)
```tsx
{
  favorites: {
    "PROP001": { code: "PROP001", title: "...", price: 115000, ... },
    "PROP002": { code: "PROP002", ... }
  },
  hidden: {
    "PROP999": { code: "PROP999", ... }
  },
  version: 3  // v3 = thread-specific preferences
}
```

### Automatic Synchronization
- **Thread Change Detection**: `useEffect` watches `currentThreadId`, fetches preferences on change
- **Manual Refresh**: Components can call `refreshPreferences(threadId?)` to force update
- **Session Cookies**: Uses `credentials: 'include'` for session-based user identification
- **Error Handling**: Catches fetch errors, sets `error` state (doesn't crash app)

### Provider Setup
```tsx
// In App.tsx
<PreferencesProvider>
  <ChatKitPanel />
  <PreferencesSidebar />
</PreferencesProvider>
```

### Helper Functions
Exported utilities for working with Record-based preferences:
- `getFavoritesArray(preferences)`: Convert `Record<code, data>` → `PropertyData[]`
- `getHiddenArray(preferences)`: Convert `Record<code, data>` → `PropertyData[]`
- `getFavoritesCount(preferences)`: Count favorites
- `getHiddenCount(preferences)`: Count hidden properties

## Usage

### Provider Wrapping
```tsx
// App.tsx
import { PreferencesProvider } from './contexts/PreferencesContext';

function App() {
  return (
    <PreferencesProvider>
      <YourComponents />
    </PreferencesProvider>
  );
}
```

### Consuming Context
```tsx
import { usePreferences, getFavoritesArray } from '../contexts/PreferencesContext';

function MyComponent() {
  const {
    preferences,
    loading,
    currentThreadId,
    setCurrentThreadId,
    refreshPreferences
  } = usePreferences();

  const favoritesArray = getFavoritesArray(preferences);

  // Update thread (auto-fetches preferences)
  const handleThreadChange = (threadId: string) => {
    setCurrentThreadId(threadId);
  };

  // Manual refresh (e.g., after adding favorite)
  const handleFavoriteAdded = async () => {
    await refreshPreferences();
  };
}
```

### Integration with ChatKitPanel
```tsx
// ChatKitPanel.tsx
const { setCurrentThreadId } = usePreferences();

useChatKit({
  onThreadChange: (event) => {
    setCurrentThreadId(event.threadId);  // Auto-syncs preferences
  }
});
```

## Data Flow

### Thread Change Flow
```
User switches thread in ChatKit
       ↓
ChatKitPanel.onThreadChange(event)
       ↓
setCurrentThreadId(event.threadId)
       ↓
useEffect detects change
       ↓
refreshPreferences(currentThreadId)
       ↓
GET /langgraph/preferences?thread_id=thr_abc123
       ↓
setPreferences(response.preferences)
       ↓
All components consuming usePreferences() re-render
```

### Manual Refresh Flow
```
User adds favorite in PropertyDetailModal
       ↓
POST /langgraph/preferences/favorites
       ↓
refreshPreferences()  // Manual call
       ↓
GET /langgraph/preferences?thread_id=...
       ↓
setPreferences(updated_data)
       ↓
PreferencesSidebar updates to show new favorite
```

## State Management

### Initial State
- `preferences`: Empty favorites/hidden (`{favorites: {}, hidden: {}, version: 3}`)
- `loading`: `true` (until first fetch completes or no thread ID)
- `error`: `null`
- `currentThreadId`: `null` (set by ChatKitPanel)

### Loading Behavior
- `loading=true` only during initial fetch
- Subsequent refreshes don't set `loading=true` (avoids flickering)
- If no thread ID, sets `loading=false` without fetching

### Error Handling
- Network errors caught, logged to console
- Sets `error` state with message
- Doesn't block rendering (components can check `error` state)

## Helper Function Reference

### `getFavoritesArray(preferences)`
Converts favorites from Record to Array for rendering lists.
```tsx
const favorites = getFavoritesArray(preferences);
// [{code: "PROP001", ...}, {code: "PROP002", ...}]
```

### `getHiddenArray(preferences)`
Converts hidden properties from Record to Array.
```tsx
const hidden = getHiddenArray(preferences);
```

### `getFavoritesCount(preferences)`
Returns number of favorited properties.
```tsx
const count = getFavoritesCount(preferences);  // 5
```

### `getHiddenCount(preferences)`
Returns number of hidden properties.
```tsx
const count = getHiddenCount(preferences);  // 3
```

## Production Considerations
- **Polling**: Currently no auto-refresh (ChatKitPanel polls every 5s, could move to context)
- **Error Boundary**: No error boundary around Provider (errors logged but not surfaced to UI)
- **Caching**: No client-side cache (re-fetches on every thread change)
- **Optimistic Updates**: No optimistic UI updates (waits for server response)
- **WebSocket Alternative**: Consider replacing polling with WebSocket for real-time updates
- **Type Safety**: All TypeScript interfaces exported for consumer type safety
