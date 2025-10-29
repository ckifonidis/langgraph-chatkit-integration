import { StartScreenPrompt } from "@openai/chatkit";

export const CHATKIT_API_URL =
  import.meta.env.VITE_CHATKIT_API_URL ?? "/langgraph/chatkit";

/**
 * ChatKit still expects a domain key at runtime. Use any placeholder locally,
 * but register your production domain at
 * https://platform.openai.com/settings/organization/security/domain-allowlist
 * and deploy the real key.
 */
export const CHATKIT_API_DOMAIN_KEY =
  import.meta.env.VITE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

export const FACTS_API_URL = import.meta.env.VITE_FACTS_API_URL ?? "/facts";

export const THEME_STORAGE_KEY = "chatkit-boilerplate-theme";

export const GREETING = "Uniko Property Assistant";

export const STARTER_PROMPTS: StartScreenPrompt[] = [
  {
    label: "Find properties in Athens",
    prompt: "Show me properties for sale in Athens",
    icon: "search",
  },
  {
    label: "Properties under €200,000",
    prompt: "Find apartments under €200,000",
    icon: "sparkle",
  },
  {
    label: "Properties near metro",
    prompt: "Show me properties near metro stations",
    icon: "maps",
  },
  {
    label: "Buying process help",
    prompt: "How does the property buying process work with Uniko?",
    icon: "circle-question",
  },
];

export const PLACEHOLDER_INPUT = "Search for properties or ask about real estate...";
