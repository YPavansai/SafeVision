import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, FileText, CheckCircle2, Clock, Activity, Calendar } from 'lucide-react';
import api from '../services/api';

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [reportType, setReportType] = useState('daily_attendance');
  const [fileFormat, setFileFormat] = useState('csv');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const res = await api.get('/reports/');
      setReports(res.data);
    } catch (e) {
      console.error('Reports fetch error:', e);
    }
  };

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/reports/', {
        report_type: reportType,
        file_format: fileFormat
      });
      fetchReports();
      alert(`Report generated successfully! Download URL: ${res.data.download_url}`);
    } catch (err) {
      alert('Failed to generate report: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Safety & Compliance Report Console</h1>
        <p style={{ color: 'var(--text-dark-secondary)', fontSize: '0.9rem' }}>
          Generate exportable CSV, Excel, and PDF documentation for site audits and attendance history.
        </p>
      </div>

      {/* Generator Form */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem' }}>Export New Compliance Report</h3>

        <form onSubmit={handleGenerateReport} style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr', gap: '1.25rem', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)', display: 'block', marginBottom: '6px' }}>Select Report Type</label>
            <select value={reportType} onChange={e => setReportType(e.target.value)} className="input-field">
              <option value="daily_attendance">Daily Attendance Log</option>
              <option value="weekly_summary">Weekly Safety Compliance Report</option>
              <option value="monthly_compliance">Monthly Executive Compliance Audit</option>
              <option value="worker_activity">Worker Shift Activity Timeline</option>
              <option value="violations_export">Violation & Incident Log</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)', display: 'block', marginBottom: '6px' }}>Export Format</label>
            <select value={fileFormat} onChange={e => setFileFormat(e.target.value)} className="input-field">
              <option value="csv">CSV Spreadsheet (.csv)</option>
              <option value="xlsx">Excel Document (.xlsx)</option>
              <option value="pdf">PDF Document (.pdf)</option>
            </select>
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', height: '42px' }}>
            {loading ? <Activity className="animate-spin" size={18} /> : <Download size={18} />}
            <span>{loading ? 'Generating...' : 'Generate & Download Report'}</span>
          </button>
        </form>
      </div>

      {/* Generated Reports Table */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px', overflowX: 'auto' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Generated Audit Reports Log</h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-dark)', color: 'var(--text-dark-muted)', textAlign: 'left' }}>
              <th style={{ padding: '12px' }}>Report Type</th>
              <th style={{ padding: '12px' }}>Format</th>
              <th style={{ padding: '12px' }}>Generated Date</th>
              <th style={{ padding: '12px' }}>Download Link</th>
            </tr>
          </thead>
          <tbody>
            {reports.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
                  No reports generated yet. Select report parameters above to create one.
                </td>
              </tr>
            ) : (
              reports.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid var(--border-dark)' }}>
                  <td style={{ padding: '14px 12px', fontWeight: 600 }}>{r.report_type.replace('_', ' ').toUpperCase()}</td>
                  <td style={{ padding: '14px 12px' }}>
                    <span className="badge badge-amber">{r.file_format.toUpperCase()}</span>
                  </td>
                  <td style={{ padding: '14px 12px', color: 'var(--text-dark-secondary)' }}>
                    {new Date(r.generated_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '14px 12px' }}>
                    <a href={r.file_path} download target="_blank" rel="noreferrer" className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', textDecoration: 'none', display: 'inline-flex' }}>
                      <Download size={14} /> Download File
                    </a>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
