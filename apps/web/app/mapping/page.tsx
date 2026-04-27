"use client";

import Link from "next/link";
import { useState } from "react";
import { Save } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { saveTemplate, type StandardField } from "@/lib/api";
import { useWorkflowStore } from "@/store/workflow";

const fields: { value: StandardField; label: string }[] = [
  { value: "date", label: "日期" },
  { value: "amount", label: "金额" },
  { value: "direction", label: "收入支出" },
  { value: "department", label: "部门" },
  { value: "project", label: "项目" },
  { value: "customer", label: "客户" },
  { value: "supplier", label: "供应商" },
  { value: "order_no", label: "订单号/流水号" },
  { value: "payment_method", label: "付款方式" },
  { value: "invoice_status", label: "发票状态" },
  { value: "remark", label: "备注" },
  { value: "ignore", label: "忽略" }
];

export default function MappingPage() {
  const { upload, mapping, setMappingField } = useWorkflowStore();
  const [templateName, setTemplateName] = useState("默认财务流水模板");
  const [message, setMessage] = useState("");

  const handleSave = async () => {
    if (!upload) return;
    await saveTemplate(templateName, mapping, upload.columns);
    setMessage("模板已保存，下次可复用。");
  };

  return (
    <AppShell>
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">字段识别页</h1>
          <p className="mt-2 text-sm text-slate-600">左侧是上传文件列名，右侧是系统自动识别结果，可手动调整。</p>
        </div>
        <Link href="/configure">
          <Button disabled={!upload}>下一步：生成配置</Button>
        </Link>
      </div>

      {!upload ? (
        <Card>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-slate-600">还没有上传文件，请先回到首页上传。</p>
            <Link href="/">
              <Button>去上传</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <Card>
            <CardHeader>
              <h2 className="font-semibold">{upload.filename}</h2>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {upload.columns.map((column) => (
                  <div key={column} className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_260px] md:items-center">
                    <div>
                      <p className="font-medium">{column}</p>
                      <p className="mt-1 truncate text-xs text-slate-500">
                        样例：{upload.sample_rows.slice(0, 3).map((row) => String(row[column] ?? "")).join(" / ")}
                      </p>
                    </div>
                    <Select value={mapping[column] || "ignore"} onChange={(event) => setMappingField(column, event.target.value as StandardField)}>
                      {fields.map((field) => (
                        <option key={field.value} value={field.value}>
                          {field.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="font-semibold">保存模板</h2>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input value={templateName} onChange={(event) => setTemplateName(event.target.value)} />
              <Button variant="secondary" onClick={handleSave} className="w-full">
                <Save size={16} />
                保存当前映射
              </Button>
              {message && <p className="rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-700">{message}</p>}
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
