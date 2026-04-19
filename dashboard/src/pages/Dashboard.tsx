import { useQuery } from "@tanstack/react-query";
import { fetchOverview, fetchCollectorHealth } from "../api";

const fmt = (n: number | null, dec = 2, pre = "") =>
  n == null ? "—" : `${pre}${n.toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec })}`;

const fgColor = (v: number | null) => {
  if (v == null) return "text-gray-400";
  if (v <= 25) return "text-red-500";
  if (v <= 45) return "text-orange-400";
  if (v <= 55) return "text-yellow-400";
  if (v <= 75) return "text-green-400";
  return "text-emerald-400";
};

export default function Dashboard() {
  const { data: ov, isLoading, error } = useQuery({
    queryKey: ["overview"], queryFn: fetchOverview, refetchInterval: 15_000,
  });
  const { data: health } = useQuery({
    queryKey: ["collector-health"], queryFn: fetchCollectorHealth, refetchInterval: 30_000,
  });
  const change = ov?.btc_change_24h ?? null;
  const chColor = change == null ? "" : change >= 0 ? "text-green-400" : "text-red-400";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Dashboard</h1>
      {error && (
        <div className="rounded-lg bg-red-900/40 border border-red-700 px-4 py-3 text-red-300 text-sm">
          API unreachable — start with <code className="font-mono">python -m src api</code>
        </div>
      )}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="BTC Price" loading={isLoading}>
          <span className="text-2xl font-bold text-white">{fmt(ov?.btc_price ?? null, 0, "$")}</span>
          {change != null && (
            <span className={`text-sm font-medium ${chColor}`}>
              {change >= 0 ? "▲" : "▼"} {Math.abs(change).toFixed(2)}%
            </span>
          )}
        </KpiCard>
        <KpiCard label="Fear & Greed" loading={isLoading}>
          <span className={`text-2xl font-bold ${fgColor(ov?.fear_greed_value ?? null)}`}>
            {ov?.fear_greed_value ?? "—"}
          </span>
          <span className="text-xs text-gray-400 capitalize">{ov?.fear_greed_classification ?? ""}</span>
        </KpiCard>
        <KpiCard label="Signals (24 h)" loading={isLoading}>
          <span className="text-2xl font-bold text-white">{ov?.signals_last_24h ?? "—"}</span>
        </KpiCard>
        <KpiCard label="Last Update" loading={isLoading}>
          <span className="text-sm text-gray-300">
            {ov?.updated_at ? new Date(ov.updated_at).toLocaleTimeString() : "—"}
          </span>
        </KpiCard>
      </div>
      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Collector Status</h2>
        {!health ? <p className="text-gray-500 text-sm">Loading…</p>
          : health.collectors.length === 0 ? (
            <p className="text-gray-500 text-sm">
              No data yet — run <code className="text-blue-400">python -m src scheduler</code>
            </p>
          ) : (
            <div className="divide-y divide-gray-700">
              {health.collectors.map((c) => (
                <div key={c.name} className="flex items-center justify-between py-2 text-sm">
                  <span className="font-mono text-gray-300">{c.name}</span>
                  <div className="flex items-center gap-3">
                    {c.last_run && <span className="text-xs text-gray-500">{new Date(c.last_run).toLocaleTimeString()}</span>}
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.status === "ok" && c.error_count === 0 ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
                      {c.status === "ok" && c.error_count === 0 ? "OK" : `ERR ×${c.error_count}`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )
        }
      </div>
    </div>
  );
}

function KpiCard({ label, loading, children }: { label: string; loading?: boolean; children: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{label}</p>
      {loading ? <div className="h-8 w-24 bg-gray-700 animate-pulse rounded" /> : <div className="flex flex-col gap-0.5">{children}</div>}
    </div>
  );
}
