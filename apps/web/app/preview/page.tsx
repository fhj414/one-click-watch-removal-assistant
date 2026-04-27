"use client";

import Link from "next/link";
import { useState } from "react";
import { Download } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { downloadReport } from "@/lib/api";
import { formatMoney } from "@/lib/utils";
import { useWorkflowStore } from "@/store/workflow";

export default function PreviewPage() {
  const report = useWorkflowStore((state) => state.report);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!report?.download_request) return;
    setDownloading(true);
    try {
      await downloadReport(report.download_request);
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

          <Card>
            <CardHeader>
              <h2 className="font-semibold">老板摘要</h2>
            </CardHeader>
            <CardContent>
              <p className="leading-7 text-slate-700">{report.boss_summary}</p>
              <p className="mt-3 text-xs text-slate-500">
                {report.ai_enabled ? `AI 增强已启用${report.ai_model ? ` · ${report.ai_model}` : ""}` : "当前为规则引擎摘要"}
              </p>
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
