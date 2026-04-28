"use client";

import Link from "next/link";
import { useState } from "react";
import { Download } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { downloadFromUrl, downloadReport, downloadReportFromFile } from "@/lib/api";
import { formatMoney } from "@/lib/utils";
import { useWorkflowStore } from "@/store/workflow";

export default function PreviewPage() {
  const report = useWorkflowStore((state) => state.report);
  const upload = useWorkflowStore((state) => state.upload);
  const sourceFile = useWorkflowStore((state) => state.sourceFile);
  const mapping = useWorkflowStore((state) => state.mapping);
  const config = useWorkflowStore((state) => state.config);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!report) return;
    setDownloading(true);
    try {
      if (report.download_url?.startsWith("http")) {
        downloadFromUrl(report.download_url);
      } else if (sourceFile) {
        await downloadReportFromFile(sourceFile, mapping, config);
      } else if (report.download_request) {
        await downloadReport({
          ...report.download_request,
          upload_id: upload?.source_url ? null : report.download_request.upload_id,
          source_url: report.download_request.source_url || upload?.source_url,
          source_filename: report.download_request.source_filename || upload?.filename
        });
      } else {
        throw new Error("原始文件已丢失，请重新上传后再下载。");
      }
    } finally {
      setDownloading(false);
    }
  };

  return (
    <AppShell>
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">结果预览页</h1>
          <p className="mt-2 text-sm text-slate-600">预览每张表前 20 行，确认后下载完整 xlsx。</p>
        </div>
        {report && (
          <Button onClick={handleDownload} disabled={downloading || !report.download_request}>
            <Download size={16} />
            {downloading ? "正在生成下载文件..." : "下载完整 Excel"}
          </Button>
        )}
      </div>

      {!report ? (
        <Card>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-slate-600">还没有生成结果，请先完成生成配置。</p>
            <Link href="/configure">
              <Button>去生成</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          <section className="grid gap-4 md:grid-cols-4">
            <Metric title="总收入" value={formatMoney(report.metrics.total_income)} />
            <Metric title="总支出" value={formatMoney(report.metrics.total_expense)} />
            <Metric title="净额" value={formatMoney(report.metrics.net_amount)} />
            <Metric title="异常记录" value={`${report.metrics.anomaly_count || 0} 条`} />
          </section>

          {report.report_plan && (
            <Card>
              <CardHeader>
                <h2 className="font-semibold">动态报表规划</h2>
              </CardHeader>
              <CardContent className="grid gap-4 lg:grid-cols-[1fr_1fr]">
                <div>
                  <p className="text-sm text-slate-500">识别类型</p>
                  <p className="mt-1 text-lg font-semibold text-slate-900">{report.report_plan.data_type_label || "通用财务台账分析"}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    {(report.report_plan.reasons || []).join(" ")}
                  </p>
                </div>
                <div className="space-y-3">
                  <TagGroup title="BP 关注点" items={report.report_plan.bp_focus || []} />
                  <TagGroup title="推荐输出" items={(report.report_plan.recommended_sheets || []).slice(0, 8)} />
                  {!!report.report_plan.missing_fields?.length && <TagGroup title="建议补充字段" items={report.report_plan.missing_fields} muted />}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <h2 className="font-semibold">老板摘要</h2>
            </CardHeader>
            <CardContent>
              <p className="leading-7 text-slate-700">{report.boss_summary}</p>
              <p className="mt-3 text-xs text-slate-500">
                {report.ai_enabled ? `AI 增强已启用${report.ai_model ? ` · ${report.ai_model}` : ""}` : "当前为规则引擎摘要"}
              </p>
              {report.download_url?.startsWith("http") ? (
                <p className="mt-2 text-xs text-emerald-600">当前结果已写入对象存储，下载会优先走直链。</p>
              ) : (
                !sourceFile && <p className="mt-2 text-xs text-amber-600">当前会话未保留原始文件，下载失败时请重新上传并生成。</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="font-semibold">异常统计</h2>
            </CardHeader>
            <CardContent className="grid gap-2 md:grid-cols-3">
              {Object.entries(report.anomaly_summary).map(([key, value]) => (
                <div key={key} className="rounded-md bg-slate-50 px-3 py-2 text-sm">
                  <span className="text-slate-500">{key}</span>
                  <span className="float-right font-semibold">{value}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {Object.entries(report.preview).map(([sheetName, rows]) => (
            <Card key={sheetName}>
              <CardHeader>
                <h2 className="font-semibold">{sheetName}</h2>
              </CardHeader>
              <CardContent>
                <DataTable rows={rows} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <p className="text-sm text-slate-500">{title}</p>
        <p className="mt-2 text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}

function TagGroup({ title, items, muted = false }: { title: string; items: string[]; muted?: boolean }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-slate-500">{title}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className={`rounded-md px-2 py-1 text-xs ${muted ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-700"}`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
