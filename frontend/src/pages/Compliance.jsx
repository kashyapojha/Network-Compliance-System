import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  FileCheck, 
  TrendingUp, 
  Download,
  Calendar,
  BarChart3
} from 'lucide-react'

const Compliance = () => {
  const [score, setScore] = useState(null)
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  // FIX: track network info so /score and reports use the current subnet
  const [networkInfo, setNetworkInfo] = useState(null)

  useEffect(() => {
    // FIX: fetch network info first, then compliance data with the range
    fetchNetworkInfo().then(info => fetchComplianceData(info?.network_range))
  }, [])

  const fetchNetworkInfo = async () => {
    try {
      const res = await axios.get('/api/monitoring/network-info')
      setNetworkInfo(res.data)
      return res.data
    } catch (error) {
      console.error('Failed to fetch network info:', error)
      return null
    }
  }

  const fetchComplianceData = async (networkRange) => {
    const range = networkRange ?? networkInfo?.network_range
    try {
      const params = range ? { network_range: range } : {}
      const [scoreResponse, reportsResponse] = await Promise.all([
        // FIX: pass network_range so /score filters alerts to current subnet
        axios.get('/api/compliance/score', { params }),
        axios.get('/api/compliance/reports')
      ])
      setScore(scoreResponse.data)
      setReports(reportsResponse.data)
    } catch (error) {
      console.error('Failed to fetch compliance data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReport = async (type) => {
    try {
      // FIX: pass network_range so the generated report score is network-scoped
      await axios.post('/api/compliance/report', {
        type,
        network_range: networkInfo?.network_range
      })
      fetchComplianceData(networkInfo?.network_range)
    } catch (error) {
      console.error('Failed to generate report:', error)
    }
  }

  const handleExportLatest = async () => {
    try {
      let reportId = reports[0]?.id
      if (!reportId) {
        const response = await axios.post('/api/compliance/report', {
          type: 'on_demand',
          network_range: networkInfo?.network_range
        })
        reportId = response.data.id
        await fetchComplianceData(networkInfo?.network_range)
      }
      await handleViewReport(reportId)
    } catch (error) {
      console.error('Failed to export report:', error)
    }
  }

  const handleViewReport = async (reportId) => {
    try {
      const response = await axios.get(`/api/compliance/reports/${reportId}`)
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `compliance-report-${reportId}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export report:', error)
    }
  }

  const getScoreColor = (s) => {
    if (s >= 90) return 'text-green-500'
    if (s >= 70) return 'text-yellow-500'
    return 'text-red-500'
  }

  // FIX: report timestamps in IST, same as Alerts page
  const formatIST = (utcString) => {
    if (!utcString) return '—'
    return new Date(utcString + 'Z').toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: true,
    })
  }

  if (loading) {
    return <div className="text-center py-12">Loading compliance data...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Compliance</h1>
        <div className="flex items-center gap-3">
          {networkInfo && (
            <span className="text-xs text-gray-500 font-mono">{networkInfo.network_range}</span>
          )}
          <button onClick={handleExportLatest} className="btn btn-primary flex items-center gap-2">
            <Download size={18} />
            Export Report
          </button>
        </div>
      </div>

      {/* Compliance Score */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <TrendingUp size={20} />
          Network Compliance Score
        </h2>
        <div className="flex items-center justify-center">
          <div className="relative w-48 h-48">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="96" cy="96" r="88" stroke="#1e293b" strokeWidth="12" fill="none"/>
              <circle
                cx="96" cy="96" r="88"
                stroke={score?.score >= 90 ? '#22c55e' : score?.score >= 70 ? '#eab308' : '#ef4444'}
                strokeWidth="12" fill="none"
                strokeDasharray={`${2 * Math.PI * 88}`}
                strokeDashoffset={`${2 * Math.PI * 88 * (1 - (score?.score ?? 0) / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <span className={`text-4xl font-bold ${getScoreColor(score?.score)}`}>
                {score?.score ?? 0}%
              </span>
              <span className="text-gray-400 text-sm">Compliance</span>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{score?.total_devices ?? 0}</p>
            <p className="text-gray-400 text-sm">Total Devices</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-500">{score?.authorized ?? 0}</p>
            <p className="text-gray-400 text-sm">Authorized</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-500">{score?.unauthorized ?? 0}</p>
            <p className="text-gray-400 text-sm">Unauthorized</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-500">{score?.quarantined ?? 0}</p>
            <p className="text-gray-400 text-sm">Quarantined</p>
          </div>
        </div>
      </div>

      {/* Generate Reports */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <FileCheck size={20} />
          Generate Compliance Report
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={() => handleGenerateReport('daily')} className="btn btn-primary flex items-center justify-center gap-2">
            <Calendar size={18} />Daily Report
          </button>
          <button onClick={() => handleGenerateReport('weekly')} className="btn btn-primary flex items-center justify-center gap-2">
            <Calendar size={18} />Weekly Report
          </button>
          <button onClick={() => handleGenerateReport('monthly')} className="btn btn-primary flex items-center justify-center gap-2">
            <Calendar size={18} />Monthly Report
          </button>
        </div>
      </div>

      {/* Recent Reports */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 size={20} />
          Recent Reports
        </h2>
        <div className="space-y-3">
          {reports.map((report) => (
            <div key={report.id} className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
              <div>
                <p className="font-medium text-white">{report.report_name}</p>
                {/* FIX: IST timestamp instead of raw UTC */}
                <p className="text-sm text-gray-400">{formatIST(report.created_at)}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-lg font-bold ${getScoreColor(report.compliance_score)}`}>
                  {report.compliance_score}%
                </span>
                <button onClick={() => handleViewReport(report.id)} className="btn btn-primary flex items-center gap-2">
                  <Download size={16} />View
                </button>
              </div>
            </div>
          ))}
          {reports.length === 0 && (
            <div className="text-center py-8 text-gray-400">No reports generated yet</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Compliance