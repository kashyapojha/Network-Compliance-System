import { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
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
  const [actionMessage, setActionMessage] = useState('')
  const [networkInfo, setNetworkInfo] = useState(null)
  const [scanning, setScanning] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchMetrics()
    fetchNetworkInfo()
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchNetworkInfo = async () => {
    try {
      const response = await axios.get('/api/monitoring/network-info')
      setNetworkInfo(response.data)
    } catch (error) {
      console.error('Failed to fetch network info:', error)
    }
  }

  const fetchMetrics = async () => {
    try {
      const [metricsRes, statusRes] = await Promise.all([
        axios.get('/api/compliance/metrics'),
        axios.get('/api/monitoring/status').catch(() => ({ data: { running: false } }))
      ])
      setMetrics({
        ...metricsRes.data,
        monitoring: statusRes.data
      })
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleScanNetwork = async () => {
    setScanning(true)
    setActionMessage('')
    try {
      const response = await axios.post('/api/monitoring/scan', {
        network_range: networkInfo?.network_range
      })
      await fetchMetrics()
      const { devices_found, alerts_created, network_range } = response.data
      setActionMessage(
        `Scan complete on ${network_range}: ${devices_found} device(s) found, ${alerts_created} new alert(s). Check Alerts page.`
      )
    } catch (error) {
      console.error('Failed to scan network:', error)
      setActionMessage(error.response?.data?.error || 'Network scan failed. Is the backend running as Administrator?')
    } finally {
      setScanning(false)
    }
  }

  const handleGenerateReport = async () => {
    try {
      await axios.post('/api/compliance/report', { type: 'full' })
      setActionMessage('Compliance report generated')
      navigate('/compliance')
    } catch (error) {
      console.error('Failed to generate report:', error)
      setActionMessage('Failed to generate report')
    }
  }

  const handleViewAlerts = () => {
    navigate('/alerts')
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
          <span className={metrics?.monitoring?.running ? 'text-green-500' : 'text-yellow-500'}>
            {metrics?.monitoring?.running ? 'Monitoring Active' : 'Manual Scan'}
          </span>
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
            <span className="text-2xl font-bold text-white">{alertMetrics.unresolved ?? 0}</span>
          </div>
          <p className="text-gray-400">Unresolved Alerts</p>
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
                {metrics?.compliance?.score ?? 100}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Based on unresolved alerts</span>
              <span className="text-gray-400">{metrics?.compliance?.unresolved_alerts ?? 0} open</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Quarantined Devices</span>
              <span className="text-yellow-500 font-bold">{deviceMetrics.quarantined || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Network info */}
      {networkInfo && (
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-3">Detected Network (this server)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-400">Your IP</p>
              <p className="text-white font-mono">{networkInfo.ip_address}</p>
            </div>
            <div>
              <p className="text-gray-400">Your MAC</p>
              <p className="text-white font-mono">{networkInfo.mac_address || 'N/A'}</p>
            </div>
            <div>
              <p className="text-gray-400">Hostname</p>
              <p className="text-white">{networkInfo.hostname}</p>
            </div>
            <div>
              <p className="text-gray-400">Scan range</p>
              <p className="text-white font-mono">{networkInfo.network_range}</p>
            </div>
          </div>
          <p className="text-gray-500 text-xs mt-3">
            Scans run on the machine where the backend runs. Unregistered devices on this network trigger alerts.
          </p>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
        {actionMessage && (
          <p className="text-sm text-primary-400 mb-4">{actionMessage}</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={handleScanNetwork} disabled={scanning} className="btn btn-primary">
            {scanning ? 'Scanning...' : 'Start Network Scan'}
          </button>
          <button onClick={handleGenerateReport} className="btn btn-primary">Generate Compliance Report</button>
          <button onClick={handleViewAlerts} className="btn btn-primary">View All Alerts</button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
