import { useQuery } from "@tanstack/react-query";
import { fetchTickers, fetchOhlcv } from "../api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function MarketData() {
  const { data: tickers, isLoading } = useQuery({ queryKey: ["tickers"], queryFn: fetchTickers, refetchInterval: 10_000 });
  const { data: ohlcv } = useQuery({ queryKey: ["ohlcv"], queryFn: () => fetchOhlcv("BTC", "1m", 60), refetchInterval: 30_000 });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Market Data</h1>

      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">BTC/USDT — 1m</h2>
        {!ohlcv || ohlcv.candles.length === 0 ? (
          <p className="text-gray-500 text-sm">No candle data yet — start the scheduler.</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={ohlcv.candles}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t).toLocaleTimeString()} stroke="#6b7280" tick={{ fontSize: 10 }} />
              <YAxis domain={["auto", "auto"]} stroke="#6b7280" tick={{ fontSize: 10 }} width={80} tickFormatter={(v) => `$${(v as number).toLocaleString()}`} />
              <Tooltip formatter={(v: number) => [`$${v.toLocaleString()}`, "Close"]} labelFormatter={(t) => new Date(t as string).toLocaleString()} contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }} />
              <Line type="monotone" dataKey="close" stroke="#60a5fa" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="rounded-xl bg-gray-800 border border-gray-700 p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Live Tickers</h2>
        {isLoading ? (
          <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-8 bg-gray-700 animate-pulse rounded" />)}</div>
        ) : !tickers || tickers.tickers.length === 0 ? (
          <p className="text-gray-500 text-sm">No ticker data yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-400 border-b border-gray-700">
              <th className="pb-2">Symbol</th><th className="pb-2">Exchange</th>
              <th className="pb-2 text-right">Last</th><th className="pb-2 text-right">24h %</th>
            </tr></thead>
            <tbody className="divide-y divide-gray-700/50">
              {tickers.tickers.slice(0, 20).map((t, i) => (
                <tr key={i} className="text-gray-300">
                  <td className="py-2 font-mono font-semibold text-white">{t.symbol}</td>
                  <td className="py-2 text-gray-400">{t.exchange}</td>
                  <td className="py-2 text-right">{t.last ? `$${t.last.toLocaleString()}` : "—"}</td>
                  <td className={`py-2 text-right font-medium ${t.change_24h == null ? "" : t.change_24h >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {t.change_24h != null ? `${t.change_24h >= 0 ? "+" : ""}${t.change_24h.toFixed(2)}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
