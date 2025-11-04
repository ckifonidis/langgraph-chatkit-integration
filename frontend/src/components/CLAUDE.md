# components

## Purpose
React UI components for the ChatKit-based property search interface, including the main chat panel, property details modal, preferences sidebar, and utility components.

## Key Files
- **`ChatKitPanel.tsx`**: Main ChatKit integration component with widget action handlers, theme management, and property modal coordination
- **`PropertyDetailModal.tsx`**: Full-screen modal displaying detailed property information with Google Maps integration, favorite/hide actions, and AI-generated descriptions
- **`PreferencesSidebar.tsx`**: Collapsible sidebar showing thread-specific favorites and hidden properties with live updates
- **`Home.tsx`**: Main layout component orchestrating left branding section, center chat panel, and right preferences sidebar
- **`ThemeToggle.tsx`**: Light/dark mode toggle button
- **`Tooltip.tsx`**: Reusable tooltip component with Headless UI

## Dependencies

### External
- `react` - Core React hooks (`useState`, `useEffect`, `useRef`)
- `@headlessui/react` - Accessible UI primitives (`Dialog`, `Transition`)
- `@heroicons/react` - Icon components (`XMarkIcon`, `StarIcon`, etc.)
- `clsx` - Conditional className composition
- Google Maps JavaScript API - Map rendering in property modal

### Internal
- `../chatkit-react` - ChatKit React hooks (`useChatKit`) and components (`<ChatKit>`)
- `../contexts/PreferencesContext` - User preferences state management (`usePreferences`)
- `../hooks/useColorScheme` - Theme management (`ColorScheme` type)
- `../lib/config` - API URLs, domain keys, starter prompts, greeting text

## Architecture Notes

### ChatKitPanel Integration
- **Theme Configuration**: Passes grayscale hue/tint/shade and accent colors to ChatKit
- **Thread Change Tracking**: Syncs current thread ID with `PreferencesContext` via `onThreadChange`
- **Widget Actions**: Handles `view_item_details` (modal), `carousel_item_click`, `open_link` (external links)
- **Client Tools**: Processes `switch_theme` tool invocation from backend
- **Polling**: Refreshes preferences every 5 seconds to catch server-side changes

### PropertyDetailModal Features
- **Google Maps Integration**: Loads Maps API dynamically, renders interactive map with property marker
- **Coordinate Parsing**: Handles multiple coordinate formats (GeoJSON, lat/lng fields, nested objects)
- **AI Description Generation**: Fetches descriptions from `/langgraph/generate-description` endpoint with caching
- **Action Handlers**:
  - Favorite toggle via `POST /langgraph/preferences/favorites` or `DELETE /favorites/{code}`
  - Hide property via `POST /langgraph/preferences/hidden`
- **Thread-Aware**: All actions include current thread ID for thread-specific preferences
- **Animations**: Uses Headless UI Transition for smooth modal open/close

### PreferencesSidebar Layout
- **Collapsed State**: Shows summary count (`X favorites • Y hidden`)
- **Expanded State**: Displays full property cards with images, titles, prices
- **Live Data**: Uses `usePreferences()` hook to access real-time preference data
- **Property Cards**: Click to open PropertyDetailModal with full details
- **Scrollable**: Auto-scrolls lists when content exceeds container height

### Layout Architecture (Home.tsx)
```
┌─────────────────────────────────────────────┐
│          Top Bar (Mobile Only)              │
├─────────┬─────────────────────┬─────────────┤
│  Left   │       Center        │    Right    │
│ Branding│    ChatKitPanel     │  Prefs      │
│  Logo   │   (Main Chat UI)    │  Sidebar    │
│  Title  │                     │             │
│  Theme  │                     │  Hidden on  │
│  Toggle │                     │  mobile     │
└─────────┴─────────────────────┴─────────────┘
   25%           50%                 25%
  (order-2    (order-1 on       (order-3 on
   on mobile)  mobile)            mobile)
```

## Usage

