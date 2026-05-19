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

  useEffect(() => {
    fetchComplianceData()
  }, [])

  const fetchComplianceData = async () => {
    try {
      const [scoreResponse, reportsResponse] = await Promise.all([
        axios.get('/api/compliance/score'),
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
      await axios.post('/api/compliance/report', { type })
      fetchComplianceData()
    } catch (error) {
      console.error('Failed to generate report:', error)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-500'
    if (score >= 70) return 'text-yellow-500'
    return 'text-red-500'
  }

  if (loading) {
    return <div className="text-center py-12">Loading compliance data...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Compliance</h1>
        <button className="btn btn-primary flex items-center gap-2">
          <Download size={18} />
          Export Report
        </button>
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
              <circle
                cx="96"
                cy="96"
                r="88"
                stroke="#1e293b"
                strokeWidth="12"
                fill="none"
              />
              <circle
                cx="96"
                cy="96"
                r="88"
                stroke={score?.score >= 90 ? '#22c55e' : score?.score >= 70 ? '#eab308' : '#ef4444'}
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 88}`}
                strokeDashoffset={`${2 * Math.PI * 88 * (1 - score?.score / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <span className={`text-4xl font-bold ${getScoreColor(score?.score)}`}>
                {score?.score || 0}%
              </span>
              <span className="text-gray-400 text-sm">Compliance</span>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{score?.total_devices || 0}</p>
            <p className="text-gray-400 text-sm">Total Devices</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-500">{score?.authorized || 0}</p>
            <p className="text-gray-400 text-sm">Authorized</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-500">{score?.unauthorized || 0}</p>
            <p className="text-gray-400 text-sm">Unauthorized</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-500">{score?.quarantined || 0}</p>
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
          <button
            onClick={() => handleGenerateReport('daily')}
            className="btn btn-primary flex items-center justify-center gap-2"
          >
            <Calendar size={18} />
            Daily Report
          </button>
          <button
            onClick={() => handleGenerateReport('weekly')}
            className="btn btn-primary flex items-center justify-center gap-2"
          >
            <Calendar size={18} />
            Weekly Report
          </button>
          <button
            onClick={() => handleGenerateReport('monthly')}
            className="btn btn-primary flex items-center justify-center gap-2"
          >
            <Calendar size={18} />
            Monthly Report
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
                <p className="text-sm text-gray-400">
                  {new Date(report.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-lg font-bold ${getScoreColor(report.compliance_score)}`}>
                  {report.compliance_score}%
                </span>
                <button className="btn btn-primary flex items-center gap-2">
                  <Download size={16} />
                  View
                </button>
              </div>
            </div>
          ))}
          {reports.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              No reports generated yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Compliance
