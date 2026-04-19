import { useQuery } from "@tanstack/react-query";
import { fetchActiveSignals, fetchSignalPerformance } from "../api";

const typeColor = (t: string) =>
  t === "BUY" ? "bg-green-900 text-green-300" : t === "SELL" ? "bg-red-900 text-red-300" : "bg-yellow-900 text-yellow-300";

export default function Signals() {
  const { data: perf } = useQuery({ queryKey: ["signal-perf"], queryFn: fetchSignalPerformance, refetchInterval: 30_000 });
  const { data: active, isLoading } = useQuery({ queryKey: ["signals-active"], queryFn: () => fetchActiveSignals(168), refetchInterval: 20_000 });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Trading Signals</h1>
      <div className="grid grid-cols-3 gap-4">
        {[["Total", perf?.total_signals], ["Executed", perf?.executed_signals], ["Pending", perf?.pending_signals]].map(([label, val]) => (
          <div key={label as string} className="rounded-xl bg-gray-800 border border-gray-700 p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{label}</p>
            <p className="text-2xl font-bold text-white">{val ?? "—"}</p>
          </div>
        ))}
      </div>
      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Last 7 days</h2>
        {isLoading ? (
          <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-10 bg-gray-700 animate-pulse rounded" />)}</div>
        ) : !active || active.signals.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No signals yet — POST to <code className="text-blue-400">/api/signals/</code> or start the analysis pipeline.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-400 border-b border-gray-700">
              <th className="pb-2">Time</th><th className="pb-2">Symbol</th><th className="pb-2">Type</th>
              <th className="pb-2">Strength</th><th className="pb-2">Strategy</th>
              <th className="pb-2 text-right">Target</th><th className="pb-2 text-right">Stop</th>
            </tr></thead>
            <tbody className="divide-y divide-gray-700/50">
              {active.signals.map((s) => (
                <tr key={s.id} className="text-gray-300">
                  <td className="py-2 text-xs text-gray-400">{new Date(s.timestamp).toLocaleString()}</td>
                  <td className="py-2 font-mono font-semibold text-white">{s.symbol}</td>
                  <td className="py-2"><span className={`px-2 py-0.5 rounded text-xs font-bold ${typeColor(s.signal_type)}`}>{s.signal_type}</span></td>
                  <td className="py-2">
                    <div className="flex gap-0.5">
                      {[...Array(5)].map((_, i) => <div key={i} className={`w-2 h-4 rounded-sm ${i < s.strength ? "bg-blue-500" : "bg-gray-600"}`} />)}
                    </div>
                  </td>
                  <td className="py-2 text-xs text-gray-400">{s.strategy}</td>
                  <td className="py-2 text-right text-green-400">{s.price_target ? `$${s.price_target.toLocaleString()}` : "—"}</td>
                  <td className="py-2 text-right text-red-400">{s.stop_loss ? `$${s.stop_loss.toLocaleString()}` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