### ChatKitPanel Setup
```tsx
<ChatKitPanel
  theme={theme}  // "light" | "dark"
  onThemeRequest={(newTheme) => setTheme(newTheme)}
/>
```

### PropertyDetailModal Integration
```tsx
// In ChatKitPanel widget handler
if (action.type === "view_item_details") {
  setSelectedProperty(action.payload?.item_data);
  setIsModalOpen(true);
}

// Modal component
<PropertyDetailModal
  isOpen={isModalOpen}
  onClose={() => setIsModalOpen(false)}
  property={selectedProperty}
  threadId={currentThreadId}  // Required for thread-specific actions
/>
```

### PreferencesSidebar Usage
```tsx
// Requires PreferencesProvider wrapping
<PreferencesProvider>
  <PreferencesSidebar />
</PreferencesProvider>
```

## Widget Action Flow

### View Property Details
```
User clicks ListView item → ChatKit onClickDetails
       ↓
ChatKitPanel.widgets.onAction({type: "view_item_details", payload: {item_data}})
       ↓
setSelectedProperty(item_data), setIsModalOpen(true)
       ↓
PropertyDetailModal renders with full property data
```

### Toggle Favorite (Modal)
```
User clicks star button in modal
       ↓
POST /langgraph/preferences/favorites
  {thread_id, propertyCode, propertyData}
       ↓
Server updates MemoryStore for thread
       ↓
refreshPreferences() → updates sidebar
       ↓
onThreadReload() → chatkit.fetchUpdates()
       ↓
✨ Thread items refetch with updated preferences
       ↓
✨ Star icons update on ALL carousels instantly
       ↓
Modal stays open, star icon updates
```

### Hide Property (Modal)
```
User clicks hide button in modal
       ↓
POST /langgraph/preferences/hidden
  {thread_id, propertyCode, propertyData}
       ↓
Server updates MemoryStore for thread
       ↓
refreshPreferences() → updates sidebar
       ↓
onThreadReload() → chatkit.fetchUpdates()
       ↓
✨ Thread items refetch with server-side filtering applied
       ↓
✨ Property disappears from ALL carousels instantly
       ↓
Modal stays open (property now hidden in background)
```

## Component Props

### ChatKitPanel
- `theme`: `ColorScheme` - Current theme ("light" | "dark")
- `onThemeRequest`: `(ColorScheme) => void` - Callback when theme change requested

### PropertyDetailModal
- `isOpen`: `boolean` - Modal visibility state
- `onClose`: `() => void` - Close callback
- `property`: `PropertyData | null` - Property data to display
- `onThreadReload`: `() => Promise<void>` (optional) - Callback to reload thread items after preference changes (triggers `chatkit.fetchUpdates()`)

### PreferencesSidebar
- No props - consumes `usePreferences()` context

## Styling & Theming

### Tailwind Configuration
- **Primary Color**: `#00BA88` (teal green for "uniko" brand)
- **Background Gradients**: `from-slate-100 via-white to-slate-200` (light), `from-slate-900 via-slate-950 to-slate-850` (dark)
- **Glassmorphism**: `bg-white/80 backdrop-blur` for cards
- **Ring Accents**: `ring-2 ring-[#00BA88]/30` for emphasis
- **Transitions**: `transition-colors duration-300` for theme switching

### ChatKit Theme Integration
```tsx
theme: {
  colorScheme: theme,  // "light" | "dark"
  color: {
    grayscale: { hue: 220, tint: 6, shade: -1 },
    accent: { primary: "#000000", level: 1 }
  },
  radius: "pill"  // Circular buttons
}
```

## Production Considerations
- **Google Maps API Key**: Exposed in HTML (consider domain restrictions)
- **Polling Overhead**: 5-second preference refresh may cause unnecessary requests (consider WebSocket)
- **Error Handling**: API failures show console errors but no user-facing messages
- **Loading States**: PropertyDetailModal shows loading spinner for description generation
- **Accessibility**: Modal uses Headless UI for keyboard navigation and ARIA attributes
- **Image Loading**: Property images load directly from URLs (no lazy loading/optimization)
