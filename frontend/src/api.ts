const API_BASE = "http://localhost:5000";


async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {

  const res = await fetch(`${API_BASE}${path}`, {

    credentials: "include",

    ...options,

    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },

  });


  const data = await res.json().catch(() => ({}));


  if (!res.ok) {

    throw new Error(
      data.message ||
      data.error ||
      "API request failed"
    );

  }


  return data as T;

}



// ============================
// Prediction Result
// ============================

export interface PredictionResult {

  type: "sms" | "url";

  prediction: string;

  score: number;

  flags: string[];

  risk_level?: "Low" | "Medium" | "High";

  risk_factors?: Array<{
    code: string;
    title: string;
    detail: string;
    points: number;
  }>;

  score_breakdown?: {
    ml_probability: number;
    ml_contribution?: number;
    rule_score: number;
    trusted_domain_adjustment: number;
    final_risk_score?: number;
  };


  llm_analysis?: {

    explanation?: string;

    threat_type?: string;

    target_organization?: string;

    risk_level?: string;

    recommendation?: string;

  };

}



// ============================
// History / Dashboard
// ============================

export interface AnalysisResult {


  result_id: string;

  submission_id: string;

  classification: string;

  confidence_score: number;

  created_at: string;

}



export interface HistoryItem {


  result_id: string;

  submission_id: string;

  type: "sms" | "url";

  content: string;

  status: string;

  classification: string;

  confidence_score: number;

  created_at: string;

}



// ============================
// Prediction API
// ============================

export function predictText(
  text:string
){

  return apiRequest<PredictionResult>(
    "/predict",
    {

      method:"POST",

      body:JSON.stringify({
        text
      }),

    }
  );

}



// ============================
// Dashboard API
// ============================

export function getDashboardResults(){

  return apiRequest<AnalysisResult[]>(
    "/api/dashboard"
  );

}



// ============================
// History API
// ============================

export function getHistory(){

  return apiRequest<HistoryItem[]>(
    "/api/history"
  );

}



// ============================
// Login / User
// ============================

export function getCurrentUser(){

  return apiRequest<{
    user_id:string
  }>("/me");

}



// ============================
// Logout
// ============================

export async function logout(){

  return apiRequest<{
    message:string
  }>(
    "/logout",
    {
      method:"GET"
    }
  );

}



// ============================
// Delete History
// ============================

export function deleteHistory(
  result_ids:string[]
){

  return apiRequest<{
    message:string
  }>(
    "/history/delete",
    {

      method:"POST",

      body:JSON.stringify({

        result_ids

      }),

    }
  );

}
