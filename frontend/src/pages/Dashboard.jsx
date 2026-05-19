import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Monitor, 
  Shield, 
  AlertTriangle, 
  TrendingUp,
  Activity,
  Users,
  Lock
} from 'lucide-react'

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/api/compliance/metrics')
      setMetrics(response.data)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  const deviceMetrics = metrics?.devices || {}
  const alertMetrics = metrics?.alerts || {}
  const authMetrics = metrics?.authentication || {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <div className="flex items-center gap-2 text-gray-400">
          <Activity size={20} className="text-green-500" />
          <span>Live Monitoring</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <Monitor className="text-primary-500" size={24} />
            <span className="text-2xl font-bold text-white">{deviceMetrics.total || 0}</span>
          </div>
          <p className="text-gray-400">Total Devices</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <Shield className="text-green-500" size={24} />
            <span className="text-2xl font-bold text-white">{deviceMetrics.authorized || 0}</span>
          </div>
          <p className="text-gray-400">Authorized Devices</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <AlertTriangle className="text-yellow-500" size={24} />
            <span className="text-2xl font-bold text-white">{alertMetrics.last_24h || 0}</span>
          </div>
          <p className="text-gray-400">Alerts (24h)</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <Lock className="text-red-500" size={24} />
            <span className="text-2xl font-bold text-white">{deviceMetrics.unauthorized || 0}</span>
          </div>
          <p className="text-gray-400">Unauthorized Devices</p>
        </div>
      </div>

      {/* Authentication Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Users size={20} />
            Authentication (24h)
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Successful</span>
              <span className="text-green-500 font-bold">{authMetrics.success_last_24h || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Failed</span>
              <span className="text-red-500 font-bold">{authMetrics.failure_last_24h || 0}</span>
            </div>
            <div className="w-full bg-dark-700 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{
                  width: `${(authMetrics.success_last_24h / (authMetrics.success_last_24h + authMetrics.failure_last_24h || 1)) * 100}%`
                }}
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={20} />
            Network Health
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Compliance Score</span>
              <span className="text-primary-500 font-bold">
                {deviceMetrics.total > 0 
                  ? Math.round((deviceMetrics.authorized / deviceMetrics.total) * 100) 
                  : 100}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Quarantined Devices</span>
              <span className="text-yellow-500 font-bold">{deviceMetrics.quarantined || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn btn-primary">Start Network Scan</button>
          <button className="btn btn-primary">Generate Compliance Report</button>
          <button className="btn btn-primary">View All Alerts</button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
