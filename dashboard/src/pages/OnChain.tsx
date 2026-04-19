import { useQuery } from "@tanstack/react-query";
import { fetchOnChain } from "../api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function OnChain() {
  const { data: btc } = useQuery({ queryKey: ["onchain", "BTC"], queryFn: () => fetchOnChain("BTC"), refetchInterval: 60_000 });
  const { data: eth } = useQuery({ queryKey: ["onchain", "ETH"], queryFn: () => fetchOnChain("ETH"), refetchInterval: 60_000 });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">On-Chain Metrics</h1>
      {[{ sym: "BTC", data: btc }, { sym: "ETH", data: eth }].map(({ sym, data }) => (
        <div key={sym} className="rounded-xl bg-gray-800 border border-gray-700 p-5">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">{sym} — CoinMetrics Community</h2>
          {!data || data.metrics.length === 0 ? (
            <p className="text-gray-500 text-sm">No on-chain data yet — start the scheduler.</p>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
                {[...new Map(data.metrics.map((m) => [m.metric_name, m])).values()].slice(0, 6).map((m) => (
                  <div key={m.metric_name} className="rounded-lg bg-gray-700/50 p-3">
                    <p className="text-xs text-gray-400 mb-1">{m.metric_name}</p>
                    <p className="text-white font-mono text-sm">{m.metric_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={data.metrics.slice(-14).map((m) => ({ date: new Date(m.timestamp).toLocaleDateString(), [m.metric_name]: m.metric_value }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#6b7280" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }} />
                  <Bar dataKey="ActiveAddresses" fill="#60a5fa" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
