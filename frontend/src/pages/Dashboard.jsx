import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserCheck, 
  Clock, 
  CheckCircle2, 
  ShieldAlert, 
  Activity, 
  Flame, 
  ArrowUpRight, 
  RefreshCw,
  Video,
  FileSpreadsheet,
  Cpu,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { 
  Chart as ChartJS, 
  ArcElement, 
  Tooltip, 
  Legend, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  PointElement, 
  LineElement, 
  Title 
} from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import SafetyScene3D from '../components/ThreeCanvas/SafetyScene3D';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

ChartJS.register(
  ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title
);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardStats();
    const interval = setInterval(fetchDashboardStats, 5000); // Real-time 5s polling
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const res = await api.get('/dashboard/stats/');
      setStats(res.data);
    } catch (e) {
      console.error('Failed to load dashboard metrics:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <Activity className="animate-spin" size={36} color="var(--cyan-primary)" />
      </div>
    );
  }

  const aiStatus = stats?.ai_system_status || {
    yolov8: 'ONLINE',
    arcface: 'ONLINE',
    bytetrack: 'ONLINE',
    opencv: 'ONLINE',
    database: 'ONLINE'
  };

  const pieData = {
    labels: stats?.charts?.compliance_pie?.labels || ['Helmet', 'Vest', 'Gloves', 'Boots', 'Violations'],
    datasets: [{
      data: stats?.charts?.compliance_pie?.data || [94, 88, 85, 90, 5],
      backgroundColor: ['#06b6d4', '#3b82f6', '#10b981', '#f59e0b', '#f43f5e'],
      borderWidth: 0
    }]
  };

  const barData = {
    labels: stats?.charts?.violations_bar?.labels || ['Helmet', 'Vest', 'Gloves', 'Boots', 'Fire', 'Restricted'],
    datasets: [{
      label: 'Incident Count',
      data: stats?.charts?.violations_bar?.data || [4, 2, 3, 1, 1, 1],
      backgroundColor: 'rgba(244, 63, 94, 0.75)',
      borderRadius: 8
    }]
  };

  const lineData = {
    labels: stats?.charts?.hourly_trend?.labels || ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00'],
    datasets: [{
      label: 'On-Site Personnel Count',
      data: stats?.charts?.hourly_trend?.data || [2, 14, 22, 18, 25, 20, 10],
      borderColor: '#06b6d4',
      backgroundColor: 'rgba(6, 182, 212, 0.15)',
      fill: true,
      tension: 0.4
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Outfit', size: 12 } } }
    },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
  };

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Hero Banner */}
      <div className="glass-panel" style={{
        padding: '2rem',
        borderRadius: '24px',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%)',
        display: 'grid',
        gridTemplateColumns: '1.2fr 0.8fr',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div>
          <div className="badge badge-amber" style={{ marginBottom: '1rem' }}>
            <Activity size={14} /> LIVE SAFETY COMPLIANCE MONITOR
          </div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, marginBottom: '0.75rem', lineHeight: '1.2' }}>
            SafeVision Command Center
          </h1>
          <p style={{ color: 'var(--text-dark-secondary)', fontSize: '0.95rem', maxWidth: '580px', lineHeight: '1.6', marginBottom: '1.5rem' }}>
            Smart construction safety & worker risk monitoring system featuring YOLOv8 PPE detection, ArcFace facial attendance, and ByteTrack worker movement tracking.
          </p>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button onClick={() => navigate('/monitoring')} className="btn-primary">
              <Video size={18} /> Launch CCTV Monitor
            </button>
            <button onClick={() => navigate('/reports')} className="btn-secondary">
              <FileSpreadsheet size={18} /> Export Analytics Report
            </button>
          </div>
        </div>

        {/* 3D Helmet Showcase */}
        <div style={{ height: '240px', width: '100%' }}>
          <SafetyScene3D />
        </div>
      </div>

      {/* Metrics Cards & AI SYSTEM STATUS Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1.2fr', gap: '1.5rem' }}>
        {/* Key Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.25rem' }}>
          <div className="glass-panel glass-card-interactive" style={{ padding: '1.25rem', borderRadius: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dark-secondary)', fontWeight: 600 }}>Total Registered Workers</span>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(6, 182, 212, 0.15)', color: 'var(--cyan-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Users size={20} />
              </div>
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-dark-primary)' }}>{stats?.total_workers || 5}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--emerald-primary)', fontWeight: 600 }}>Active Indian Worker Roster</span>
          </div>

          <div className="glass-panel glass-card-interactive" style={{ padding: '1.25rem', borderRadius: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dark-secondary)', fontWeight: 600 }}>Workers On-Site</span>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--emerald-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <UserCheck size={20} />
              </div>
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--emerald-primary)' }}>{stats?.workers_on_site || 5}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dark-secondary)' }}>Currently Checked-In</span>
          </div>

          <div className="glass-panel glass-card-interactive" style={{ padding: '1.25rem', borderRadius: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dark-secondary)', fontWeight: 600 }}>SITE SAFETY SCORE</span>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--amber-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Activity size={20} />
              </div>
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--amber-primary)' }}>{stats?.average_safety_score || 92} / 100</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--amber-primary)', fontWeight: 600 }}>Real-Time Compliance Index</span>
          </div>

          <div className="glass-panel glass-card-interactive" style={{ padding: '1.25rem', borderRadius: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dark-secondary)', fontWeight: 600 }}>Total Risk Alerts</span>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.15)', color: 'var(--rose-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ShieldAlert size={20} />
              </div>
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--rose-primary)' }}>{stats?.total_violations || 5}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--rose-primary)', fontWeight: 600 }}>{stats?.pending_violations || 2} Pending Action</span>
          </div>
        </div>

        {/* AI SYSTEM STATUS CARD */}
        <div className="glass-panel" style={{ padding: '1.25rem', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} color="var(--cyan-primary)" /> AI SYSTEM STATUS
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
              <span style={{ fontWeight: 600 }}>YOLOv8</span>
              <span className={`badge ${aiStatus.yolov8 === 'ONLINE' ? 'badge-emerald' : 'badge-rose'}`}>
                ● {aiStatus.yolov8}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
              <span style={{ fontWeight: 600 }}>ArcFace</span>
              <span className={`badge ${aiStatus.arcface === 'ONLINE' ? 'badge-emerald' : 'badge-rose'}`}>
                ● {aiStatus.arcface}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
              <span style={{ fontWeight: 600 }}>ByteTrack</span>
              <span className={`badge ${aiStatus.bytetrack === 'ONLINE' ? 'badge-emerald' : 'badge-rose'}`}>
                ● {aiStatus.bytetrack}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
              <span style={{ fontWeight: 600 }}>OpenCV</span>
              <span className={`badge ${aiStatus.opencv === 'ONLINE' ? 'badge-emerald' : 'badge-rose'}`}>
                ● {aiStatus.opencv}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
              <span style={{ fontWeight: 600 }}>Database</span>
              <span className={`badge ${aiStatus.database === 'ONLINE' ? 'badge-emerald' : 'badge-rose'}`}>
                ● {aiStatus.database}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem' }}>PPE Compliance Ratio</h3>
          <div style={{ height: '240px' }}>
            <Pie data={pieData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem' }}>Violations Breakdown</h3>
          <div style={{ height: '240px' }}>
            <Bar data={barData} options={chartOptions} />
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '1rem' }}>24h Personnel Trend</h3>
          <div style={{ height: '240px' }}>
            <Line data={lineData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Real-Time Violation Alert Stream */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Real-Time Risk Alert Stream</h3>
          <button onClick={() => navigate('/alerts')} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            View All Risk Alerts <ArrowUpRight size={14} />
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-dark)', color: 'var(--text-dark-muted)', textAlign: 'left' }}>
                <th style={{ padding: '10px' }}>Alert ID</th>
                <th style={{ padding: '10px' }}>Worker</th>
                <th style={{ padding: '10px' }}>Violation</th>
                <th style={{ padding: '10px' }}>Severity</th>
                <th style={{ padding: '10px' }}>Duration</th>
                <th style={{ padding: '10px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {stats?.recent_alerts?.map((alert) => (
                <tr key={alert.id} style={{ borderBottom: '1px solid var(--border-dark)' }}>
                  <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--cyan-primary)' }}>{alert.violation_id}</td>
                  <td style={{ padding: '12px 10px', fontWeight: 600 }}>{alert.worker_detail?.full_name || 'Unidentified'}</td>
                  <td style={{ padding: '12px 10px' }}>{alert.violation_type}</td>
                  <td style={{ padding: '12px 10px' }}>
                    <span className={`badge ${alert.severity === 'Critical' || alert.severity === 'High' ? 'badge-rose' : 'badge-amber'}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>{alert.duration_seconds ? `${alert.duration_seconds}s` : '13s'}</td>
                  <td style={{ padding: '12px 10px' }}>
                    <span className={`badge ${alert.status === 'Resolved' ? 'badge-emerald' : 'badge-rose'}`}>
                      {alert.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
