// Types and requests for the FastAPI backend (see backend/app/schemas.py).

// In production Caddy serves the web app and the API from the same domain.
const API_URL = __DEV__ ? 'http://localhost:8000' : '';

export type Coordinates = { lat: number; lng: number };
export type Length = 'short' | 'medium' | 'long';
export type Mood = 'historical' | 'historical_emotional' | 'romantic';
export type StoryStatus =
  | 'pending'
  | 'finding_place'
  | 'researching'
  | 'writing'
  | 'generating_audio'
  | 'done'
  | 'failed';

export type Place = {
  name: string;
  description: string | null;
  wikipedia_url: string;
  distance_m: number;
  at_place: boolean;
};

export type Source = { title: string; url: string; license: string };

export type Story = {
  job_id: string;
  status: StoryStatus;
  length: Length;
  mood: Mood;
  place: Place | null;
  transcript: string | null;
  audio_url: string | null;
  duration_seconds: number | null;
  sources: Source[];
  error: string | null;
};

export class ApiError extends Error {
  // 0 means the server couldn't be reached at all.
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export async function findNearbyPlace({ lat, lng }: Coordinates): Promise<Place> {
  const body = await request<{ place: Place }>(`/api/places/nearby?lat=${lat}&lng=${lng}`);
  return body.place;
}

export async function createStory(coordinates: Coordinates, length: Length, mood: Mood): Promise<string> {
  const body = await request<{ job_id: string }>('/api/stories', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...coordinates, length, mood }),
  });
  return body.job_id;
}

export function getStory(jobId: string): Promise<Story> {
  return request<Story>(`/api/stories/${encodeURIComponent(jobId)}`);
}

export function isFinished(status: StoryStatus): boolean {
  return status === 'done' || status === 'failed';
}

// The API returns paths like /api/media/audio/x.mp3.
export function fullUrl(path: string): string {
  return API_URL + path;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(API_URL + path, init);
  } catch (error) {
    console.error(`Request to ${path} failed`, error);
    throw new ApiError("Can't reach the server. Check your connection and try again.", 0);
  }

  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }
  return response.json();
}

// FastAPI puts the reason in "detail": a string for our own errors, a list for invalid input.
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') {
      return body.detail;
    }
  } catch {
    // Not JSON, e.g. a proxy error page.
  }
  return `Something went wrong on the server (${response.status}). Please try again.`;
}
