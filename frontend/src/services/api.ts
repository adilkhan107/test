export const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";

export type Status = "queued" | "processing" | "completed" | "failed";
export type Risk = "low" | "medium" | "high" | "critical" | "unknown";

export interface AnalysisSummary {
  id: number;
  original_filename: string;
  status: Status;
  progress: number;
  error: string | null;
  duration_seconds: number | null;
  ppe_compliance: number | null;
  risk_score: number | null;
  risk_level: Risk | null;
  peak_people: number;
  created_at: string;
  completed_at: string | null;
}
export interface Incident {
  id: number;
  type: "no_hardhat" | "no_vest" | "no_mask";
  timestamp_seconds: number;
  count: number;
  people_in_frame: number;
}
export interface Snapshot {
  url: string;
  timestamp_seconds: number;
  violations: number;
}
export interface AnalysisDetail extends AnalysisSummary {
  frames_sampled: number;
  frames_with_people: number;
  avg_people: number;
  detections: Record<string, number>;
  snapshots: Snapshot[];
  incidents: Incident[];
}
export interface Dashboard {
  total_analyses: number;
  completed: number;
  failed: number;
  in_progress: number;
  avg_compliance: number | null;
  total_incidents: number;
  risk_distribution: Record<string, number>;
  incidents_by_type: Record<string, number>;
  trend: { id: number; label: string; compliance: number; risk_score: number | null }[];
  recent: AnalysisSummary[];
}
export interface RiskReport {
  risk_score: number;
  risk_level: Risk;
  factors: string[];
  recommendations: string[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new Error(`Cannot reach the server at ${API_URL}. Check that the backend is running.`);
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
    } catch { /* keep default */ }
    throw new Error(msg);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  upload(video: File) {
    const form = new FormData();
    form.append("video", video);
    return request<{ id: number }>("/api/vision/analyze", { method: "POST", body: form });
  },
  list(limit = 50, offset = 0) {
    return request<{ total: number; items: AnalysisSummary[] }>(`/api/vision/analyses?limit=${limit}&offset=${offset}`);
  },
  get: (id: number) => request<AnalysisDetail>(`/api/vision/analyses/${id}`),
  remove: (id: number) => request<void>(`/api/vision/analyses/${id}`, { method: "DELETE" }),
  risk: (id: number) => request<RiskReport>(`/api/risk/${id}`),
  dashboard: () => request<Dashboard>("/api/dashboard/summary"),
};
