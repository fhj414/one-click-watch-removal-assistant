"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { ArrowRight, Download, FileUp, History, Layers, WandSparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { fileUrl, uploadFile } from "@/lib/api";
import { useWorkflowStore } from "@/store/workflow";

const highlights = [
  ["字段自动识别", "金额、日期、客户、供应商、订单号等字段别名自动归一。"],
  ["多表一键生成", "一次导出清洗表、明细表、汇总表、异常表和管理摘要。"],
  ["财务可用格式", "冻结首行、筛选、千分位、公式、条件格式全部写入 Excel。"]
];

export default function HomePage() {
  const router = useRouter();
  const setUpload = useWorkflowStore((state) => state.setUpload);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onDrop = async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setError("");
    setLoading(true);
    try {
      const result = await uploadFile(file);
      setUpload(result, file);
      router.push("/mapping");
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"]
    }
  });

  return (
    <AppShell>
      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="flex flex-col justify-center gap-6 py-4">
          <div className="max-w-3xl">
            <p className="mb-3 text-sm font-medium text-teal-700">智能 Excel 处理平台</p>
            <h1 className="text-4xl font-semibold leading-tight tracking-normal text-slate-950 md:text-5xl">
              上传原始财务数据，一键生成多个 Excel 报表
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
              把流水、报销、收入、采购等原始表丢进来，自动清洗、拆分、汇总、查异常，输出老板汇报和财务复盘都能直接使用的工作簿。
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href={fileUrl("/api/sample-file")}>
              <Button variant="secondary">
                <Download size={16} />
                示例文件下载
              </Button>
            </a>
            <Link href="/history">
              <Button variant="ghost">
                <History size={16} />
                处理历史
              </Button>
            </Link>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <FileUp className="text-blue-700" />
              <div>
                <h2 className="font-semibold">上传原始文件</h2>
                <p className="text-sm text-slate-500">支持 xlsx、xls、csv</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`flex min-h-[260px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition ${
                isDragActive ? "border-blue-600 bg-blue-50" : "border-slate-300 bg-slate-50"
              }`}
            >
              <input {...getInputProps()} />
              <WandSparkles className="mb-4 text-blue-700" size={42} />
              <p className="text-lg font-semibold">{loading ? "正在上传并识别字段..." : "拖拽文件到这里，或点击选择"}</p>
              <p className="mt-2 text-sm text-slate-500">上传后会进入字段识别页确认映射</p>
            </div>
            {error && <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          </CardContent>
        </Card>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {highlights.map(([title, detail]) => (
          <Card key={title}>
            <CardContent className="flex gap-4">
              <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-teal-50 text-teal-700">
                <Layers size={18} />
              </span>
              <div>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-1 text-sm leading-6 text-slate-600">{detail}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="mt-8">
        <Card>
          <CardHeader>
            <h2 className="font-semibold">最近模板记录</h2>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm text-slate-600 md:flex-row md:items-center md:justify-between">
            <span>模板会在字段识别页保存，下一次上传相似表格时可直接复用。</span>
            <Link href="/mapping">
              <Button variant="secondary">
                查看字段识别
                <ArrowRight size={16} />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>
    </AppShell>
  );
}
