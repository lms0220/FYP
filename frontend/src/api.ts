const API_BASE = "http://localhost:5000";

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.message || data.error || "API request failed");
  }

  return data;
}

export interface AnalysisResult {
  result_id: string;
  submission_id: string;
  classification: string;
  confidence_score: number;
  created_at: string;
}

export interface HistoryItem extends AnalysisResult {
  type: "sms" | "url";
  content: string;
  status: string;
}

export interface PredictionResult {
  type: "sms" | "url";
  prediction: string;
  score: number;
  flags: string[];
  message: string;
}

export function predictText(text: string) {
  return apiRequest<PredictionResult>("/predict", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function getDashboardResults() {
  return apiRequest<AnalysisResult[]>("/api/dashboard");
}

export function getHistory() {
  return apiRequest<HistoryItem[]>("/api/history");
}

export async function logout() {
  return fetch("http://localhost:5000/logout", {
    method: "GET",
    credentials: "include",
  });
}

export async function deleteHistory(result_ids:string[]) {

  const response = await fetch(
    "http://localhost:5000/history/delete",
    {
      method:"POST",
      credentials:"include",
      headers:{
        "Content-Type":"application/json",
      },
      body:JSON.stringify({
        result_ids
      })
    }
  );


  if(!response.ok){
    throw new Error("Delete failed");
  }


  return response.json();

}