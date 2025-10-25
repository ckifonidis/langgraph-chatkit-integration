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

export const GREETING = "LangGraph AI Assistant";

export const STARTER_PROMPTS: StartScreenPrompt[] = [
  {
    label: "What can you help me with?",
    prompt: "Hello! What can you help me with?",
    icon: "circle-question",
  },
  {
    label: "Banking services",
    prompt: "What banking services do you offer?",
    icon: "search",
  },
  {
    label: "Account help",
    prompt: "I need help with my account",
    icon: "book-open",
  },
  {
    label: "Loan information",
    prompt: "Tell me about loans",
    icon: "sparkle",
  },
];

export const PLACEHOLDER_INPUT = "Ask me anything...";
