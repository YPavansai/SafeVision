import React, { useState, useEffect } from 'react';
import { Video, ShieldAlert, Activity, Play, Grid, Camera, Wifi } from 'lucide-react';
import LiveVideoPlayer from '../components/Monitoring/LiveVideoPlayer';
import api from '../services/api';

export default function LiveMonitoringPage() {
  const [selectedVideo, setSelectedVideo] = useState('construction_1.mp4');
  const [customStreamUrl, setCustomStreamUrl] = useState('');
  const [activeStreamType, setActiveStreamType] = useState('prebuilt'); // 'prebuilt', 'webcam', or 'wireless'
  const [videoList, setVideoList] = useState([
    'construction_1.mp4',
    'construction_2.mp4',
    'helmet_violation.mp4',
    'fire_alert.mp4'
  ]);

  useEffect(() => {
    fetchMediaList();
  }, []);

  const fetchMediaList = async () => {
    try {
      const res = await api.get('/analysis/media/');
      if (res.data.videos && res.data.videos.length > 0) {
        setVideoList(res.data.videos.map(v => v.name));
      }
    } catch (e) {
      console.error('Media list fetch error:', e);
    }
  };

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Live CCTV Safety Monitoring Station</h1>
        <p style={{ color: 'var(--text-dark-secondary)', fontSize: '0.9rem' }}>
          Real-time AI construction site safety inspection: pre-built video feeds, live webcam stream, or IP camera RTSP feed.
        </p>
      </div>

      {/* Main Stream Player & Source Selector */}
      <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1fr', gap: '1.5rem' }}>
        {/* Main Feed Player */}
        <LiveVideoPlayer
          activeStreamType={activeStreamType}
          selectedVideo={activeStreamType === 'prebuilt' ? selectedVideo : ''}
          customStreamUrl={activeStreamType === 'wireless' ? customStreamUrl : ''}
        />

        {/* Monitoring Source Selector Panel */}
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Grid size={18} color="var(--cyan-primary)" /> Monitoring Source
          </h3>

          {/* Source Type Toggle Buttons */}
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              onClick={() => setActiveStreamType('prebuilt')}
              className={activeStreamType === 'prebuilt' ? 'btn-primary' : 'btn-secondary'}
              style={{ flex: 1, padding: '6px', fontSize: '0.75rem', justifyContent: 'center' }}
            >
              Pre-built
            </button>
            <button
              onClick={() => setActiveStreamType('webcam')}
              className={activeStreamType === 'webcam' ? 'btn-primary' : 'btn-secondary'}
              style={{ flex: 1, padding: '6px', fontSize: '0.75rem', justifyContent: 'center' }}
            >
              Live Webcam
            </button>
            <button
              onClick={() => setActiveStreamType('wireless')}
              className={activeStreamType === 'wireless' ? 'btn-primary' : 'btn-secondary'}
              style={{ flex: 1, padding: '6px', fontSize: '0.75rem', justifyContent: 'center' }}
            >
              IP Stream
            </button>
          </div>

          {activeStreamType === 'prebuilt' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {videoList.map((vName) => {
                const isSelected = selectedVideo === vName;
                return (
                  <div
                    key={vName}
                    onClick={() => setSelectedVideo(vName)}
                    className="glass-card-interactive"
                    style={{
                      padding: '12px 14px',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected ? '1px solid var(--cyan-primary)' : '1px solid var(--border-dark)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Video size={16} color={isSelected ? 'var(--cyan-primary)' : 'var(--text-dark-secondary)'} />
                      <span style={{ fontSize: '0.85rem', fontWeight: isSelected ? 700 : 500, fontFamily: 'var(--font-mono)' }}>
                        {vName}
                      </span>
                    </div>
                    {isSelected && <span className="pulse-dot" />}
                  </div>
                );
              })}
            </div>
          )}

          {activeStreamType === 'webcam' && (
            <div style={{ padding: '1rem', background: 'rgba(6, 182, 212, 0.08)', borderRadius: '12px', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cyan-primary)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '6px' }}>
                <Camera size={18} /> Laptop Webcam CCTV
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-secondary)', lineHeight: '1.4' }}>
                Captures real-time camera feed to run YOLO safety detection and ArcFace worker identification.
              </p>
            </div>
          )}

          {activeStreamType === 'wireless' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>
                Wireless Stream / IP Camera URL (RTSP / HTTP)
              </label>
              <input
                type="text"
                placeholder="http://192.168.1.100:8080/video or rtsp://..."
                value={customStreamUrl}
                onChange={(e) => setCustomStreamUrl(e.target.value)}
                className="input-field"
                style={{ fontSize: '0.85rem' }}
              />
              <button
                onClick={() => { if (!customStreamUrl) setCustomStreamUrl('http://192.168.1.100:8080/video'); }}
                className="btn-secondary"
                style={{ padding: '8px', fontSize: '0.8rem', justifyContent: 'center' }}
              >
                <Wifi size={14} /> Connect Stream Feed
              </button>
            </div>
          )}

          <div style={{ marginTop: 'auto', padding: '1rem', background: 'rgba(245, 158, 11, 0.08)', borderRadius: '12px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--amber-primary)', fontWeight: 600, marginBottom: '4px' }}>AI Detection Classes</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-secondary)', lineHeight: '1.4' }}>
              Worker, Helmet, Safety Vest, Gloves, Boots, Fire Hazard, Heavy Crane, Truck.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

