import { useState, useEffect, useRef } from "react";
import { ChatKit, useChatKit } from "../chatkit-react";
import {
  CHATKIT_API_URL,
  CHATKIT_API_DOMAIN_KEY,
  STARTER_PROMPTS,
  PLACEHOLDER_INPUT,
  GREETING,
} from "../lib/config";
import type { ColorScheme } from "../hooks/useColorScheme";
import { PropertyDetailModal } from "./PropertyDetailModal";
import { usePreferences } from "../contexts/PreferencesContext";

type ChatKitPanelProps = {
  theme: ColorScheme;
  onThemeRequest: (scheme: ColorScheme) => void;
};

export function ChatKitPanel({
  theme,
  onThemeRequest,
}: ChatKitPanelProps) {
  const [selectedProperty, setSelectedProperty] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const { refreshPreferences, setCurrentThreadId: setPreferencesThreadId, registerThreadReload } = usePreferences();

  // Throttle + debounce refs for thread reload
  const lastReloadRef = useRef<number>(0);
  const pendingReloadRef = useRef<NodeJS.Timeout | null>(null);
  const RELOAD_THROTTLE_MS = 2000;  // ChatKit requires 2s minimum between calls
  const RELOAD_DEBOUNCE_MS = 300;   // Group rapid actions together

  const chatkit = useChatKit({
    api: { url: CHATKIT_API_URL, domainKey: CHATKIT_API_DOMAIN_KEY },
    theme: {
      colorScheme: theme,
      color: {
        grayscale: {
          hue: 220,
          tint: 6,
          shade: theme === "dark" ? -1 : -4,
        },
        accent: {
          primary: "#000000", // Black for send button
          level: 1,
        },
      },
      radius: "pill", // Makes buttons pill-shaped (most circular option)
    },
    startScreen: {
      greeting: GREETING,
      prompts: STARTER_PROMPTS,
    },
    composer: {
      placeholder: PLACEHOLDER_INPUT,
    },
    threadItemActions: {
      feedback: false,
    },
    onThreadChange: (event) => {
      setCurrentThreadId(event.threadId);
      setPreferencesThreadId(event.threadId);  // Update preferences context
      if (import.meta.env.DEV) {
        console.debug("[ChatKitPanel] Thread changed:", event.threadId);
      }
    },
    widgets: {
      async onAction(action, widgetItem) {
        if (import.meta.env.DEV) {
          console.debug("[ChatKitPanel] widget.action", action);
        }

        // Handle property detail modal (client-side only)
        if (action.type === "view_item_details") {
          const propertyData = action.payload?.item_data;
          if (propertyData) {
            console.log("[DEBUG] Opening property modal - Thread ID:", currentThreadId, "Property:", propertyData.code);
            setSelectedProperty(propertyData);
            setIsModalOpen(true);
          }
          return;
        }

        // Handle carousel item clicks
        if (action.type === "carousel_item_click" || action.type === "open_link") {
          const linkUrl = action.payload?.link_url;
          if (linkUrl) {
            window.open(linkUrl, "_blank", "noopener,noreferrer");
            return;
          }
        }
      },
    },
    onClientTool: async (invocation) => {
      if (invocation.name === "switch_theme") {
        const requested = invocation.params.theme;
        if (requested === "light" || requested === "dark") {
          if (import.meta.env.DEV) {
            console.debug("[ChatKitPanel] switch_theme", requested);
          }
          onThemeRequest(requested);
          return { success: true };
        }
        return { success: false };
      }

      return { success: false };
    },
    onError: ({ error }) => {
      // ChatKit handles displaying the error to the user
      console.error("ChatKit error", error);
    },
  });

  // Handler to reload current thread items (with throttling + debouncing)
  const handleThreadReload = async () => {
    const now = Date.now();
    const timeSinceLastReload = now - lastReloadRef.current;

    // Clear any pending debounced call
    if (pendingReloadRef.current) {
      clearTimeout(pendingReloadRef.current);
    }

    // If within 2s throttle window, schedule for later
    if (timeSinceLastReload < RELOAD_THROTTLE_MS) {
      const delay = RELOAD_THROTTLE_MS - timeSinceLastReload + RELOAD_DEBOUNCE_MS;
      console.log(`[THREAD-RELOAD] Throttled, queuing reload for ${delay}ms from now`);

      pendingReloadRef.current = setTimeout(() => {
        handleThreadReload(); // Execute after delay
      }, delay);
      return;
    }

    // Execute reload now
    lastReloadRef.current = now;
    console.log('[THREAD-RELOAD] Executing reload');

    if (!chatkit.fetchUpdates) {
      console.error('[THREAD-RELOAD] chatkit.fetchUpdates is not available!');
      return;
    }

    try {
      await chatkit.fetchUpdates();
      console.log('[THREAD-RELOAD] ✅ Thread items refreshed');
    } catch (error) {
      console.error('[THREAD-RELOAD] Error refreshing thread items:', error);
    }
  };

  // Register thread reload function with preferences context
  useEffect(() => {
    registerThreadReload(handleThreadReload);
  }, [registerThreadReload, handleThreadReload]);

  // Cleanup pending reload timeout on unmount
  useEffect(() => {
    return () => {
      if (pendingReloadRef.current) {
        clearTimeout(pendingReloadRef.current);
      }
    };
  }, []);

  return (
    <>
      <div className="relative h-full w-full overflow-hidden border border-slate-200/60 bg-white shadow-card dark:border-slate-800/70 dark:bg-slate-900">
        <ChatKit control={chatkit.control} className="block h-full w-full" />
      </div>

      <PropertyDetailModal
        isOpen={isModalOpen}
        onClose={async () => {
          setIsModalOpen(false);
          setSelectedProperty(null);
          // Reload thread items after modal closes to reflect any preference changes
          // Modal actions use skipThreadReload=true, so refresh happens only once here
          await handleThreadReload();
        }}
        property={selectedProperty}
      />
    </>
  );
}
