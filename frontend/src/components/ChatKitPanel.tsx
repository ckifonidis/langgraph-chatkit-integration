import { useState, useEffect } from "react";
import { ChatKit, useChatKit } from "@openai/chatkit-react";
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
  const { refreshPreferences, setCurrentThreadId: setPreferencesThreadId } = usePreferences();

  // Refresh preferences periodically to catch server-side updates
  useEffect(() => {
    const interval = setInterval(() => {
      refreshPreferences();
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [refreshPreferences]);

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

  return (
    <>
      <div className="relative h-full w-full overflow-hidden border border-slate-200/60 bg-white shadow-card dark:border-slate-800/70 dark:bg-slate-900">
        <ChatKit control={chatkit.control} className="block h-full w-full" />
      </div>

      <PropertyDetailModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedProperty(null);
        }}
        property={selectedProperty}
      />
    </>
  );
}
