// All requests proxy through Vite's /api → http://localhost:8000/api

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ── Dashboard ────────────────────────────────────────────────────────────────
export interface Overview {
  btc_price: number | null;
  btc_change_24h: number | null;
  fear_greed_value: number | null;
  fear_greed_classification: string | null;
  signals_last_24h: number;
  updated_at: string;
}
export interface Ticker {
  symbol: string; exchange: string; last: number | null;
  bid: number | null; ask: number | null; change_24h: number | null; timestamp: string;
}
export interface Candle {
  timestamp: string; open: number; high: number; low: number; close: number; volume: number;
}
export interface OnChainMetric { timestamp: string; metric_name: string; metric_value: number; }
export interface CollectorHealth { name: string; status: string; last_run: string | null; error_count: number; }

export const fetchOverview    = () => get<Overview>("/dashboard/overview");
export const fetchTickers     = () => get<{ tickers: Ticker[] }>("/dashboard/market");
export const fetchOhlcv       = (sym = "BTC", tf = "1m", limit = 100) =>
  get<{ symbol: string; timeframe: string; candles: Candle[] }>(
    `/dashboard/ohlcv?symbol=${sym}&timeframe=${tf}&limit=${limit}`
  );
export const fetchOnChain     = (sym = "BTC") =>
  get<{ symbol: string; metrics: OnChainMetric[] }>(`/dashboard/on-chain?symbol=${sym}`);
export const fetchCollectorHealth = () =>
  get<{ collectors: CollectorHealth[]; updated_at: string }>("/dashboard/health");

// ── Signals ──────────────────────────────────────────────────────────────────
export interface Signal {
  id: number; timestamp: string; symbol: string; strategy: string;
  signal_type: string; strength: number; price_target: number | null;
  stop_loss: number | null; executed: boolean;
}
export const fetchActiveSignals     = (hours = 24) =>
  get<{ signals: Signal[]; total: number }>(`/signals/active?hours=${hours}`);
export const fetchSignalPerformance = () =>
  get<{ total_signals: number; executed_signals: number; pending_signals: number }>(
    "/signals/performance"
  );

// ── Status ───────────────────────────────────────────────────────────────────
export interface CollectorStatus {
  name: string; status: string; last_run: string | null; next_run: string | null;
  error_count: number; last_error: string | null;
}
export interface SystemStatus {
  version: string; uptime_seconds: number; uptime_human: string; utc_now: string; pid: number;
}
export const fetchCollectorStatus = () => get<{ collectors: CollectorStatus[] }>("/status/collectors");
export const fetchDbStatus        = () =>
  get<{ connected: boolean; backend: string; size_mb: number | null }>("/status/database");
export const fetchSystemStatus    = () => get<SystemStatus>("/status/system");
