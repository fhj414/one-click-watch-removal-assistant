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
  storage_key?: string | null;
  source_url?: string | null;
};

type UploadInitResponse = {
  storage_mode: "local" | "r2";
  upload_url?: string | null;
  object_key?: string | null;
  expires_in?: number | null;
  storage_error?: string | null;
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
  report_plan?: {
    data_type?: string;
    data_type_label?: string;
    recommended_sheets?: string[];
    bp_focus?: string[];
    missing_fields?: string[];
    reasons?: string[];
    row_count?: number;
    income_count?: number;
    expense_count?: number;
    anomaly_count?: number;
  } | null;
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
        const detail = await uploadResponse.text();
        throw new Error(detail || "上传到对象存储失败");
      }
      const completeResponse = await fetch(`${API_BASE}/api/uploads/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          object_key: initPayload.object_key,
          filename: file.name,
          content_type: file.type || "application/octet-stream",
          ...(await buildClientSample(file))
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

export async function generateReport(upload: string | UploadResult, mapping: Record<string, StandardField>, config: GenerateConfig) {
  const uploadId = typeof upload === "string" ? upload : upload.upload_id;
  const storageKey = typeof upload === "string" ? null : upload.storage_key;
  const sourceUrl = typeof upload === "string" || storageKey ? null : upload.source_url;
  const sourceFilename = typeof upload === "string" ? null : upload.filename;
  const response = await fetch(`${API_BASE}/api/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      upload_id: uploadId,
      storage_key: storageKey,
      source_url: sourceUrl,
      source_filename: sourceFilename,
      mapping,
      config
    })
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

async function buildClientSample(file: File): Promise<{
  columns?: string[];
  sample_rows?: Record<string, string>[];
  rows_count?: number;
}> {
  if (!file.name.toLowerCase().endsWith(".csv")) return {};
  const text = await file.text();
  const rows = parseCsvSample(text, 50);
  if (!rows.length) return {};
  const columns = rows[0].map((column) => column.trim());
  if (!columns.length) return {};
  const sampleRows = rows.slice(1, 21).map((row) =>
    Object.fromEntries(columns.map((column, index) => [column || `列${index + 1}`, row[index] ?? ""]))
  );
  const rowCount = Math.max(rows.length - 1, sampleRows.length);
  return { columns: columns.map((column, index) => column || `列${index + 1}`), sample_rows: sampleRows, rows_count: rowCount };
}

function parseCsvSample(text: string, maxRows: number): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;
  for (let index = 0; index < text.length && rows.length < maxRows; index += 1) {
    const char = text[index];
    const nextChar = text[index + 1];
    if (char === '"' && inQuotes && nextChar === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && nextChar === "\n") index += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }
  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }
  return rows.filter((item) => item.some((cellValue) => cellValue.trim() !== ""));
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
