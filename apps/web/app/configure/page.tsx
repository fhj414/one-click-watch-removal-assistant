"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Play } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { generateReport } from "@/lib/api";
import { sheetOptions, useWorkflowStore } from "@/store/workflow";

export default function ConfigurePage() {
  const router = useRouter();
  const { upload, mapping, config, setConfig, setReport } = useWorkflowStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const toggleSheet = (key: string) => {
    const sheets = config.sheets.includes(key) ? config.sheets.filter((item) => item !== key) : [...config.sheets, key];
    setConfig({ sheets });
  };

  const handleGenerate = async () => {
    if (!upload) return;
    setLoading(true);
    setError("");
    try {
      const report = await generateReport(upload, mapping, config);
      setReport(report);
      router.push("/preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">生成配置页</h1>
        <p className="mt-2 text-sm text-slate-600">选择要生成的表、检查规则和导出版本。</p>
      </div>

      {!upload ? (
        <Card>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-slate-600">请先上传并确认字段映射。</p>
            <Link href="/">
              <Button>去上传</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <Card>
            <CardHeader>
              <h2 className="font-semibold">选择报表</h2>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {sheetOptions.map(([key, label]) => (
                <label key={key} className="flex items-center gap-3 rounded-md border border-slate-200 bg-white p-3 text-sm">
                  <input type="checkbox" checked={config.sheets.includes(key)} onChange={() => toggleSheet(key)} />
                  <span>{label}</span>
                </label>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="font-semibold">导出选项</h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={config.enable_anomaly_check}
                  onChange={(event) => setConfig({ enable_anomaly_check: event.target.checked })}
                />
                启用异常检查
              </label>
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={config.enable_formulas}
                  onChange={(event) => setConfig({ enable_formulas: event.target.checked })}
                />
                启用自动公式
              </label>
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={config.enable_summary}
                  onChange={(event) => setConfig({ enable_summary: event.target.checked })}
                />
                启用摘要分析
              </label>
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={config.enable_ai_enhance}
                  onChange={(event) => setConfig({ enable_ai_enhance: event.target.checked })}
                />
                启用 OpenRouter 智能增强
              </label>
              <div>
                <p className="mb-2 text-sm font-medium">AI 模型（可选覆盖）</p>
                <Select value={config.ai_model || ""} onChange={(event) => setConfig({ ai_model: event.target.value })}>
                  <option value="">默认模型</option>
                  <option value="qwen/qwen3-30b-a3b">Qwen3 30B A3B</option>
                  <option value="deepseek/deepseek-chat-v3-0324">DeepSeek V3 0324</option>
                  <option value="google/gemini-2.5-flash">Gemini 2.5 Flash</option>
                  <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B Instruct</option>
                  <option value="anthropic/claude-3.5-haiku">Claude 3.5 Haiku</option>
                </Select>
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  推荐用于财务 BP：默认用更快的高性价比模型，AI 会补充经营结论、风险提示、动作建议和洞察 sheet。
                </p>
              </div>
              <div>
                <p className="mb-2 text-sm font-medium">导出版本</p>
                <Select value={config.export_version} onChange={(event) => setConfig({ export_version: event.target.value as any })}>
                  <option value="finance">财务版</option>
                  <option value="boss">老板版</option>
                  <option value="operations">运营版</option>
                </Select>
              </div>
              <Button onClick={handleGenerate} disabled={loading} className="w-full">
                <Play size={16} />
                {loading ? "正在生成..." : "生成报表"}
              </Button>
              {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
