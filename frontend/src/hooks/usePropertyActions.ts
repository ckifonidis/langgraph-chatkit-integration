import { useState } from 'react';
import { usePreferences } from '../contexts/PreferencesContext';
import { preferenceApi } from '../utils/preferenceApi';

interface PropertyData {
  code: string;
  title: string;
  price: number;
  [key: string]: any;
}

interface UsePropertyActionsOptions {
  /**
   * Whether to skip thread reload after actions.
   * - true: Skip reload (modal context - refresh on modal close instead)
   * - false: Trigger immediate reload (sidebar context - immediate feedback)
   */
  skipThreadReload?: boolean;
}

/**
 * Reusable hook for property preference actions (favorite/unfavorite, hide/unhide)
 *
 * Encapsulates:
 * - State checks (isFavorited, isHidden)
 * - Loading states (isUpdating)
 * - API calls via preferenceApi
 * - Integration with PreferencesContext
 *
 * @param propertyCode - Property code to manage
 * @param propertyData - Full property data object
 * @param options - Configuration options
 * @returns Object with state and action handlers
 */
export function usePropertyActions(
  propertyCode: string | undefined,
  propertyData: PropertyData | null,
  options: UsePropertyActionsOptions = {}
) {
  const { skipThreadReload = false } = options;
  const { preferences, updatePreferences, currentThreadId } = usePreferences();
  const [isUpdating, setIsUpdating] = useState(false);

  // State checks
  const isFavorited = propertyCode ? propertyCode in preferences.favorites : false;
  const isHidden = propertyCode ? propertyCode in preferences.hidden : false;

  /**
   * Toggle favorite status
   * @returns Promise<boolean> - Success status
   */
  const toggleFavorite = async (): Promise<boolean> => {
    if (!currentThreadId || !propertyCode || !propertyData) {
      console.error('[usePropertyActions] Missing required data:', {
        currentThreadId,
        propertyCode,
        hasPropertyData: !!propertyData,
      });
      return false;
    }

    setIsUpdating(true);
    try {
      const success = await updatePreferences(
        () =>
          isFavorited
            ? preferenceApi.removeFavorite(currentThreadId, propertyCode)
            : preferenceApi.addFavorite(currentThreadId, propertyCode, propertyData),
        { skipThreadReload }
      );

      if (success) {
        console.log(
          `[usePropertyActions] ✅ ${isFavorited ? 'Removed from' : 'Added to'} favorites:`,
          propertyCode
        );
      } else {
        console.error('[usePropertyActions] ❌ Failed to update favorite');
      }

      return success;
    } catch (error) {
      console.error('[usePropertyActions] Error toggling favorite:', error);
      return false;
    } finally {
      setIsUpdating(false);
    }
  };

  /**
   * Toggle hidden status
   * @returns Promise<boolean> - Success status
   */
  const toggleHide = async (): Promise<boolean> => {
    if (!currentThreadId || !propertyCode || !propertyData) {
      console.error('[usePropertyActions] Missing required data:', {
        currentThreadId,
        propertyCode,
        hasPropertyData: !!propertyData,
      });
      return false;
    }

    setIsUpdating(true);
    try {
      const success = await updatePreferences(
        () =>
          isHidden
            ? preferenceApi.unhideProperty(currentThreadId, propertyCode)
            : preferenceApi.hideProperty(currentThreadId, propertyCode, propertyData),
        { skipThreadReload }
      );

      if (success) {
        console.log(
          `[usePropertyActions] ✅ ${isHidden ? 'Unhid' : 'Hid'} property:`,
          propertyCode
        );
      } else {
        console.error('[usePropertyActions] ❌ Failed to update hidden status');
      }

      return success;
    } catch (error) {
      console.error('[usePropertyActions] Error toggling hide:', error);
      return false;
    } finally {
      setIsUpdating(false);
    }
  };

  return {
    isFavorited,
    isHidden,
    isUpdating,
    toggleFavorite,
    toggleHide,
  };
}
