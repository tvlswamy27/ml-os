export interface ExecutionEvent {
  run_id: string;
  event_type: string;
  stage: string;
  timestamp: string;
  payload: Record<string, any>;
}
