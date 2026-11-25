import React, { useState, useEffect } from 'react';
import { Sun, Moon, Bell, Search, ShieldAlert, User, Play, Pause, Activity } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import { useDemo } from '../../context/DemoContext';
import api from '../../services/api';

export default function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const { isDemoActive, toggleDemo, currentStepText } = useDemo();
  const [unreadAlerts, setUnreadAlerts] = useState(2);

  useEffect(() => {
    fetchAlertCount();
  }, []);

  const fetchAlertCount = async () => {
    try {
      const res = await api.get('/violations/');
      const pending = res.data.filter(v => v.status === 'Pending').length;
      setUnreadAlerts(pending);
    } catch (e) {
      console.error('Navbar alert count fetch error:', e);
    }
  };

  return (
    <header style={{
      height: '70px',
      backgroundColor: 'var(--bg-dark-secondary)',
      borderBottom: '1px solid var(--border-dark)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      {/* Search & Demo Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ position: 'relative', width: '280px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dark-muted)' }} />
          <input
            type="text"
            placeholder="Search workers, IDs, alerts..."
            className="input-field"
            style={{ paddingLeft: '38px', height: '38px', fontSize: '0.85rem' }}
          />
        </div>

        {isDemoActive && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: '9999px',
            background: 'rgba(6, 182, 212, 0.15)',
            border: '1px solid var(--cyan-primary)',
            color: 'var(--cyan-primary)',
            fontSize: '0.8rem',
            fontWeight: 700
          }}>
            <span className="pulse-dot" />
            <span>DEMO MODE ● RUNNING: <strong style={{ color: '#ffffff' }}>{currentStepText}</strong></span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Demo Mode Toggle Button */}
        <button
          onClick={toggleDemo}
          className={isDemoActive ? 'btn-danger' : 'btn-primary'}
          style={{ padding: '6px 14px', fontSize: '0.82rem' }}
        >
          {isDemoActive ? <Pause size={14} /> : <Play size={14} />}
          <span>{isDemoActive ? 'STOP DEMO' : 'START DEMO MODE'}</span>
        </button>

        {/* Risk Alerts Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: '9999px',
          background: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: 'var(--rose-primary)',
          fontSize: '0.8rem',
          fontWeight: 700
        }}>
          <ShieldAlert size={16} />
          <span>{unreadAlerts} Active Risk Alerts</span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            border: '1px solid var(--border-dark)',
            background: 'var(--bg-dark-card)',
            color: 'var(--text-dark-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
          title="Toggle Dark/Light Mode"
        >
          {theme === 'dark' ? <Sun size={18} color="#f59e0b" /> : <Moon size={18} color="#06b6d4" />}
        </button>

        {/* Admin Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '0.5rem', borderLeft: '1px solid var(--border-dark)' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontWeight: 700
          }}>
            <User size={18} />
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-dark-primary)' }}>
              {user?.first_name || 'Pavan Sai'}
            </p>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-dark-muted)' }}>Site Safety Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
}
