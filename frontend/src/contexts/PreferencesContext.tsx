import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Type definitions
interface PropertyData {
  code: string;
  title: string;
  price: number;
  propertyArea?: number;
  numberOfRooms?: number;
  numberOfBathrooms?: number;
  defaultImagePath?: string;
  address?: {
    prefecture?: string;
  };
  description?: string;
  [key: string]: any;
}

interface Preferences {
  favorites: Record<string, PropertyData>;
  hidden: Record<string, PropertyData>;
  version: number;
}

interface PreferencesContextType {
  preferences: Preferences;
  loading: boolean;
  error: string | null;
  currentThreadId: string | null;
  setCurrentThreadId: (threadId: string | null) => void;
  refreshPreferences: (threadId?: string) => Promise<void>;
}

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

interface PreferencesProviderProps {
  children: ReactNode;
}

export function PreferencesProvider({ children }: PreferencesProviderProps) {
  const [preferences, setPreferences] = useState<Preferences>({
    favorites: {},
    hidden: {},
    version: 3,  // v3 = thread-specific
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);

  const refreshPreferences = async (threadId?: string) => {
    // Use provided threadId or current one
    const targetThreadId = threadId || currentThreadId;

    // Don't fetch if no thread ID available
    if (!targetThreadId) {
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const response = await fetch(`/langgraph/preferences?thread_id=${encodeURIComponent(targetThreadId)}`, {
        credentials: 'include', // Include session cookie
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch preferences: ${response.statusText}`);
      }

      const data = await response.json();

      // Extract preferences from response
      if (data.preferences) {
        setPreferences(data.preferences);
      }
    } catch (err) {
      console.error('Error fetching preferences:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Refresh preferences when thread changes
  useEffect(() => {
    if (currentThreadId) {
      refreshPreferences(currentThreadId);
    }
  }, [currentThreadId]);

  const value: PreferencesContextType = {
    preferences,
    loading,
    error,
    currentThreadId,
    setCurrentThreadId,
    refreshPreferences,
  };

  return (
    <PreferencesContext.Provider value={value}>
      {children}
    </PreferencesContext.Provider>
  );
}

// Custom hook to use preferences context
export function usePreferences(): PreferencesContextType {
  const context = useContext(PreferencesContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
}

// Helper functions to work with preferences
export function getFavoritesArray(preferences: Preferences): PropertyData[] {
  return Object.values(preferences.favorites);
}

export function getHiddenArray(preferences: Preferences): PropertyData[] {
  return Object.values(preferences.hidden);
}

export function getFavoritesCount(preferences: Preferences): number {
  return Object.keys(preferences.favorites).length;
}

export function getHiddenCount(preferences: Preferences): number {
  return Object.keys(preferences.hidden).length;
}
