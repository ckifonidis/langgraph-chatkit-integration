import clsx from "clsx";

import { ChatKitPanel } from "./ChatKitPanel";
import { ThemeToggle } from "./ThemeToggle";
import { PreferencesSidebar } from "./PreferencesSidebar";
import { ColorScheme } from "../hooks/useColorScheme";

export default function Home({
  scheme,
  handleThemeChange,
}: {
  scheme: ColorScheme;
  handleThemeChange: (scheme: ColorScheme) => void;
}) {
  const containerClass = clsx(
    "min-h-screen bg-gradient-to-br transition-colors duration-300",
    scheme === "dark"
      ? "from-slate-900 via-slate-950 to-slate-850 text-slate-100"
      : "from-slate-100 via-white to-slate-200 text-slate-900"
  );

  return (
    <div className={containerClass}>
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-6 pt-4 pb-10 md:py-10 lg:flex-row lg:gap-8">

        {/* Left Column - Branding (shows 2nd on mobile) */}
        <section className="w-full lg:w-1/4 order-2 lg:order-1 space-y-6">
          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex items-center gap-3 mb-2">
                <svg
                  width="48"
                  height="48"
                  viewBox="0 0 48 48"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="text-[#00BA88]"
                >
                  <path
                    d="M24 8L8 20V40H18V28H30V40H40V20L24 8Z"
                    fill="currentColor"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinejoin="round"
                  />
                  <rect x="20" y="32" width="8" height="8" fill="white" />
                </svg>
                <span className="text-2xl font-bold text-[#00BA88]">uniko</span>
              </div>
              <h1 className="text-3xl font-semibold sm:text-4xl">
                Uniko Property Assistant
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Search for properties across Greece with AI-powered
                assistance. Get personalized recommendations, compare
                listings, and learn about the buying process with the
                National Bank of Greece as your partner.
              </p>
            </div>
            <div className="flex justify-start">
              <ThemeToggle value={scheme} onChange={handleThemeChange} />
            </div>
          </div>
        </section>

        {/* Middle Column - ChatKit Panel (shows 1st on mobile) */}
        <div className="relative w-full lg:w-[40%] order-1 lg:order-2 flex h-[70vh] lg:h-[90vh] items-stretch overflow-hidden rounded-3xl bg-white/80 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.6)] ring-2 ring-[#00BA88]/30 backdrop-blur dark:bg-slate-900/70 dark:shadow-[0_45px_90px_-45px_rgba(15,23,42,0.85)] dark:ring-[#00BA88]/40">
          <ChatKitPanel
            theme={scheme}
            onThemeRequest={handleThemeChange}
          />
        </div>

        {/* Right Column - Preferences (shows 3rd on mobile) */}
        <section className="w-full lg:w-[35%] order-3">
          <PreferencesSidebar />
        </section>

      </div>
    </div>
  );
}
