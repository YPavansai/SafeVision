import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Users, 
  UserCheck, 
  Video, 
  Scan, 
  BellRing, 
  Film, 
  FileSpreadsheet, 
  LogOut 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const { logout, user } = useAuth();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/workers', label: 'Worker Registry', icon: Users },
    { path: '/attendance', label: 'Face Attendance', icon: UserCheck },
    { path: '/monitoring', label: 'Live CCTV Monitor', icon: Video },
    { path: '/image-analysis', label: 'Image Analysis AI', icon: Scan },
    { path: '/alerts', label: 'Violations & Risk', icon: BellRing },
    { path: '/media-library', label: 'Media Library', icon: Film },
    { path: '/reports', label: 'Compliance Reports', icon: FileSpreadsheet },
  ];

  return (
    <aside style={{
      width: '260px',
      backgroundColor: 'var(--bg-dark-secondary)',
      borderRight: '1px solid var(--border-dark)',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem 1rem',
      height: '100vh',
      position: 'sticky',
      top: 0,
      zIndex: 50
    }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 0.5rem 1.5rem 0.5rem', borderBottom: '1px solid var(--border-dark)' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #f59e0b 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px rgba(245, 158, 11, 0.4)'
        }}>
          <ShieldCheck size={26} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #ffffff 0%, #94a3b8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            SafeVision
          </h1>
          <span style={{ fontSize: '0.7rem', color: 'var(--amber-primary)', fontWeight: 600, letterSpacing: '0.05em' }}>
            SAFETY COMPLIANCE
          </span>
        </div>
      </div>

      {/* Admin Role Status Card */}
      <div style={{
        margin: '1.25rem 0',
        padding: '0.85rem',
        borderRadius: '12px',
        background: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.2)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        <div className="pulse-dot" />
        <div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-secondary)', fontWeight: 500 }}>Logged as Admin</p>
          <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--amber-primary)' }}>{user?.first_name || user?.username || 'Administrator'}</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, overflowY: 'auto' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: '10px',
                textDecoration: 'none',
                fontSize: '0.9rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--text-dark-secondary)',
                background: isActive ? 'linear-gradient(90deg, rgba(6, 182, 212, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--cyan-primary)' : '3px solid transparent',
                transition: 'all 0.2s ease'
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Logout Action */}
      <button
        onClick={logout}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '10px 14px',
          borderRadius: '10px',
          border: '1px solid var(--border-dark)',
          background: 'rgba(244, 63, 94, 0.08)',
          color: 'var(--rose-primary)',
          cursor: 'pointer',
          fontWeight: 600,
          fontSize: '0.88rem',
          marginTop: 'auto',
          transition: 'all 0.2s ease'
        }}
      >
        <LogOut size={18} />
        <span>Secure Logout</span>
      </button>
    </aside>
  );
}
