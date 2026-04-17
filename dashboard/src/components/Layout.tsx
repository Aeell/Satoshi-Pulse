import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Card, Metric, Text, Badge, Grid, Flex } from '@tremor/react'

const Layout = ({ children }: { children?: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const navItems = [
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Market', href: '/market' },
    { name: 'On-Chain', href: '/onchain' },
    { name: 'Signals', href: '/signals' },
    { name: 'Settings', href: '/settings' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b px-4 py-3">
        <Flex justifyContent="between">
          <Text className="font-bold text-xl">Satoshi Pulse</Text>
          <Badge color="green">Connected</Badge>
        </Flex>
      </nav>
      <div className="flex">
        <aside className="w-48 bg-white border-r p-4">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `block py-2 px-3 rounded ${isActive ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`
              }
            >
              {item.name}
            </NavLink>
          ))}
        </aside>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}

export default Layout