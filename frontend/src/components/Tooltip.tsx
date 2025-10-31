import { ReactNode, useState } from 'react';

interface TooltipProps {
  content: string;
  children: ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 bg-slate-900 dark:bg-slate-700 text-white text-xs font-medium rounded-lg shadow-lg whitespace-nowrap z-[100] pointer-events-none">
          {content}
          {/* Arrow pointing up */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-px">
            <div className="border-4 border-transparent border-b-slate-900 dark:border-b-slate-700"></div>
          </div>
        </div>
      )}
    </div>
  );
}
