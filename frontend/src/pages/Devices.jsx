import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Monitor, 
  Shield, 
  Lock, 
  Unlock,
  Search,
  Filter,
  Plus,
  Download
} from 'lucide-react'

const Devices = () => {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchDevices()
  }, [filter])

  const fetchDevices = async () => {
    try {
      const params = {}
      if (filter === 'authorized') params.authorized = 'true'
      if (filter === 'unauthorized') params.authorized = 'false'
      if (filter === 'quarantined') params.quarantined = 'true'
      
      const response = await axios.get('/api/devices', { params })
      setDevices(response.data)
    } catch (error) {
      console.error('Failed to fetch devices:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAuthorize = async (deviceId) => {
    try {
      await axios.post(`/api/devices/${deviceId}/authorize`)
      fetchDevices()
    } catch (error) {
      console.error('Failed to authorize device:', error)
    }
  }

  const handleQuarantine = async (deviceId) => {
    try {
      await axios.post(`/api/devices/${deviceId}/quarantine`)
      fetchDevices()
    } catch (error) {
      console.error('Failed to quarantine device:', error)
    }
  }

  const filteredDevices = devices.filter(device =>
    device.hostname.toLowerCase().includes(search.toLowerCase()) ||
    device.mac_address.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return <div className="text-center py-12">Loading devices...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Devices</h1>
        <button className="btn btn-primary flex items-center gap-2">
          <Plus size={18} />
          Register Device
        </button>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 flex-1 min-w-64">
          <Search size={20} className="text-gray-400" />
          <input
            type="text"
            placeholder="Search devices..."
            className="input flex-1"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={20} className="text-gray-400" />
          <select
            className="input"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Devices</option>
            <option value="authorized">Authorized</option>
            <option value="unauthorized">Unauthorized</option>
            <option value="quarantined">Quarantined</option>
          </select>
        </div>
      </div>

      {/* Devices Table */}
      <div className="card overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Hostname</th>
              <th>MAC Address</th>
              <th>IP Address</th>
              <th>Type</th>
              <th>Department</th>
              <th>Status</th>
              <th>Trust Score</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredDevices.map((device) => (
              <tr key={device.id}>
                <td className="font-medium">{device.hostname}</td>
                <td className="font-mono text-sm">{device.mac_address}</td>
                <td className="font-mono text-sm">{device.ip_address || 'N/A'}</td>
                <td>{device.device_type}</td>
                <td>{device.department}</td>
                <td>
                  {device.is_authorized ? (
                    <span className="px-2 py-1 bg-green-900/50 text-green-400 rounded text-xs">
                      Authorized
                    </span>
                  ) : device.is_quarantined ? (
                    <span className="px-2 py-1 bg-red-900/50 text-red-400 rounded text-xs">
                      Quarantined
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-yellow-900/50 text-yellow-400 rounded text-xs">
                      Unauthorized
                    </span>
                  )}
                </td>
                <td>
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-dark-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          device.trust_score >= 80 ? 'bg-green-500' :
                          device.trust_score >= 50 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${device.trust_score}%` }}
                      />
                    </div>
                    <span className="text-sm">{device.trust_score}</span>
                  </div>
                </td>
                <td>
                  <div className="flex items-center gap-2">
                    {device.is_authorized ? (
                      <button
                        onClick={() => handleQuarantine(device.id)}
                        className="p-2 hover:bg-dark-700 rounded"
                        title="Quarantine"
                      >
                        <Lock size={16} className="text-yellow-500" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAuthorize(device.id)}
                        className="p-2 hover:bg-dark-700 rounded"
                        title="Authorize"
                      >
                        <Unlock size={16} className="text-green-500" />
                      </button>
                    )}
                    <button className="p-2 hover:bg-dark-700 rounded" title="Download Certificate">
                      <Download size={16} className="text-gray-400" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredDevices.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            No devices found
          </div>
        )}
      </div>
    </div>
  )
}

export default Devices
