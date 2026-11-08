import { useEffect, useState } from 'react';

import { ApiError, getStory, isFinished, type Story } from '@/api';

const POLL_INTERVAL_MS = 2000;

// Fetches the story every couple of seconds until it is done or failed.
export function useStory(jobId: string) {
  const [story, setStory] = useState<Story | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionProblem, setConnectionProblem] = useState(false);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const latest = await getStory(jobId);
        if (stopped) return;
        setStory(latest);
        setConnectionProblem(false);
        if (isFinished(latest.status)) return;
      } catch (caught) {
        if (stopped) return;
        // 4xx (e.g. an unknown story) won't change by asking again; network and 5xx errors might.
        if (caught instanceof ApiError && caught.status >= 400 && caught.status < 500) {
          setError(caught.message);
          return;
        }
        console.warn('Polling the story failed, retrying', caught);
        setConnectionProblem(true);
      }
      timer = setTimeout(poll, POLL_INTERVAL_MS);
    }

    poll();
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [jobId]);

  return { story, error, connectionProblem };
}
