"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { fileUrl, getHistory } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

type HistoryState = {
  uploads: any[];
  reports: any[];
};

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryState>({ uploads: [], reports: [] });

  useEffect(() => {
    getHistory().then(setHistory).catch(() => setHistory({ uploads: [], reports: [] }));
  }, []);

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">处理历史记录</h1>
        <p className="mt-2 text-sm text-slate-600">查看最近上传文件和生成结果。</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="font-semibold">最近上传</h2>
          </CardHeader>
          <CardContent className="space-y-3">
            {history.uploads.length === 0 && <p className="text-sm text-slate-500">暂无上传记录</p>}
            {history.uploads.map((item) => (
              <div key={item.id} className="rounded-md border border-slate-200 p-3">
                <p className="font-medium">{item.original_name}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {item.rows_count} 行 · {item.columns?.length || 0} 列 · {item.created_at}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="font-semibold">最近报表</h2>
          </CardHeader>
          <CardContent className="space-y-3">
            {history.reports.length === 0 && <p className="text-sm text-slate-500">暂无报表记录</p>}
            {history.reports.map((item) => (
              <div key={item.id} className="flex flex-col gap-3 rounded-md border border-slate-200 p-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-medium">{item.source_filename}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    净额 {Number(item.metrics?.net_amount || 0).toLocaleString("zh-CN")} · 异常 {item.metrics?.anomaly_count || 0} 条
                  </p>
                </div>
                <a href={fileUrl(item.download_url)}>
                  <Button variant="secondary">
                    <Download size={16} />
                    下载
                  </Button>
                </a>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
