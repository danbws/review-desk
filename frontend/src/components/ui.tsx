import { Finding, Severity } from "../api";

const SEVERITY_STYLE: Record<Severity, string> = {
  critical: "bg-red-100 text-red-800 ring-red-200",
  high: "bg-orange-100 text-orange-800 ring-orange-200",
  medium: "bg-amber-100 text-amber-800 ring-amber-200",
  low: "bg-sky-100 text-sky-800 ring-sky-200",
  info: "bg-slate-100 text-slate-700 ring-slate-200",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold uppercase ring-1 ${SEVERITY_STYLE[severity]}`}
    >
      {severity}
    </span>
  );
}

export function FindingCard({ finding, dim = false }: { finding: Finding; dim?: boolean }) {
  return (
    <li
      className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${dim ? "opacity-60" : ""}`}
    >
      <div className="flex items-center gap-2">
        <SeverityBadge severity={finding.severity} />
        {finding.line != null && (
          <span className="font-mono text-xs text-slate-500">line {finding.line}</span>
        )}
      </div>
      <p className="mt-2 font-medium">{finding.title}</p>
      {finding.suggestion && <p className="mt-1 text-sm text-slate-600">{finding.suggestion}</p>}
    </li>
  );
}

export function usagePercent(used: number, limit: number): number {
  if (limit <= 0) return 100;
  return Math.min(100, Math.round((used / limit) * 100));
}

export function UsageMeter({ used, limit, plan }: { used: number; limit: number; plan: string }) {
  const pct = usagePercent(used, limit);
  const full = used >= limit;
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-medium capitalize">{plan} plan</span>
        <span className={full ? "font-semibold text-red-600" : "text-slate-600"}>
          {used} / {limit} reviews this month
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={used}
        aria-valuemax={limit}
        className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200"
      >
        <div
          className={`h-full ${full ? "bg-red-500" : "bg-indigo-600"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className.includes("p-0") ? "" : "p-5"} ${className}`}>
      {children}
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      {message}
    </div>
  );
}

export const buttonClass =
  "inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50";
export const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";
