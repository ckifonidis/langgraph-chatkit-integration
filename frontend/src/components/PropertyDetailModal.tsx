import { Fragment, useEffect, useState, useRef } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { XMarkIcon, CheckIcon, XCircleIcon, StarIcon } from "@heroicons/react/24/outline";
import { StarIcon as StarIconSolid } from "@heroicons/react/24/solid";
import { usePreferences } from "../contexts/PreferencesContext";
import { Tooltip } from "./Tooltip";

// Google Maps type declarations
declare global {
  interface Window {
    google: any;
  }
}

interface PropertyData {
  code?: string;
  title?: string;
  price?: number;
  propertyArea?: number;
  numberOfRooms?: number;
  numberOfBathrooms?: number;
  numberOfFloors?: number;
  numberOfWC?: number;
  defaultImagePath?: string;
  address?: {
    prefecture?: string;
    city?: string;
    area?: string;
    fullAddress?: string;
    country?: string;
    postalCode?: string;
    geoPoint?: {
      type?: string;
      coordinates?: [number, number]; // GeoJSON format: [longitude, latitude]
    };
  };
  // Coordinates can be at various levels
  latitude?: number;
  longitude?: number;
  lat?: number;
  lng?: number;
  coordinates?: {
    latitude?: number;
    longitude?: number;
  };
  propertyType?: string;
  type?: string;
  floor?: number;
  constructionYear?: number;
  energyClass?: string;
  availability?: string;
  frames?: string;
  floorMaterial?: string[] | string;
  amenities?: {
    hasElevator?: boolean;
    hasAlarm?: boolean;
    hasSafetyDoor?: boolean;
    hasGarden?: boolean;
    hasPool?: boolean;
    internalStaircase?: boolean;
  };
  plotArea?: number;
  basementSize?: number;
  description?: string;
  heatingType?: string;
  heatingControl?: string;
  parkingType?: string[];
  parkingSpace?: number;
  storageArea?: number;
  storageType?: string[];
  masterRoom?: number;
  renovationYear?: number;
  neighborhood?: string;
  kaek?: string;
  [key: string]: any;
}

interface PropertyDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  property: PropertyData | null;
}

// Helper function to get energy class badge color
function getEnergyClassColor(energyClass?: string): string {
  if (!energyClass) return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  const grade = energyClass.toUpperCase();
  if (grade.includes("A+") || grade === "A") return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
  if (grade === "B") return "bg-lime-100 text-lime-700 dark:bg-lime-900/30 dark:text-lime-400";
  if (grade === "C") return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
  if (grade === "D") return "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400";
  return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
}

// Helper function to parse amenities
function parseAmenities(amenities?: any): { label: string; value: boolean }[] {
  if (!amenities || typeof amenities !== "object") return [];

  const amenityMap: { [key: string]: string } = {
    hasElevator: "Elevator",
    hasAlarm: "Alarm System",
    hasSafetyDoor: "Safety Door",
    hasGarden: "Garden",
    hasPool: "Swimming Pool",
    internalStaircase: "Internal Staircase",
    accessibilityForDisabled: "Wheelchair Accessible",
    hasPlayroom: "Playroom",
    hasStorageRoom: "Storage Room",
    petsAreAllowed: "Pets Allowed",
    hasSolarWaterHeating: "Solar Water Heating",
    hasNightElectricCurrent: "Night Electric Current",
    hasBoiler: "Boiler",
    sieves: "Window Screens",
    hasTents: "Awnings",
    isAiry: "Well Ventilated",
    isBright: "Bright & Sunny",
    isPenthouse: "Penthouse",
    isFloorApartment: "Through Apartment",
    suitableForTouristUse: "Tourist Rental Approved",
    suitableForProfessionalUse: "Commercial Use Approved",
  };

  return Object.entries(amenities)
    .filter(([key]) => key in amenityMap)
    .map(([key, value]) => ({
      label: amenityMap[key],
      value: Boolean(value),
    }))
    .sort((a, b) => {
      // Sort: true values first, then alphabetically
      if (a.value === b.value) return a.label.localeCompare(b.label);
      return a.value ? -1 : 1;
    });
}

