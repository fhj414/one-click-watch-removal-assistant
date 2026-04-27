import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "财务数据一键拆表助手",
  description: "上传原始财务数据，一键生成多个 Excel 报表"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
