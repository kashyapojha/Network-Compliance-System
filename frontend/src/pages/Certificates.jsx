import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Shield, 
  Download, 
  X,
  RefreshCw,
  CheckCircle,
  XCircle
} from 'lucide-react'

const Certificates = () => {
  const [caInfo, setCaInfo] = useState(null)
  const [certificates, setCertificates] = useState([])
  const [devices, setDevices] = useState([])
  const [selectedDeviceId, setSelectedDeviceId] = useState('')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setError('')
    try {
      const [caResponse, certsResponse, devicesResponse] = await Promise.all([
        axios.get('/api/certificates/ca/info'),
        axios.get('/api/certificates/'),
        axios.get('/api/devices')
      ])
      setCaInfo(caResponse.data)
      setCertificates(certsResponse.data)
      setDevices(devicesResponse.data)
    } catch (err) {
      console.error('Failed to fetch certificates:', err)
      setError('Failed to load certificate data')
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async (certId) => {
    if (!confirm('Are you sure you want to revoke this certificate?')) return
    
    try {
      await axios.post(`/api/certificates/${certId}/revoke`, { reason: 'Admin revocation' })
      fetchData()
    } catch (err) {
      console.error('Failed to revoke certificate:', err)
      setError(err.response?.data?.error || 'Failed to revoke certificate')
    }
  }

  const handleDownload = async (certId) => {
    try {
      const response = await axios.get(`/api/certificates/${certId}/download`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `certificate-${certId}.pem`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download certificate:', err)
      setError(err.response?.data?.error || 'Failed to download certificate')
    }
  }

  const handleGenerate = async () => {
    if (!selectedDeviceId) {
      setError('Please select a device')
      return
    }

    setGenerating(true)
    setError('')
    try {
      await axios.post(`/api/certificates/generate/${selectedDeviceId}`)
      setSelectedDeviceId('')
      fetchData()
    } catch (err) {
      console.error('Failed to generate certificate:', err)
      setError(err.response?.data?.error || 'Failed to generate certificate')
    } finally {
      setGenerating(false)
    }
  }

  const devicesWithoutCert = devices.filter(
    (d) => !certificates.some((c) => c.device_id === d.id && !c.is_revoked)
  )

  if (loading) {
    return <div className="text-center py-12">Loading certificates...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Certificates</h1>
        <button onClick={fetchData} className="btn btn-primary flex items-center gap-2">
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* CA Information */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield size={20} />
          Certificate Authority
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Subject</p>
            <p className="text-white font-mono text-sm">{caInfo?.subject || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Issuer</p>
            <p className="text-white font-mono text-sm">{caInfo?.issuer || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Serial Number</p>
            <p className="text-white font-mono text-sm">{caInfo?.serial_number || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Valid Until</p>
            <p className="text-white font-mono text-sm">
              {caInfo?.not_valid_after ? new Date(caInfo.not_valid_after).toLocaleDateString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Device Certificates */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Device Certificates</h2>
        <div className="space-y-4">
          {certificates.map((cert) => (
            <div key={cert.id} className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center gap-4">
                {cert.is_revoked ? (
                  <XCircle size={24} className="text-red-500" />
                ) : (
                  <CheckCircle size={24} className="text-green-500" />
                )}
                <div>
                  <p className="font-medium text-white">{cert.device_hostname || `Device #${cert.device_id}`}</p>
                  <p className="text-sm text-gray-400">
                    Serial: {cert.serial_number}
                    {cert.is_revoked ? ' - Revoked' : ''}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {cert.is_revoked ? (
                  <span className="px-2 py-1 bg-red-900/50 text-red-400 rounded text-xs">
                    Revoked
                  </span>
                ) : (
                  <>
                    <button
                      onClick={() => handleDownload(cert.id)}
                      className="btn btn-primary flex items-center gap-2"
                    >
                      <Download size={16} />
                      Download
                    </button>
                    <button
                      onClick={() => handleRevoke(cert.id)}
                      className="btn btn-danger flex items-center gap-2"
                    >
                      <X size={16} />
                      Revoke
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
          {certificates.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              No device certificates issued yet
            </div>
          )}
        </div>
      </div>

      {/* Certificate Generation */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Generate Certificate</h2>
        <p className="text-gray-400 mb-4">
          Generate a new certificate for a registered device. The device will be authorized automatically.
        </p>
        <div className="flex items-center gap-4">
          <select
            className="input flex-1"
            value={selectedDeviceId}
            onChange={(e) => setSelectedDeviceId(e.target.value)}
          >
            <option value="">Select a device...</option>
            {devicesWithoutCert.map((device) => (
              <option key={device.id} value={device.id}>
                {device.hostname} ({device.mac_address})
              </option>
            ))}
          </select>
          <button
            onClick={handleGenerate}
            disabled={generating || !selectedDeviceId}
            className="btn btn-primary"
          >
            {generating ? 'Generating...' : 'Generate Certificate'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Certificates
