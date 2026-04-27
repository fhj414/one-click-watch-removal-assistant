export type StandardField =
  | "date"
  | "amount"
  | "direction"
  | "department"
  | "project"
  | "customer"
  | "supplier"
  | "order_no"
  | "payment_method"
  | "invoice_status"
  | "remark"
  | "ignore";

export type UploadResult = {
  upload_id: string;
  filename: string;
  columns: string[];
  sample_rows: Record<string, unknown>[];
  suggested_mapping: Record<string, StandardField>;
};

export type GenerateConfig = {
  sheets: string[];
  enable_anomaly_check: boolean;
  enable_formulas: boolean;
  enable_summary: boolean;
  enable_ai_enhance: boolean;
  ai_model?: string | null;
  export_version: "finance" | "boss" | "operations";
};

export type ReportResult = {
  report_id: string;
  status: string;
  metrics: Record<string, number>;
  anomaly_summary: Record<string, number>;
  preview: Record<string, Record<string, unknown>[]>;
  download_url: string;
  boss_summary: string;
  ai_enabled: boolean;
  ai_model?: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function fileUrl(path: string) {
  return `${API_BASE}${path}`;
}

export async function uploadFile(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/api/uploads`, { method: "POST", body: form });
  return handleResponse(response);
}

export async function saveTemplate(name: string, mapping: Record<string, StandardField>, sourceColumns: string[]) {
  const response = await fetch(`${API_BASE}/api/templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, mapping, source_columns: sourceColumns })
  });
  return handleResponse(response);
}

export async function listTemplates() {
  const response = await fetch(`${API_BASE}/api/templates`, { cache: "no-store" });
  return handleResponse(response);
}

export async function generateReport(uploadId: string, mapping: Record<string, StandardField>, config: GenerateConfig) {
  const response = await fetch(`${API_BASE}/api/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId, mapping, config })
  });
  return handleResponse<ReportResult>(response);
}

export async function getHistory() {
  const response = await fetch(`${API_BASE}/api/history`, { cache: "no-store" });
  return handleResponse(response);
}

async function handleResponse<T = any>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}
