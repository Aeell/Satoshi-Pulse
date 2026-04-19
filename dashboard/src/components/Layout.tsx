import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { name: "Dashboard", href: "/dashboard", icon: "◈" },
  { name: "Market",    href: "/market",    icon: "📈" },
  { name: "On-Chain",  href: "/onchain",   icon: "⛓" },
  { name: "Signals",   href: "/signals",   icon: "⚡" },
  { name: "Status",    href: "/settings",  icon: "⚙" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">₿</span>
          <span className="font-bold text-white text-lg tracking-tight">Satoshi Pulse</span>
          <span className="text-xs text-gray-400 bg-gray-700 px-2 py-0.5 rounded-full">v2</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-gray-400">live</span>
        </div>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <nav className="w-48 bg-gray-800 border-r border-gray-700 p-4 flex-shrink-0">
          <div className="space-y-1">
            {NAV.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-blue-600 text-white font-medium"
                      : "text-gray-400 hover:text-white hover:bg-gray-700"
                  }`
                }
              >
                <span>{item.icon}</span>
                {item.name}
              </NavLink>
            ))}
          </div>
        </nav>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
