import { useQuery } from "@tanstack/react-query";
import { fetchCollectorStatus, fetchDbStatus, fetchSystemStatus } from "../api";

export default function Settings() {
  const { data: sys }        = useQuery({ queryKey: ["sys"],      queryFn: fetchSystemStatus,    refetchInterval: 10_000 });
  const { data: db }         = useQuery({ queryKey: ["db"],       queryFn: fetchDbStatus,        refetchInterval: 15_000 });
  const { data: collectors } = useQuery({ queryKey: ["col-stat"], queryFn: fetchCollectorStatus, refetchInterval: 15_000 });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Status &amp; Settings</h1>

      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">System</h2>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          {[
            { label: "Version",  value: sys?.version },
            { label: "Uptime",   value: sys?.uptime_human },
            { label: "PID",      value: sys?.pid?.toString() },
            { label: "UTC Now",  value: sys?.utc_now ? new Date(sys.utc_now).toLocaleTimeString() : undefined },
          ].map(({ label, value }) => (
            <div key={label}>
              <dt className="text-xs text-gray-400 uppercase tracking-wider mb-0.5">{label}</dt>
              <dd className="text-white font-mono">{value ?? "—"}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Database</h2>
        <dl className="grid grid-cols-3 gap-4 text-sm">
          {[
            { label: "Backend",   value: db?.backend },
            { label: "Connected", value: db?.connected == null ? "—" : db.connected ? "Yes" : "No" },
            { label: "Size",      value: db?.size_mb != null ? `${db.size_mb} MB` : "—" },
          ].map(({ label, value }) => (
            <div key={label}>
              <dt className="text-xs text-gray-400 uppercase tracking-wider mb-0.5">{label}</dt>
              <dd className="text-white font-mono">{value ?? "—"}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Collectors</h2>
        {!collectors || collectors.collectors.length === 0 ? (
          <p className="text-gray-500 text-sm">No collector records yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-400 border-b border-gray-700">
              <th className="pb-2">Name</th><th className="pb-2">Status</th>
              <th className="pb-2">Last Run</th><th className="pb-2 text-right">Errors</th>
              <th className="pb-2">Last Error</th>
            </tr></thead>
            <tbody className="divide-y divide-gray-700/50">
              {collectors.collectors.map((c) => (
                <tr key={c.name} className="text-gray-300">
                  <td className="py-2 font-mono text-white">{c.name}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.status === "ok" ? "bg-green-900 text-green-300" : "bg-yellow-900 text-yellow-300"}`}>{c.status}</span>
                  </td>
                  <td className="py-2 text-xs text-gray-400">{c.last_run ? new Date(c.last_run).toLocaleString() : "—"}</td>
                  <td className="py-2 text-right text-red-400">{c.error_count}</td>
                  <td className="py-2 text-xs text-gray-500 max-w-xs truncate">{c.last_error ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
