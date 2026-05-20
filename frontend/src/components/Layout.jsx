import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  LayoutDashboard, 
  Monitor, 
  Shield, 
  AlertTriangle, 
  FileCheck,
  LogOut,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'

const Layout = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/devices', icon: Monitor, label: 'Devices' },
    { path: '/certificates', icon: Shield, label: 'Certificates' },
    { path: '/alerts', icon: AlertTriangle, label: 'Alerts' },
    { path: '/compliance', icon: FileCheck, label: 'Compliance' },
  ]

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Mobile sidebar toggle */}
      <button
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-dark-800 rounded-lg"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X /> : <Menu />}
      </button>

      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full w-64 bg-dark-800 border-r border-dark-600 transform transition-transform duration-200 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} z-40`}>
        <div className="p-6">
          <h1 className="text-xl font-bold text-white mb-8">Network Compliance</h1>
          
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-dark-700'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon size={20} />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-dark-600">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
              {user.username[0].toUpperCase()}
            </div>
            <div>
              <p className="font-medium text-white">{user.username}</p>
              <p className="text-sm text-gray-400">{user.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
