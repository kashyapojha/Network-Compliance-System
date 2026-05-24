import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  AlertTriangle, 
  Check, 
  X,
  Filter,
  Search
} from 'lucide-react'

// FIX: Convert a UTC datetime string from the backend into IST (Asia/Kolkata)
// The backend stores timestamps without 'Z', so we append it to tell JS it's UTC.
const formatIST = (utcString) => {
  if (!utcString) return '—'
  return new Date(utcString + 'Z').toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  })
}

const Alerts = () => {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [stats, setStats] = useState(null)
  const [networkInfo, setNetworkInfo] = useState(null)
  const [filterByNetwork, setFilterByNetwork] = useState(true)

  useEffect(() => {
    fetchAlerts()
    fetchNetworkInfo()
    const interval = setInterval(fetchAlerts, 15000)
    const onNewAlert = () => fetchAlerts()
    window.addEventListener('compliance:new-alert', onNewAlert)
    return () => {
      clearInterval(interval)
      window.removeEventListener('compliance:new-alert', onNewAlert)
    }
  }, [filter])

  const fetchAlerts = async () => {
    try {
      setError('')
      const params = {}
      if (filter === 'resolved') params.resolved = 'true'
      if (filter === 'unresolved') params.resolved = 'false'

      const [alertsRes, statsRes] = await Promise.all([
        axios.get('/api/alerts', { params }),
        axios.get('/api/alerts/stats')
      ])
      setAlerts(Array.isArray(alertsRes.data) ? alertsRes.data : [])
      setStats(statsRes.data)
    } catch (err) {
      console.error('Failed to fetch alerts:', err)
      setError('Failed to load alerts. Make sure the backend is running.')
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  const fetchNetworkInfo = async () => {
    try {
      const res = await axios.get('/api/monitoring/network-info')
      setNetworkInfo(res.data)
    } catch (err) {
      console.error('Failed to fetch network info:', err)
    }
  }

  const handleResolve = async (alertId) => {
    try {
      await axios.post(`/api/alerts/${alertId}/resolve`, { resolved_by: 'admin' })
      fetchAlerts()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-900/50 text-red-400'
      case 'high': return 'bg-orange-900/50 text-orange-400'
      case 'medium': return 'bg-yellow-900/50 text-yellow-400'
      case 'low': return 'bg-blue-900/50 text-blue-400'
      default: return 'bg-gray-900/50 text-gray-400'
    }
  }

  // Returns true if ip falls within a CIDR range (e.g. 192.168.1.0/24)
  const ipInNetwork = (ip, cidr) => {
    try {
      if (!ip || !cidr) return true
      const [netAddr, prefixLen] = cidr.split('/')
      const prefix = parseInt(prefixLen, 10)
      const ipToInt = (s) => s.split('.').reduce((acc, o) => (acc << 8) + parseInt(o, 10), 0) >>> 0
      const mask = prefix === 0 ? 0 : (0xffffffff << (32 - prefix)) >>> 0
      return (ipToInt(ip) & mask) === (ipToInt(netAddr) & mask)
    } catch { return true }
  }

  const filteredAlerts = alerts.filter(alert => {
    // Network filter — only show alerts from the current subnet
    if (filterByNetwork && networkInfo?.network_range) {
      if (!ipInNetwork(alert.ip_address, networkInfo.network_range)) return false
    }
    const q = search.toLowerCase()
    const title = (alert.title || '').toLowerCase()
    const desc = (alert.description || '').toLowerCase()
    const mac = (alert.mac_address || '').toLowerCase()
    return title.includes(q) || desc.includes(q) || mac.includes(q)
  })

  if (loading) {
    return <div className="text-center py-12">Loading alerts...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Alerts</h1>
        <div className="flex items-center gap-4">
          {stats && (
            <span className="text-gray-400 text-sm">
              {stats.unresolved} unresolved · {stats.total} total
            </span>
          )}
          <button onClick={fetchAlerts} className="btn btn-primary text-sm">
            Refresh
          </button>
          {networkInfo && (
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={filterByNetwork}
                onChange={e => setFilterByNetwork(e.target.checked)}
                className="accent-primary-500"
              />
              This network only
              <span className="font-mono text-xs text-gray-500">({networkInfo.network_range})</span>
            </label>
          )}
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              className="input"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All Alerts</option>
              <option value="unresolved">Unresolved</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Search */}
      <div className="card flex items-center gap-2">
        <Search size={20} className="text-gray-400" />
        <input
          type="text"
          placeholder="Search alerts..."
          className="input flex-1"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <div key={alert.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <AlertTriangle size={20} className="text-yellow-500" />
                  <h3 className="font-bold text-white">{alert.title}</h3>
                  <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(alert.severity)}`}>
                    {alert.severity.toUpperCase()}
                  </span>
                  {alert.is_resolved && (
                    <span className="px-2 py-1 bg-green-900/50 text-green-400 rounded text-xs">
                      Resolved
                    </span>
                  )}
                </div>
                <p className="text-gray-400 mb-2">{alert.description}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  {alert.device_hostname && (
                    <span>Device: {alert.device_hostname}</span>
                  )}
                  {alert.ip_address && (
                    <span>IP: {alert.ip_address}</span>
                  )}
                  {alert.mac_address && (
                    <span>MAC: {alert.mac_address}</span>
                  )}
                  {/* FIX: was new Date(alert.created_at).toLocaleString()
                      which treated the UTC string as local time, showing
                      timestamps 5h30m behind IST. Now explicitly converts
                      UTC → IST using Asia/Kolkata timezone. */}
                  <span>{formatIST(alert.created_at)}</span>
                </div>
                {alert.is_resolved && alert.resolved_at && (
                  <div className="mt-1 text-xs text-gray-600">
                    Resolved {formatIST(alert.resolved_at)}
                    {alert.resolved_by ? ` by ${alert.resolved_by}` : ''}
                  </div>
                )}
              </div>
              {!alert.is_resolved && (
                <button
                  onClick={() => handleResolve(alert.id)}
                  className="btn btn-success flex items-center gap-2"
                >
                  <Check size={16} />
                  Resolve
                </button>
              )}
            </div>
          </div>
        ))}

        {filteredAlerts.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <p>No alerts found.</p>
            <p className="text-sm mt-2">
              Run a network scan from Dashboard or Devices to detect unknown/unauthorized devices.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Alerts