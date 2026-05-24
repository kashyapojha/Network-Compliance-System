import { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { 
  Monitor, 
  Shield, 
  AlertTriangle, 
  TrendingUp,
  Activity,
  Lock
} from 'lucide-react'

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  // FIX: track message + type separately so success vs error can be styled differently
  const [actionMessage, setActionMessage] = useState({ text: '', type: '' })
  const [networkInfo, setNetworkInfo] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanHistory, setScanHistory] = useState([])
  const [currentTime, setCurrentTime] = useState(new Date())
  const navigate = useNavigate()

  useEffect(() => {
    // FIX: fetch network info first so the metrics call has the range available
    fetchNetworkInfo().then(info => fetchMetrics(info?.network_range))
    fetchScanHistory()
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  // FIX: re-fetch metrics whenever networkInfo changes so the
  // unresolved count updates immediately after network detection
  useEffect(() => {
    if (networkInfo) fetchMetrics(networkInfo.network_range)
  }, [networkInfo])

  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timeInterval)
  }, [])

  const fetchNetworkInfo = async () => {
    try {
      const response = await axios.get('/api/monitoring/network-info')
      setNetworkInfo(response.data)
      return response.data  // FIX: return so callers can chain immediately
    } catch (error) {
      console.error('Failed to fetch network info:', error)
      return null
    }
  }

  const fetchScanHistory = async () => {
    try {
      const res = await axios.get('/api/monitoring/scan-history', { timeout: 10000 })
      setScanHistory(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      console.error('Failed to fetch scan history:', err)
    }
  }

  const fetchMetrics = async (networkRange) => {
    // FIX: accept networkRange as param so it works correctly on first load
    // before React state has updated, falling back to state value
    const range = networkRange ?? networkInfo?.network_range
    try {
      const [metricsRes, statusRes] = await Promise.all([
        axios.get('/api/compliance/metrics', {
          timeout: 15000,
          params: range ? { network_range: range } : {}
        }),
        axios.get('/api/monitoring/status', { timeout: 15000 }).catch(() => ({ data: { running: false } }))
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
    // FIX: clear stale message before every new scan attempt
    setActionMessage({ text: '', type: '' })
    try {
      const response = await axios.post('/api/monitoring/scan', {
        network_range: networkInfo?.network_range
      }, { timeout: 30000 }) // 30s — parallel ping sweep completes in 3-5s
      await fetchMetrics(networkInfo?.network_range)
      fetchScanHistory()
      const { devices_found, alerts_created, network_range } = response.data
      setActionMessage({
        text: `Scan complete on ${network_range}: ${devices_found} device(s) found, ${alerts_created} new alert(s).`,
        type: 'success',
      })
    } catch (error) {
      console.error('Scan error:', error)
      // FIX: read error.response.data.message (the detailed string set by the
      // backend) first, then fall back to .error (the short code), then a
      // truly generic fallback only if the request never reached the backend.
      const detail =
        error.response?.data?.message ||
        error.response?.data?.error ||
        (error.request
          ? 'No response from backend — is the server running?'
          : `Request error: ${error.message}`)
      setActionMessage({ text: detail, type: 'error' })
    } finally {
      setScanning(false)
    }
  }

  const handleGenerateReport = async () => {
    setActionMessage({ text: '', type: '' })
    try {
      await axios.post('/api/compliance/report', { type: 'full' })
      setActionMessage({ text: 'Compliance report generated', type: 'success' })
      navigate('/compliance')
    } catch (error) {
      console.error('Failed to generate report:', error)
      setActionMessage({ text: 'Failed to generate report', type: 'error' })
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
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-gray-400">
            <Activity size={20} className="text-green-500" />
            <span className={metrics?.monitoring?.running ? 'text-green-500' : 'text-yellow-500'}>
              {metrics?.monitoring?.running ? 'Monitoring Active' : 'Manual Scan'}
            </span>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </div>
            <div className="text-sm text-gray-400">
              {currentTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </div>
          </div>
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
            <Activity size={20} />
            Recent Scan Activity
          </h2>
          <div className="space-y-2">
            {scanHistory.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-4">No scans yet — run a scan to see history</p>
            ) : (
              scanHistory.slice(0, 5).map((entry, i) => (
                <div key={i} className="flex items-center justify-between text-sm py-1 border-b border-dark-700 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-mono text-xs w-36">
                      {new Date(entry.timestamp + 'Z').toLocaleTimeString('en-IN', {
                        timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: true
                      })}
                    </span>
                    <span className="text-white font-mono text-xs">{entry.network_range}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-primary-400">{entry.devices_found} device{entry.devices_found !== 1 ? 's' : ''}</span>
                    <span className={entry.alerts_created > 0 ? 'text-yellow-400' : 'text-gray-500'}>
                      {entry.alerts_created} alert{entry.alerts_created !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
              ))
            )}
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

        {/* FIX: success = green, error = red, clearly distinct */}
        {actionMessage.text && (
          <p className={`text-sm mb-4 ${
            actionMessage.type === 'error' ? 'text-red-400' : 'text-green-400'
          }`}>
            {actionMessage.text}
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={handleScanNetwork} disabled={scanning} className="btn btn-primary">
            {scanning ? 'Scanning…' : 'Start Network Scan'}
          </button>
          <button onClick={handleGenerateReport} className="btn btn-primary">Generate Compliance Report</button>
          <button onClick={handleViewAlerts} className="btn btn-primary">View All Alerts</button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard