// The browser's Geolocation API. Browsers only allow it over HTTPS, or on localhost.
import type { Coordinates } from '@/api';

const LOCATION_TIMEOUT_MS = 20_000;
// A position from the last minute is fine; an older one may be from another street.
const MAX_LOCATION_AGE_MS = 60_000;

export function getCurrentLocation(): Promise<Coordinates> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      reject(new Error("This browser can't share your location. Enter coordinates instead."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ lat: position.coords.latitude, lng: position.coords.longitude }),
      (error) => {
        console.warn('Geolocation failed', error.code, error.message);
        reject(new Error(locationErrorMessage(error)));
      },
      { enableHighAccuracy: true, timeout: LOCATION_TIMEOUT_MS, maximumAge: MAX_LOCATION_AGE_MS },
    );
  });
}

function locationErrorMessage(error: GeolocationPositionError): string {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return "Location access is blocked. Allow it in your browser's site settings, or enter coordinates instead.";
    case error.TIMEOUT:
      return 'Finding your location took too long. Try again, or enter coordinates instead.';
    default:
      return "Couldn't find your location. Try again, or enter coordinates instead.";
  }
}
