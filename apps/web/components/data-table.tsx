"use client";

import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";

export function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  const columns = Object.keys(rows[0] || {}).map((key) => ({
    accessorKey: key,
    header: key,
    cell: (info: any) => String(info.getValue() ?? "")
  }));
  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });

  if (!rows.length) {
    return <div className="rounded-md border border-dashed border-slate-300 p-6 text-sm text-slate-500">暂无数据</div>;
  }

  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="whitespace-nowrap border-b border-slate-200 px-3 py-2 font-semibold">
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="odd:bg-white even:bg-slate-50/60">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="max-w-[240px] truncate border-b border-slate-100 px-3 py-2">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
