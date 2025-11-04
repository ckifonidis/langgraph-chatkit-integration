/**
 * Centralized API layer for preference operations
 *
 * Consolidates all API endpoint calls for favorites and hidden properties.
 * All functions return fetch Promises for use with PreferencesContext.updatePreferences()
 */

interface PropertyData {
  code: string;
  title: string;
  price: number;
  [key: string]: any;
}

export const preferenceApi = {
  /**
   * Add a property to favorites
   */
  addFavorite: (threadId: string, propertyCode: string, propertyData: PropertyData) =>
    fetch('/langgraph/preferences/favorites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        thread_id: threadId,
        propertyCode,
        propertyData,
      }),
    }),

  /**
   * Remove a property from favorites
   */
  removeFavorite: (threadId: string, propertyCode: string) =>
    fetch(`/langgraph/preferences/favorites/${propertyCode}?thread_id=${encodeURIComponent(threadId)}`, {
      method: 'DELETE',
      credentials: 'include',
    }),

  /**
   * Hide a property
   */
  hideProperty: (threadId: string, propertyCode: string, propertyData: PropertyData) =>
    fetch('/langgraph/preferences/hidden', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        thread_id: threadId,
        propertyCode,
        propertyData,
      }),
    }),

  /**
   * Unhide a property
   */
  unhideProperty: (threadId: string, propertyCode: string) =>
    fetch(`/langgraph/preferences/hidden/${propertyCode}?thread_id=${encodeURIComponent(threadId)}`, {
      method: 'DELETE',
      credentials: 'include',
    }),
};
