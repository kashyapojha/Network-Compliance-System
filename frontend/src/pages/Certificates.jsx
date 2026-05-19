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
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCertificates()
  }, [])

  const fetchCertificates = async () => {
    try {
      const response = await axios.get('/api/certificates/ca/info')
      // In a real implementation, you'd fetch all certificates
      setCertificates([response.data])
    } catch (error) {
      console.error('Failed to fetch certificates:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async (certId) => {
    if (!confirm('Are you sure you want to revoke this certificate?')) return
    
    try {
      await axios.post(`/api/certificates/${certId}/revoke`, { reason: 'Admin revocation' })
      fetchCertificates()
    } catch (error) {
      console.error('Failed to revoke certificate:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading certificates...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Certificates</h1>
        <button className="btn btn-primary flex items-center gap-2">
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {/* CA Information */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield size={20} />
          Certificate Authority
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Subject</p>
            <p className="text-white font-mono text-sm">{certificates[0]?.subject || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Issuer</p>
            <p className="text-white font-mono text-sm">{certificates[0]?.issuer || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Serial Number</p>
            <p className="text-white font-mono text-sm">{certificates[0]?.serial_number || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Valid Until</p>
            <p className="text-white font-mono text-sm">
              {certificates[0]?.not_valid_after ? new Date(certificates[0].not_valid_after).toLocaleDateString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Device Certificates */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Device Certificates</h2>
        <div className="space-y-4">
          {/* Example certificate entry */}
          <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
            <div className="flex items-center gap-4">
              <CheckCircle size={24} className="text-green-500" />
              <div>
                <p className="font-medium text-white">IT-WS-0042</p>
                <p className="text-sm text-gray-400">Serial: 1234567890ABCDEF</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="btn btn-primary flex items-center gap-2">
                <Download size={16} />
                Download
              </button>
              <button className="btn btn-danger flex items-center gap-2">
                <X size={16} />
                Revoke
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
            <div className="flex items-center gap-4">
              <XCircle size={24} className="text-red-500" />
              <div>
                <p className="font-medium text-white">HR-LPT-0023</p>
                <p className="text-sm text-gray-400">Serial: 0987654321FEDCBA - Revoked</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 bg-red-900/50 text-red-400 rounded text-xs">
                Revoked
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Certificate Generation */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Generate Certificate</h2>
        <p className="text-gray-400 mb-4">
          Generate a new certificate for a registered device. The device will be authorized automatically.
        </p>
        <div className="flex items-center gap-4">
          <select className="input flex-1">
            <option value="">Select a device...</option>
            <option value="1">IT-WS-0042</option>
            <option value="2">HR-LPT-0023</option>
          </select>
          <button className="btn btn-primary">
            Generate Certificate
          </button>
        </div>
      </div>
    </div>
  )
}

export default Certificates
