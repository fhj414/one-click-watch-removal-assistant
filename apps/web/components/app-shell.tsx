import Link from "next/link";
import { FileSpreadsheet } from "lucide-react";

const nav = [
  ["首页", "/"],
  ["字段识别", "/mapping"],
  ["生成配置", "/configure"],
  ["结果预览", "/preview"],
  ["历史记录", "/history"]
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-blue-700 text-white">
              <FileSpreadsheet size={22} />
            </span>
            <span>
              <span className="block text-base font-semibold">财务数据一键拆表助手</span>
              <span className="block text-xs text-slate-500">Finance Excel Splitter</span>
            </span>
          </Link>
          <nav className="flex flex-wrap gap-2">
            {nav.map(([label, href]) => (
              <Link key={href} href={href} className="rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100">
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-4 py-8">{children}</div>
    </main>
  );
}
