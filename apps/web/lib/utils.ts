import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMoney(value: number | string | undefined) {
  const numeric = Number(value || 0);
  return numeric.toLocaleString("zh-CN", { style: "currency", currency: "CNY" });
}
