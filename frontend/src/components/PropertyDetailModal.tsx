import { Fragment, useEffect, useState } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { XMarkIcon, CheckIcon, XCircleIcon } from "@heroicons/react/24/outline";

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

  // Get API key
  const mapsApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

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

  if (!property) return null;

  const formatPrice = (price?: number) => {
    if (!price) return "Price on request";
    return `€${price.toLocaleString()}`;
  };

  const amenitiesList = parseAmenities(property.amenities);
  const floorMaterial = formatArray(property.floorMaterial);

  // Get coordinates for Google Maps
  const coords = property.address?.geoPoint?.coordinates;
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
                        {property.title || "Property Details"}
                      </Dialog.Title>
                      {property.code && (
                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                          Property Code: {property.code}
                        </p>
                      )}
                    </div>
                    <button
                      type="button"
                      className="flex-shrink-0 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors"
                      onClick={onClose}
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>
                </div>

                {/* Content */}
                <div className="px-6 py-6 max-h-[75vh] overflow-y-auto">
                  {/* Image */}
                  {property.defaultImagePath && (
                    <div className="mb-6">
                      <img
                        src={property.defaultImagePath}
                        alt={property.title || "Property"}
                        className="w-full h-96 object-cover rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg"
                      />
                    </div>
                  )}

                  {/* Price */}
                  <div className="mb-6">
                    <div className="inline-flex items-center px-5 py-3 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 font-bold text-3xl shadow-sm">
                      {formatPrice(property.price)}
                    </div>
                  </div>

                  {/* Key Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {(property.propertyArea ?? 0) > 0 && (
                      <StatCard label="Area" value={`${property.propertyArea}m²`} />
                    )}
                    {(property.numberOfRooms ?? 0) > 0 && (
                      <StatCard label="Rooms" value={property.numberOfRooms.toString()} />
                    )}
                    {(property.numberOfBathrooms ?? 0) > 0 && (
                      <StatCard label="Bathrooms" value={property.numberOfBathrooms.toString()} />
                    )}
                    {property.floor !== undefined && property.floor !== null && (
                      <StatCard label="Floor" value={property.floor.toString()} />
                    )}
                  </div>

                  {/* Location */}
                  {property.address && (
                    <Section title="📍 Location" className="mb-6">
                      <div className="space-y-3">
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                          <p className="text-slate-700 dark:text-slate-300 font-medium">
                            {[
                              property.address.prefecture,
                              property.address.city,
                              property.address.area,
                            ]
                              .filter(Boolean)
                              .join(", ")}
                          </p>
                          {property.address.fullAddress && (
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                              {property.address.fullAddress}
                            </p>
                          )}
                        </div>

                        {/* Embedded Google Map with Circle Range */}
                        {lat && lng && mapsLoaded && (
                          <div className="space-y-2">
                            <div
                              ref={(el) => {
                                if (!el || !window.google) return;

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
                              const address = property.address?.fullAddress || [
                                property.address?.prefecture,
                                property.address?.city,
                                property.address?.area,
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
                  {property.description && property.description !== "Property Description" && (
                    <Section title="📋 Description" className="mb-6">
                      <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                        {property.description}
                      </p>
                    </Section>
                  )}

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
                      {property.type && (
                        <DetailRow label="Type" value={property.type} />
                      )}
                      {(property.constructionYear ?? 0) > 0 && (
                        <DetailRow label="Construction Year" value={property.constructionYear.toString()} />
                      )}
                      {property.energyClass && (
                        <div className="flex justify-between items-center py-2">
                          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            Energy Class
                          </span>
                          <span className={`px-3 py-1 rounded-full text-sm font-bold ${getEnergyClassColor(property.energyClass)}`}>
                            {property.energyClass}
                          </span>
                        </div>
                      )}
                      {property.availability && (
                        <div className="flex justify-between items-center py-2">
                          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                            Availability
                          </span>
                          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            property.availability.toLowerCase() === "vacant"
                              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
                          }`}>
                            {property.availability}
                          </span>
                        </div>
                      )}
                      {property.frames && (
                        <DetailRow label="Window Frames" value={property.frames} />
                      )}
                      {floorMaterial && (
                        <DetailRow label="Flooring" value={floorMaterial} />
                      )}
                      {(property.renovationYear ?? 0) > 0 && (
                        <DetailRow label="Renovation Year" value={property.renovationYear.toString()} />
                      )}
                      {property.kaek && (
                        <DetailRow label="KAEK Code" value={property.kaek} />
                      )}
                    </div>
                  </Section>

                  {/* Heating & Climate */}
                  {(property.heatingType || property.heatingControl) && (
                    <Section title="🔥 Heating & Climate" className="mb-6">
                      <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                        <div className="space-y-2">
                          {property.heatingType && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-orange-900 dark:text-orange-300">
                                Type:
                              </span>
                              <span className="text-sm text-slate-700 dark:text-slate-300">
                                {formatHeatingType(property.heatingType)}
                              </span>
                            </div>
                          )}
                          {property.heatingControl && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-orange-900 dark:text-orange-300">
                                Control:
                              </span>
                              <span className="text-sm text-slate-700 dark:text-slate-300">
                                {property.heatingControl}
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
                      {(property.plotArea ?? 0) > 0 && (
                        <DetailRow label="Plot Area" value={`${property.plotArea}m²`} />
                      )}
                      {(property.basementSize ?? 0) > 0 && (
                        <DetailRow label="Basement" value={`${property.basementSize}m²`} />
                      )}
                      {(property.numberOfFloors ?? 0) > 0 && (
                        <DetailRow label="Number of Floors" value={property.numberOfFloors.toString()} />
                      )}
                      {(property.numberOfWC ?? 0) > 0 && (
                        <DetailRow label="WCs" value={property.numberOfWC.toString()} />
                      )}
                      {(property.masterRoom ?? 0) > 0 && (
                        <DetailRow label="Master Bedrooms" value={property.masterRoom.toString()} />
                      )}
                    </div>
                  </Section>

                  {/* Parking & Storage */}
                  {(
                    (property.parkingType && property.parkingType.length > 0) ||
                    (property.parkingSpace ?? 0) > 0 ||
                    (property.storageArea ?? 0) > 0
                  ) && (
                    <Section title="🚗 Parking & Storage" className="mb-6">
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                        <div className="space-y-2">
                          {property.parkingType && property.parkingType.length > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                Parking:
                              </span>
                              <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold">
                                {formatParkingType(property.parkingType)}
                              </span>
                            </div>
                          )}
                          {(property.parkingSpace ?? 0) > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                Parking Spaces:
                              </span>
                              <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold">
                                {property.parkingSpace}
                              </span>
                            </div>
                          )}
                          {(property.storageArea ?? 0) > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                Storage:
                              </span>
                              <span className="text-sm text-slate-900 dark:text-slate-100 font-semibold">
                                {property.storageArea}m²
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </Section>
                  )}

                  {/* Neighborhood */}
                  {property.neighborhood && (
                    <Section title="🏘️ Neighborhood" className="mb-6">
                      <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                          {property.neighborhood}
                        </p>
                      </div>
                    </Section>
                  )}

                  {/* Financial Info (if pre-approval exists) */}
                  {(property.preApprovalAmmount ?? 0) > 0 && (
                    <Section title="💰 Financial Information" className="mb-6">
                      <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-purple-900 dark:text-purple-300">
                            Pre-Approved Amount
                          </span>
                          <span className="text-lg font-bold text-purple-700 dark:text-purple-400">
                            €{property.preApprovalAmmount.toLocaleString()}
                          </span>
                        </div>
                        {property.preApproved && (
                          <p className="text-xs text-purple-600 dark:text-purple-400 mt-2">
                            Status: {property.preApproved}
                          </p>
                        )}
                      </div>
                    </Section>
                  )}
                </div>

                {/* Footer */}
                <div className="border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 px-6 py-4">
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
