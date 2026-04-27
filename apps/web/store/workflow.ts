"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { GenerateConfig, ReportResult, StandardField, UploadResult } from "@/lib/api";

type WorkflowState = {
  upload?: UploadResult;
  mapping: Record<string, StandardField>;
  config: GenerateConfig;
  report?: ReportResult;
  setUpload: (upload: UploadResult) => void;
  setMappingField: (column: string, field: StandardField) => void;
  setConfig: (config: Partial<GenerateConfig>) => void;
  setReport: (report: ReportResult) => void;
};

export const sheetOptions = [
  ["cleaned", "原始清洗表"],
  ["income", "收入明细表"],
  ["expense", "支出明细表"],
  ["monthly", "月度汇总表"],
  ["department", "部门汇总表"],
  ["customer", "客户汇总表"],
  ["supplier", "供应商汇总表"],
  ["customer_concentration", "客户集中度表"],
  ["expense_structure", "费用结构表"],
  ["department_performance", "部门经营分析表"],
  ["project_profitability", "项目盈利测算表"],
  ["customer_risk", "客户回款风险表"],
  ["working_capital", "营运资金关注表"],
  ["anomalies", "异常数据表"],
  ["summary", "管理摘要表"],
  ["bp_insights", "财务BP洞察表"]
] as const;

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set) => ({
      mapping: {},
      config: {
        sheets: sheetOptions.map(([key]) => key),
        enable_anomaly_check: true,
        enable_formulas: true,
        enable_summary: true,
        enable_ai_enhance: true,
        ai_model: "",
        export_version: "finance"
      },
      setUpload: (upload) => set({ upload, mapping: upload.suggested_mapping }),
      setMappingField: (column, field) => set((state) => ({ mapping: { ...state.mapping, [column]: field } })),
      setConfig: (config) => set((state) => ({ config: { ...state.config, ...config } })),
      setReport: (report) => set({ report })
    }),
    { name: "finance-splitter-workflow" }
  )
);
