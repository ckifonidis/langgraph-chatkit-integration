import { useState } from 'react';
import clsx from 'clsx';
import {
  usePreferences,
  getFavoritesArray,
  getHiddenArray,
  getFavoritesCount,
  getHiddenCount,
} from '../contexts/PreferencesContext';
import { usePropertyActions } from '../hooks/usePropertyActions';
import { PropertyDetailModal } from './PropertyDetailModal';

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

export function PreferencesSidebar() {
  const { preferences, loading, currentThreadId, refreshPreferences, triggerThreadReload } = usePreferences();
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const favoritesCount = getFavoritesCount(preferences);
  const hiddenCount = getHiddenCount(preferences);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white/80 p-6 shadow-lg ring-2 ring-[#00BA88]/30 backdrop-blur dark:bg-slate-900/70 dark:ring-[#00BA88]/40">
        <div className="animate-pulse">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-3xl bg-white/80 shadow-lg ring-2 ring-[#00BA88]/30 backdrop-blur dark:bg-slate-900/70 dark:ring-[#00BA88]/40">
      {/* Collapsed View */}
      {!isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full p-6 text-left transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-800/50"
        >
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#00BA88]/10">
                <svg
                  className="h-5 w-5 text-[#00BA88]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                  This Conversation
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {favoritesCount} favorites • {hiddenCount} hidden
                </p>
              </div>
            </div>
            <svg
              className="h-5 w-5 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </button>
      )}

      {/* Expanded View */}
      {isExpanded && (
        <div className="p-6">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#00BA88]/10">
                <svg
                  className="h-5 w-5 text-[#00BA88]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                  This Conversation
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {favoritesCount} favorites • {hiddenCount} hidden
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="rounded-lg p-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <svg
                className="h-5 w-5 text-slate-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 15l7-7 7 7"
                />
              </svg>
            </button>
          </div>

          {/* Favorites Section */}
          {favoritesCount > 0 && (
            <div className="mb-6">
              <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#00BA88]">
                <svg
                  className="h-4 w-4"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                Favorites
              </h4>
              <div className="max-h-96 space-y-3 overflow-y-auto">
                {getFavoritesArray(preferences).map((property) => (
                  <PropertyCard
                    key={property.code}
                    property={property}
                    onCardClick={() => {
                      setSelectedProperty(property);
                      setIsModalOpen(true);
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Hidden Section */}
          {hiddenCount > 0 && (
            <div>
              <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-400">
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                  />
                </svg>
                Hidden Properties
              </h4>
              <div className="max-h-96 space-y-3 overflow-y-auto">
                {getHiddenArray(preferences).map((property) => (
                  <PropertyCard
                    key={property.code}
                    property={property}
                    isHidden
                    onCardClick={() => {
                      setSelectedProperty(property);
                      setIsModalOpen(true);
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {favoritesCount === 0 && hiddenCount === 0 && (
            <div className="py-8 text-center">
              <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                <svg
                  className="h-8 w-8 text-slate-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                  />
                </svg>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                No preferences saved yet
              </p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
                Favorite properties or hide listings to get started
              </p>
            </div>
          )}
        </div>
      )}

      {/* Property Detail Modal */}
      <PropertyDetailModal
        isOpen={isModalOpen}
        onClose={async () => {
          setIsModalOpen(false);
          setSelectedProperty(null);
          // Reload thread items after modal closes to reflect any preference changes
          await triggerThreadReload();
        }}
        property={selectedProperty}
      />
    </div>
  );
}

function PropertyCard({
  property,
  isHidden = false,
  onCardClick,
}: {
  property: PropertyData;
  isHidden?: boolean;
  onCardClick: () => void;
}) {
  // Use the centralized property actions hook
  // Sidebar actions trigger immediate reload (skipThreadReload: false is default)
  const { toggleFavorite, toggleHide, isUpdating } = usePropertyActions(
    property.code,
    property,
    { skipThreadReload: false } // Sidebar actions need immediate reload
  );

  const formatPrice = (price: number) => {
    return price ? `€${price.toLocaleString()}` : 'Price on request';
  };

  const formatSpecs = () => {
    const specs = [];
    if (property.propertyArea) specs.push(`${property.propertyArea}sqm`);
    if (property.numberOfRooms) specs.push(`${property.numberOfRooms} rooms`);
    if (property.numberOfBathrooms) specs.push(`${property.numberOfBathrooms} bath`);
    return specs.join(' • ');
  };

  const handleRemove = async (e: React.MouseEvent) => {
    e.stopPropagation();

    // Call the appropriate toggle function based on context
    if (isHidden) {
      await toggleHide(); // Unhide
    } else {
      await toggleFavorite(); // Remove from favorites
    }
  };

  return (
    <div
      onClick={onCardClick}
      className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition-all hover:shadow-md hover:ring-2 hover:ring-[#00BA88]/50 cursor-pointer dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="flex gap-3">
        {/* Image */}
        {property.defaultImagePath && (
          <div className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg">
            <img
              src={property.defaultImagePath}
              alt={property.title}
              className="h-full w-full object-cover"
            />
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h5 className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
            {property.title}
          </h5>
          <p className="mt-1 text-base font-bold text-[#00BA88]">
            {formatPrice(property.price)}
          </p>
          {formatSpecs() && (
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
              {formatSpecs()}
            </p>
          )}
          {property.address?.prefecture && (
            <p className="mt-1 flex items-center gap-1 text-xs text-slate-500 dark:text-slate-500">
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {property.address.prefecture}
            </p>
          )}
        </div>
      </div>

      {/* Remove/Unhide Button */}
      <div className="absolute bottom-2 right-2">
        <button
          onClick={handleRemove}
          disabled={isUpdating}
          className={clsx(
            "rounded-lg p-1.5 transition-all",
            isUpdating && "opacity-50 cursor-not-allowed",
            !isUpdating && "hover:bg-slate-100 dark:hover:bg-slate-700 hover:scale-110"
          )}
          title={isHidden ? "Unhide property" : "Remove from favorites"}
        >
          {isHidden ? (
            // Eye icon for unhiding
            <svg
              className="h-5 w-5 text-slate-500 hover:text-[#00BA88]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
          ) : (
            // X icon for removing from favorites
            <svg
              className="h-5 w-5 text-slate-400 hover:text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