// Helper function to format arrays
function formatArray(value: any): string | null {
  if (Array.isArray(value)) {
    return value.filter(Boolean).join(", ") || null;
  }
  return null;
}

// Helper function to format heating type
function formatHeatingType(type?: string): string | null {
  if (!type) return null;
  const heatingMap: { [key: string]: string } = {
    HeatingOil: "Oil Heating",
    NaturalGas: "Natural Gas",
    ElectricAirConditioning: "Air Conditioning",
    HeatPump: "Heat Pump",
  };
  return heatingMap[type] || type;
}

// Helper function to format parking type
function formatParkingType(types?: string[]): string | null {
  if (!types || types.length === 0) return null;
  const parkingMap: { [key: string]: string } = {
    Open: "Open Parking",
    Closed: "Garage",
    Underground: "Underground Parking",
    Other: "Other",
  };
  return types.map(t => parkingMap[t] || t).join(", ");
}

export function PropertyDetailModal({
  isOpen,
  onClose,
  property,
}: PropertyDetailModalProps) {
  const [mapsLoaded, setMapsLoaded] = useState(false);
  const { preferences, updatePreferences, currentThreadId } = usePreferences();
  const [isTogglingFavorite, setIsTogglingFavorite] = useState(false);
  const [isHiding, setIsHiding] = useState(false);
  const mapInstanceRef = useRef<any>(null);

  // Description generation state
  const [isLoadingDescription, setIsLoadingDescription] = useState(false);
  const [descriptionError, setDescriptionError] = useState<string | null>(null);
  const [enhancedProperty, setEnhancedProperty] = useState<PropertyData | null>(property);

  // Get API key
  const mapsApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  // Check if property is favorited
  const isFavorited = property?.code ? property.code in preferences.favorites : false;
  const isHidden = property?.code ? property.code in preferences.hidden : false;

  // Handle favorite toggle
  const handleToggleFavorite = async () => {
    if (!property?.code || !currentThreadId) return;

    console.log('[FAVORITE] Toggle clicked, isFavorited:', isFavorited, 'property:', property.code);

    setIsTogglingFavorite(true);
    try {
      const success = await updatePreferences(() => {
        if (isFavorited) {
          // Remove from favorites
          console.log('[FAVORITE] Removing from favorites...');
          return fetch(`/langgraph/preferences/favorites/${property.code}?thread_id=${encodeURIComponent(currentThreadId)}`, {
            method: 'DELETE',
            credentials: 'include',
          });
        } else {
          // Add to favorites
          console.log('[FAVORITE] Adding to favorites...');
          return fetch('/langgraph/preferences/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              thread_id: currentThreadId,
              propertyCode: property.code,
              propertyData: property,
            }),
          });
        }
      });

      if (success) {
        console.log('[FAVORITE] ✅ Successfully updated favorites');
      } else {
        console.error('[FAVORITE] ❌ Failed to update favorites');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    } finally {
      setIsTogglingFavorite(false);
    }
  };

  // Handle hide/unhide toggle
  const handleToggleHide = async () => {
    if (!property?.code || !currentThreadId) return;

    setIsHiding(true);
    try {
      const success = await updatePreferences(() => {
        if (isHidden) {
          // Unhide property
          return fetch(`/langgraph/preferences/hidden/${property.code}?thread_id=${encodeURIComponent(currentThreadId)}`, {
            method: 'DELETE',
            credentials: 'include',
          });
        } else {
          // Hide property
          return fetch('/langgraph/preferences/hidden', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              thread_id: currentThreadId,
              propertyCode: property.code,
              propertyData: property,
            }),
          });
        }
      });

      if (success) {
        console.log('[HIDE] ✅ Successfully updated hidden properties');
      } else {
        console.error('[HIDE] ❌ Failed to update hidden properties');
      }
    } catch (error) {
      console.error('Error toggling hide:', error);
    } finally {
      setIsHiding(false);
    }
  };

  // Dynamically load Google Maps API
  useEffect(() => {
    if (window.google || !mapsApiKey) {
      setMapsLoaded(true);
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${mapsApiKey}&loading=async`;
    script.async = true;
    script.defer = true;
    script.onload = () => setMapsLoaded(true);
    document.head.appendChild(script);
  }, [mapsApiKey]);

  // Reset map instance when modal closes or property changes
  useEffect(() => {
    if (!isOpen) {
      mapInstanceRef.current = null;
    }
  }, [isOpen, property?.code]);

  // Sync enhanced property with incoming property prop
  useEffect(() => {
    if (property) {
      setEnhancedProperty(property);
      setDescriptionError(null);
    }
  }, [property?.code]);

  // Auto-fetch description when modal opens
  useEffect(() => {
    const fetchDescription = async () => {
      if (!isOpen || !property?.code || !property) return;

      // Skip if already loading
      if (isLoadingDescription) return;

      setIsLoadingDescription(true);
      setDescriptionError(null);

      try {
        const response = await fetch('/langgraph/generate-description', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            propertyCode: property.code,
            propertyData: property,
            language: 'english',
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to generate description');
        }

        const data = await response.json();

        // Update property with AI-generated description
        setEnhancedProperty((prev) => ({
          ...prev!,
          description: data.description,
        }));

      } catch (error) {
        console.error('Description generation error:', error);
        setDescriptionError('Unable to generate AI description');
      } finally {
        setIsLoadingDescription(false);
      }
    };

    fetchDescription();
  }, [isOpen, property?.code]);

  if (!property) return null;

  // Use enhanced property for display
  const displayProperty = enhancedProperty || property;

  const formatPrice = (price?: number) => {
    if (!price) return "Price on request";
    return `€${price.toLocaleString()}`;
  };

  const amenitiesList = parseAmenities(displayProperty.amenities);
  const floorMaterial = formatArray(displayProperty.floorMaterial);

  // Get coordinates for Google Maps
  const coords = displayProperty.address?.geoPoint?.coordinates;
  let lat: number | undefined;
  let lng: number | undefined;

  if (coords && coords.length === 2) {
    // GeoJSON format: [longitude, latitude]
    lng = coords[0];
    lat = coords[1];
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white dark:bg-slate-900 shadow-2xl transition-all">
                {/* Header */}
                <div className="relative border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-900 px-6 py-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Dialog.Title className="text-2xl font-bold text-slate-900 dark:text-slate-100 pr-8">
                        {displayProperty.title || "Property Details"}
                      </Dialog.Title>
                      {displayProperty.code && (
                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                          Property Code: {displayProperty.code}
                        </p>
                      )}
                    </div>
                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      {/* Favorite Button */}
                      <Tooltip content={isFavorited ? "Click to remove from favorites" : "Click to add to favorites"}>
                        <button
                          type="button"
                          onClick={handleToggleFavorite}
                          disabled={isTogglingFavorite}
                          className="flex-shrink-0 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-yellow-500 dark:hover:bg-slate-800 dark:hover:text-yellow-400 transition-colors disabled:opacity-50"
                        >
                          {isFavorited ? (
                            <StarIconSolid className="h-6 w-6 text-yellow-500" />
                          ) : (
                            <StarIcon className="h-6 w-6" />
                          )}
                        </button>
                      </Tooltip>

                      {/* Hide/Unhide Button */}
                      <Tooltip content={isHidden ? "Click to unhide this property" : "Click to hide this property"}>
                        <button
                          type="button"
                          onClick={handleToggleHide}
                          disabled={isHiding}
                          className="flex-shrink-0 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors disabled:opacity-50"
                        >
                          {isHidden ? (
                            // Eye icon (visible/unhide)
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          ) : (
                            // Eye-slash icon (hidden/hide)
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                            </svg>
                          )}
                        </button>
                      </Tooltip>

                      {/* Close Button */}
                      <Tooltip content="Close modal">
                        <button
                          type="button"
                          className="flex-shrink-0 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors"
                          onClick={onClose}
                        >
                          <XMarkIcon className="h-6 w-6" />
                        </button>
                      </Tooltip>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="px-6 py-6 max-h-[75vh] overflow-y-auto">
                  {/* Image */}
                  {displayProperty.defaultImagePath && (
                    <div className="mb-6">
                      <img
                        src={displayProperty.defaultImagePath}
                        alt={displayProperty.title || "Property"}
                        className="w-full h-96 object-cover rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg"
                      />
                    </div>
                  )}

                  {/* Price */}
                  <div className="mb-6">
                    <div className="inline-flex items-center px-5 py-3 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 font-bold text-3xl shadow-sm">
                      {formatPrice(displayProperty.price)}
                    </div>
                  </div>

                  {/* Key Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {(displayProperty.propertyArea ?? 0) > 0 && (
                      <StatCard label="Area" value={`${displayProperty.propertyArea}m²`} />
                    )}
                    {(displayProperty.numberOfRooms ?? 0) > 0 && (
                      <StatCard label="Rooms" value={displayProperty.numberOfRooms.toString()} />
                    )}
                    {(displayProperty.numberOfBathrooms ?? 0) > 0 && (
                      <StatCard label="Bathrooms" value={displayProperty.numberOfBathrooms.toString()} />
                    )}
                    {displayProperty.floor !== undefined && displayProperty.floor !== null && (
                      <StatCard label="Floor" value={displayProperty.floor.toString()} />
                    )}
                  </div>

                  {/* Location */}
                  {displayProperty.address && (
                    <Section title="📍 Location" className="mb-6">
                      <div className="space-y-3">
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                          <p className="text-slate-700 dark:text-slate-300 font-medium">
                            {[
                              displayProperty.address.prefecture,
                              displayProperty.address.city,
                              displayProperty.address.area,
                            ]
                              .filter(Boolean)
                              .join(", ")}
                          </p>
                          {displayProperty.address.fullAddress && (
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                              {displayProperty.address.fullAddress}
                            </p>
                          )}
                        </div>

                        {/* Embedded Google Map with Circle Range */}
                        {lat && lng && mapsLoaded && (
                          <div className="space-y-2">
                            <div
                              ref={(el) => {
                                if (!el || !window.google) return;

                                // Only create map if it doesn't exist yet
                                if (!mapInstanceRef.current) {
                                  const map = new window.google.maps.Map(el, {
                                    center: { lat, lng },
                                    zoom: 14,
                                    mapTypeControl: true,
                                    streetViewControl: false,
                                    gestureHandling: 'cooperative',
                                  });

                                  new window.google.maps.Circle({
                                    center: { lat, lng },
                                    radius: 500, // 500 meters - same for all properties
                                    strokeColor: '#00BA88',
                                    strokeOpacity: 1,
                                    strokeWeight: 2,
                                    fillColor: '#00BA88',
                                    fillOpacity: 0.25,
                                    map: map,
                                  });

                                  mapInstanceRef.current = map;
                                }
                              }}
                              className="w-full h-[350px] rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg"
                            />
                            <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                              <span>📍</span>
                              <span>Approximate location shown (500m radius) for privacy</span>
                            </p>
                          </div>
                        )}

                        {/* Fallback: Open in new tab button if no coordinates */}
                        {(!lat || !lng) && (
                          <button
                            type="button"
                            onClick={() => {
                              const address = displayProperty.address?.fullAddress || [
                                displayProperty.address?.prefecture,
                                displayProperty.address?.city,
                                displayProperty.address?.area,
                              ].filter(Boolean).join(", ");
                              const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
                              window.open(mapsUrl, "_blank", "noopener,noreferrer");
                            }}
                            className="w-full inline-flex justify-center items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white font-medium text-sm transition-colors shadow-sm"
                          >
                            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                            </svg>
                            View on Google Maps
                          </button>
                        )}
                      </div>
                    </Section>
                  )}

                  {/* Description */}
                  <Section title="📋 Description" className="mb-6">
                    {isLoadingDescription ? (
                      <div className="animate-pulse space-y-3">
                        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
                        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
                        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-4/6"></div>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-4 flex items-center gap-2">
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Generating AI description...
                        </p>
                      </div>
                    ) : descriptionError ? (
                      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
                        <p className="text-red-700 dark:text-red-400 text-sm mb-2">{descriptionError}</p>
                        <button
                          type="button"
                          onClick={() => {
                            setDescriptionError(null);
                            setIsLoadingDescription(false);
                            // Re-trigger fetch by toggling a flag or manually calling
                            const triggerRefetch = async () => {
                              setIsLoadingDescription(true);
                              try {
                                const response = await fetch('/langgraph/generate-description', {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  credentials: 'include',
                                  body: JSON.stringify({
                                    propertyCode: property.code,
                                    propertyData: property,
                                    language: 'english',
                                  }),
                                });
                                if (!response.ok) throw new Error('Failed to generate description');
                                const data = await response.json();
                                setEnhancedProperty((prev) => ({ ...prev!, description: data.description }));
                              } catch (error) {
                                setDescriptionError('Unable to generate AI description');
                              } finally {
                                setIsLoadingDescription(false);
                              }
                            };
                            triggerRefetch();
                          }}
                          className="text-xs text-red-600 dark:text-red-400 hover:underline font-medium"
                        >
                          Retry
                        </button>
                      </div>
                    ) : displayProperty.description && displayProperty.description !== "Property Description" ? (
                      <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                        {displayProperty.description}
                      </p>
                    ) : (
                      <p className="text-slate-500 dark:text-slate-400 italic text-sm">
                        No description available
                      </p>
                    )}
                  </Section>

                  {/* Features & Amenities */}
                  {amenitiesList.length > 0 && (
                    <Section title="✨ Features & Amenities" className="mb-6">
                      <div className="grid grid-cols-2 gap-3">
                        {amenitiesList.map((amenity) => (
                          <div
                            key={amenity.label}
                            className="flex items-center gap-2"
                          >
                            {amenity.value ? (
                              <CheckIcon className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                            ) : (
                              <XCircleIcon className="h-5 w-5 text-slate-300 dark:text-slate-600 flex-shrink-0" />
                            )}
                            <span
                              className={`text-sm ${
                                amenity.value
                                  ? "text-slate-700 dark:text-slate-300 font-medium"
                                  : "text-slate-400 dark:text-slate-600"
                              }`}
                            >
                              {amenity.label}
                            </span>
                          </div>
                        ))}
                      </div>
                    </Section>
                  )}

                  {/* Property Overview */}
                  <Section title="🏠 Property Overview" className="mb-6">
                    <div className="space-y-3">
                      {displayProperty.type && (
                        <DetailRow label="Type" value={displayProperty.type} />
                      )}
                      {(displayProperty.constructionYear ?? 0) > 0 && (
                        <DetailRow label="Construction Year" value={displayProperty.constructionYear.toString()} />
                      )}
                      {displayProperty.energyClass && (
                        <div className="flex justify-between items-center py-2">
                          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            Energy Class
                          </span>
                          <span className={`px-3 py-1 rounded-full text-sm font-bold ${getEnergyClassColor(displayProperty.energyClass)}`}>
                            {displayProperty.energyClass}
                          </span>
                        </div>
                      )}
                      {displayProperty.availability && (
                        <div className="flex justify-between items-center py-2">
                          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            Availability
                          </span>
                          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            displayProperty.availability.toLowerCase() === "vacant"
                              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
                          }`}>
                            {displayProperty.availability}
                          </span>
                        </div>
                      )}
                      {displayProperty.frames && (
                        <DetailRow label="Window Frames" value={displayProperty.frames} />
                      )}
                      {floorMaterial && (
                        <DetailRow label="Flooring" value={floorMaterial} />
                      )}
                      {(displayProperty.renovationYear ?? 0) > 0 && (
                        <DetailRow label="Renovation Year" value={displayProperty.renovationYear.toString()} />
                      )}
                      {displayProperty.kaek && (
                        <DetailRow label="KAEK Code" value={displayProperty.kaek} />
                      )}
                    </div>
                  </Section>

                  {/* Heating & Climate */}
                  {(displayProperty.heatingType || displayProperty.heatingControl) && (
                    <Section title="🔥 Heating & Climate" className="mb-6">
                      <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                        <div className="space-y-2">
                          {displayProperty.heatingType && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-orange-900 dark:text-orange-300">
                                Type:
                              </span>
                              <span className="text-sm text-slate-700 dark:text-slate-300">
                                {formatHeatingType(displayProperty.heatingType)}
                              </span>
                            </div>
                          )}
                          {displayProperty.heatingControl && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-orange-900 dark:text-orange-300">
                                Control:
                              </span>
                              <span className="text-sm text-slate-700 dark:text-slate-300">
                                {displayProperty.heatingControl}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </Section>
                  )}

                  {/* Technical Details */}
                  <Section title="🏗️ Technical Details" className="mb-6">
                    <div className="space-y-3">
                      {(displayProperty.plotArea ?? 0) > 0 && (
                        <DetailRow label="Plot Area" value={`${displayProperty.plotArea}m²`} />
                      )}
                      {(displayProperty.basementSize ?? 0) > 0 && (
                        <DetailRow label="Basement" value={`${displayProperty.basementSize}m²`} />
                      )}
                      {(displayProperty.numberOfFloors ?? 0) > 0 && (
                        <DetailRow label="Number of Floors" value={displayProperty.numberOfFloors.toString()} />
                      )}
                      {(displayProperty.numberOfWC ?? 0) > 0 && (
                        <DetailRow label="WCs" value={displayProperty.numberOfWC.toString()} />
                      )}
                      {(displayProperty.masterRoom ?? 0) > 0 && (
                        <DetailRow label="Master Bedrooms" value={displayProperty.masterRoom.toString()} />
                      )}
                    </div>
                  </Section>

                  {/* Parking & Storage */}
                  {(
                    (displayProperty.parkingType && displayProperty.parkingType.length > 0) ||
                    (displayProperty.parkingSpace ?? 0) > 0 ||
                    (displayProperty.storageArea ?? 0) > 0
                  ) && (
                    <Section title="🚗 Parking & Storage" className="mb-6">
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                        <div className="space-y-2">
                          {displayProperty.parkingType && displayProperty.parkingType.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                Parking:
                              </span>
                              <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold">
                                {formatParkingType(displayProperty.parkingType)}
                              </span>
                            </div>
                          )}
                          {(displayProperty.parkingSpace ?? 0) > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                Parking Spaces:
                              </span>
                              <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold">
                                {displayProperty.parkingSpace}
                              </span>
                            </div>
                          )}
                          {(displayProperty.storageArea ?? 0) > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                Storage:
                              </span>
                              <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold">
                                {displayProperty.storageArea}m²
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </Section>
                  )}

                  {/* Neighborhood */}
                  {displayProperty.neighborhood && (
                    <Section title="🏘️ Neighborhood" className="mb-6">
                      <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                          {displayProperty.neighborhood}
                        </p>
                      </div>
                    </Section>
                  )}

                  {/* Financial Info (if pre-approval exists) */}
                  {(displayProperty.preApprovalAmmount ?? 0) > 0 && (
                    <Section title="💰 Financial Information" className="mb-6">
                      <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-purple-900 dark:text-purple-300">
                            Pre-Approved Amount
                          </span>
                          <span className="text-lg font-bold text-purple-700 dark:text-purple-400">
                            €{displayProperty.preApprovalAmmount.toLocaleString()}
                          </span>
                        </div>
                        {displayProperty.preApproved && (
                          <p className="text-xs text-purple-600 dark:text-purple-400 mt-2">
                            Status: {displayProperty.preApproved}
                          </p>
                        )}
                      </div>
                    </Section>
                  )}
                </div>

                {/* Footer */}
                <div className="border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 px-6 py-4">
                  {/* Close Button */}
                  <button
                    type="button"
                    className="w-full inline-flex justify-center items-center px-6 py-3 rounded-lg bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-medium hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors shadow-sm"
                    onClick={onClose}
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

// Section component for organized layout
function Section({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

// Stat card for key metrics
function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
      <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">
        {label}
      </p>
      <p className="text-xl font-bold text-slate-900 dark:text-slate-100">
        {value}
      </p>
    </div>
  );
}

// Detail row for key-value pairs
function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-start py-2 border-b border-slate-100 dark:border-slate-800">
      <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
        {label}
      </span>
      <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold text-right max-w-xs">
        {value}
      </span>
    </div>
  );
}
