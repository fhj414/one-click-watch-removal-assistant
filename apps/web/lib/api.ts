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
  storage_mode?: string;
};

type UploadInitResponse = {
  storage_mode: "local" | "r2";
  upload_url?: string | null;
  object_key?: string | null;
  expires_in?: number | null;
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
  download_request?: Record<string, unknown> | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function fileUrl(path: string) {
  return `${API_BASE}${path}`;
}

export async function uploadFile(file: File): Promise<UploadResult> {
  const initResponse = await fetch(`${API_BASE}/api/uploads/init`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, content_type: file.type || "application/octet-stream" })
  });
  if (initResponse.ok) {
    const initPayload = (await initResponse.json()) as UploadInitResponse;
    if (initPayload.storage_mode === "r2" && initPayload.upload_url && initPayload.object_key) {
      const uploadResponse = await fetch(initPayload.upload_url, {
        method: "PUT",
        headers: { "Content-Type": file.type || "application/octet-stream" },
        body: file
      });
      if (!uploadResponse.ok) {
        throw new Error("上传到对象存储失败");
      }
      const completeResponse = await fetch(`${API_BASE}/api/uploads/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          object_key: initPayload.object_key,
          filename: file.name,
          content_type: file.type || "application/octet-stream"
        })
      });
      return handleResponse(completeResponse);
    }
  }

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

export async function downloadReport(downloadRequest: Record<string, unknown>) {
  const response = await fetch(`${API_BASE}/api/reports/download-direct`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(downloadRequest)
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  const blob = await response.blob();
  downloadBlob(blob, extractFilename(response.headers.get("Content-Disposition")), "财务数据一键拆表结果.xlsx");
}

export async function downloadReportFromFile(
  file: File,
  mapping: Record<string, StandardField>,
  config: GenerateConfig
) {
  const form = new FormData();
  form.append("file", file);
  form.append("mapping_json", JSON.stringify(mapping));
  form.append("config_json", JSON.stringify(config));
  const response = await fetch(`${API_BASE}/api/reports/download-from-file`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  const blob = await response.blob();
  downloadBlob(blob, extractFilename(response.headers.get("Content-Disposition")), "财务数据一键拆表结果.xlsx");
}

export function downloadFromUrl(url: string, filename?: string) {
  const link = document.createElement("a");
  link.href = url;
  if (filename) link.download = filename;
  link.target = "_blank";
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  link.remove();
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

function extractFilename(contentDisposition: string | null): string | null {
  if (!contentDisposition) return null;
  const utf8Match = contentDisposition.match(/filename\*\=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }
  const basicMatch = contentDisposition.match(/filename=\"?([^"]+)\"?/i);
  return basicMatch?.[1] || null;
}

function downloadBlob(blob: Blob, filename: string | null, fallbackName: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename || fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
