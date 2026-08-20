const BASE_URL = 'http://localhost:8000';

export interface ExecutionEvent {
  run_id: string;
  event_type: string;
  stage: string;
  timestamp: string;
  payload: Record<string, any>;
}

export const eventService = {
  subscribeToRunEvents: (
    projectId: number,
    runId: string,
    onMessage: (event: ExecutionEvent) => void,
    onError: (errorMsg: string) => void
  ): (() => void) => {
    const url = `${BASE_URL}/api/projects/${projectId}/run/events/${runId}`;
    const eventSource = new EventSource(url, { withCredentials: true });

    const handleEvent = (event: MessageEvent) => {
      try {
        const parsed: ExecutionEvent = JSON.parse(event.data);
        onMessage(parsed);
      } catch {
        // Skip parsing errors for hearbeats or non-JSON payloads
      }
    };

    // Supported canonical lifecycle event types published by MLOSEngine
    const eventTypes = [
      'ExecutionStarted',
      'StageStarted',
      'StageCompleted',
      'ExecutionCompleted',
      'ExecutionFailed',
      'NodeStarted',
      'NodeCompleted',
      'NodeFailed'
    ];

    // Explicitly register listeners on EventSource to catch custom event namespaces
    eventTypes.forEach((type) => {
      eventSource.addEventListener(type, handleEvent as any);
    });

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        onMessage(parsed);
      } catch {
        // Skip
      }
    };

    eventSource.onerror = () => {
      // Stop and report error on connection drop or server failure
      onError('Connection to execution stream lost.');
    };

    // Return the clean unsubscribe callback
    return () => {
      eventTypes.forEach((type) => {
        eventSource.removeEventListener(type, handleEvent as any);
      });
      eventSource.close();
    };
  },
};
