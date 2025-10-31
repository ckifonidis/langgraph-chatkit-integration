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
