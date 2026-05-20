import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  AlertTriangle, 
  Check, 
  X,
  Filter,
  Search
} from 'lucide-react'

const Alerts = () => {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 15000)
    return () => clearInterval(interval)
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

  const filteredAlerts = alerts.filter(alert => {
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
                  <span>
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                </div>
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
