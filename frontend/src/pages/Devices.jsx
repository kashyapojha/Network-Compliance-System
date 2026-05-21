import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Lock, 
  Unlock,
  Search,
  Filter,
  Plus,
  Download,
  X,
  Wifi,
  Scan
} from 'lucide-react'

const Devices = () => {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [showRegister, setShowRegister] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    hostname: '',
    mac_address: '',
    ip_address: '',
    device_type: 'workstation',
    department: 'IT'
  })
  const [networkInfo, setNetworkInfo] = useState(null)
  const [discovered, setDiscovered] = useState([])
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    fetchDevices()
    fetchNetworkInfo()
  }, [filter])

  const fetchNetworkInfo = async () => {
    try {
      const response = await axios.get('/api/monitoring/network-info')
      setNetworkInfo(response.data)
    } catch (err) {
      console.error('Failed to fetch network info:', err)
    }
  }

  const handleAutoFill = async () => {
    try {
      const response = await axios.get('/api/devices/local-info')
      setForm({
        ...form,
        hostname: response.data.hostname || form.hostname,
        mac_address: response.data.mac_address || form.mac_address,
        ip_address: response.data.ip_address || form.ip_address,
      })
      setShowRegister(true)
      setError('')
    } catch (err) {
      setError('Could not detect device info from server')
    }
  }

  const handleScanNetwork = async () => {
    setScanning(true)
    setError('')
    try {
      const response = await axios.post('/api/monitoring/scan', {
        network_range: networkInfo?.network_range
      })
      setDiscovered(response.data.devices || [])
      fetchDevices()
      if (response.data.alerts_created > 0) {
        setError('')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Scan failed. Run backend as Administrator on Windows.')
    } finally {
      setScanning(false)
    }
  }

  const fetchDevices = async () => {
    try {
      const params = {}
      if (filter === 'authorized') params.authorized = 'true'
      if (filter === 'unauthorized') params.authorized = 'false'
      if (filter === 'quarantined') params.quarantined = 'true'
      
      const response = await axios.get('/api/devices', { params })
      setDevices(response.data)
    } catch (err) {
      console.error('Failed to fetch devices:', err)
      setError('Failed to load devices')
    } finally {
      setLoading(false)
    }
  }

  const handleAuthorize = async (deviceId) => {
    try {
      await axios.post(`/api/devices/${deviceId}/authorize`)
      fetchDevices()
    } catch (err) {
      console.error('Failed to authorize device:', err)
      setError(err.response?.data?.error || 'Failed to authorize device')
    }
  }

  const handleQuarantine = async (deviceId) => {
    try {
      await axios.post(`/api/devices/${deviceId}/quarantine`)
      fetchDevices()
    } catch (err) {
      console.error('Failed to quarantine device:', err)
      setError(err.response?.data?.error || 'Failed to quarantine device')
    }
  }

  const handleDownloadCert = async (deviceId) => {
    try {
      const certsResponse = await axios.get(`/api/certificates/device/${deviceId}`)
      const activeCert = certsResponse.data.find((c) => !c.is_revoked)
      if (!activeCert) {
        setError('No active certificate for this device')
        return
      }
      const response = await axios.get(`/api/certificates/${activeCert.id}/download`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `device-${deviceId}-cert.pem`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download certificate:', err)
      setError(err.response?.data?.error || 'Failed to download certificate')
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await axios.post('/api/devices', form)
      setShowRegister(false)
      setForm({
        hostname: '',
        mac_address: '',
        ip_address: '',
        device_type: 'workstation',
        department: 'IT'
      })
      fetchDevices()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to register device')
    } finally {
      setSubmitting(false)
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
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-white">Devices</h1>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleScanNetwork}
            disabled={scanning}
            className="btn btn-primary flex items-center gap-2"
          >
            <Scan size={18} />
            {scanning ? 'Scanning...' : 'Scan Network'}
          </button>
          <button
            onClick={handleAutoFill}
            className="btn bg-dark-700 hover:bg-dark-600 text-white flex items-center gap-2"
          >
            <Wifi size={18} />
            Use My Device Info
          </button>
          <button
            onClick={() => setShowRegister(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus size={18} />
            Register Device
          </button>
        </div>
      </div>

      {networkInfo && (
        <div className="card text-sm">
          <p className="text-gray-400">
            Auto-detected network: <span className="text-white font-mono">{networkInfo.network_range}</span>
            {' · '}This machine: <span className="text-white font-mono">{networkInfo.ip_address}</span>
            {networkInfo.mac_address && (
              <> · MAC: <span className="text-white font-mono">{networkInfo.mac_address}</span></>
            )}
          </p>
        </div>
      )}

      {discovered.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-bold text-white mb-3">Devices found on last scan</h2>
          <div className="space-y-2">
            {discovered.map((d) => (
              <div key={d.mac_address} className="flex flex-wrap items-center justify-between gap-2 p-3 bg-dark-700 rounded-lg">
                <div>
                  <p className="text-white font-medium">{d.hostname}</p>
                  <p className="text-gray-400 text-xs font-mono">{d.ip_address} · {d.mac_address}</p>
                </div>
                <button
                  type="button"
                  className="btn btn-primary text-sm"
                  onClick={() => {
                    setForm({
                      hostname: d.hostname,
                      mac_address: d.mac_address,
                      ip_address: d.ip_address,
                      device_type: 'workstation',
                      department: 'IT'
                    })
                    setShowRegister(true)
                  }}
                >
                  Register
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-200 hover:text-white">
            <X size={16} />
          </button>
        </div>
      )}

      {showRegister && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Register New Device</h2>
            <button onClick={() => setShowRegister(false)} className="text-gray-400 hover:text-white">
              <X size={20} />
            </button>
          </div>
          <form onSubmit={handleRegister} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-300 mb-2">Hostname</label>
              <input
                className="input w-full"
                value={form.hostname}
                onChange={(e) => setForm({ ...form, hostname: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">MAC Address</label>
              <input
                className="input w-full"
                value={form.mac_address}
                onChange={(e) => setForm({ ...form, mac_address: e.target.value })}
                placeholder="AA:BB:CC:DD:EE:FF"
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">IP Address</label>
              <input
                className="input w-full"
                value={form.ip_address}
                onChange={(e) => setForm({ ...form, ip_address: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">Device Type</label>
              <select
                className="input w-full"
                value={form.device_type}
                onChange={(e) => setForm({ ...form, device_type: e.target.value })}
              >
                <option value="workstation">Workstation</option>
                <option value="laptop">Laptop</option>
                <option value="server">Server</option>
                <option value="mobile">Mobile</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">Department</label>
              <input
                className="input w-full"
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
                required
              />
            </div>
            <div className="md:col-span-2 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleAutoFill}
                className="btn bg-dark-700 hover:bg-dark-600 text-white"
              >
                Auto-fill from this PC
              </button>
              <button type="submit" disabled={submitting} className="btn btn-primary">
                {submitting ? 'Registering...' : 'Register'}
              </button>
              <button type="button" onClick={() => setShowRegister(false)} className="btn bg-dark-700 hover:bg-dark-600 text-white">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

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
              <th>First Seen</th>
              <th>Last Seen</th>
              <th>Times Seen</th>
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
                <td className="text-sm text-gray-400 whitespace-nowrap">
                  {device.first_seen ? new Date(device.first_seen).toLocaleString() : '—'}
                </td>
                <td className="text-sm text-gray-400 whitespace-nowrap">
                  {device.last_seen ? new Date(device.last_seen).toLocaleString() : '—'}
                </td>
                <td className="text-sm text-gray-100">{device.times_seen ?? 0}</td>
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
                        className="p-2 hover:bg-dark-700 rounded cursor-pointer"
                        title="Quarantine"
                      >
                        <Lock size={16} className="text-yellow-500" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAuthorize(device.id)}
                        className="p-2 hover:bg-dark-700 rounded cursor-pointer"
                        title="Authorize"
                      >
                        <Unlock size={16} className="text-green-500" />
                      </button>
                    )}
                    {device.certificate_count > 0 && (
                      <button
                        onClick={() => handleDownloadCert(device.id)}
                        className="p-2 hover:bg-dark-700 rounded cursor-pointer"
                        title="Download Certificate"
                      >
                        <Download size={16} className="text-gray-400" />
                      </button>
                    )}
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
