import React, { useState, useEffect } from 'react';
import { Film, Play, Scan, Image as ImageIcon, Video as VideoIcon, Download, X, Activity, Pause } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function MediaLibraryPage() {
  const [media, setMedia] = useState({ videos: [], images: [] });
  const [activeTab, setActiveTab] = useState('videos');
  const [playingVideo, setPlayingVideo] = useState(null);
  const [videoFrameData, setVideoFrameData] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMedia();
  }, []);

  useEffect(() => {
    let interval;
    if (playingVideo && isPlaying) {
      interval = setInterval(() => {
        setCurrentFrame((prev) => {
          const next = (prev + 1) % 60;
          fetchModalFrame(playingVideo.name, next);
          return next;
        });
      }, 250);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [playingVideo, isPlaying]);

  const fetchMedia = async () => {
    try {
      const res = await api.get('/analysis/media/');
      setMedia(res.data);
    } catch (e) {
      console.error('Media fetch error:', e);
    }
  };

  const openVideoModal = (video) => {
    setPlayingVideo(video);
    setIsPlaying(true);
    setCurrentFrame(0);
    fetchModalFrame(video.name, 0);
  };

  const fetchModalFrame = async (videoName, frameNum) => {
    try {
      const res = await api.post('/analysis/video-frame/', {
        video_name: videoName,
        frame_num: frameNum
      });
      setVideoFrameData(res.data);
    } catch (e) {
      console.error('Failed to fetch modal frame:', e);
    }
  };

  const closeVideoModal = () => {
    setPlayingVideo(null);
    setIsPlaying(false);
    setVideoFrameData(null);
  };

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Media Asset Library</h1>
        <p style={{ color: 'var(--text-dark-secondary)', fontSize: '0.9rem' }}>
          Browse stored pre-built construction site videos, inspection images, and processed AI output logs.
        </p>
      </div>

      {/* Tabs Switcher */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border-dark)', paddingBottom: '1rem' }}>
        <button
          onClick={() => setActiveTab('videos')}
          className={activeTab === 'videos' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 18px', fontSize: '0.85rem' }}
        >
          <VideoIcon size={16} /> Construction Videos ({media.videos.length})
        </button>
        <button
          onClick={() => setActiveTab('images')}
          className={activeTab === 'images' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 18px', fontSize: '0.85rem' }}
        >
          <ImageIcon size={16} /> Inspection Photos ({media.images.length})
        </button>
      </div>

      {/* Media Grid */}
      {activeTab === 'videos' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {media.videos.map((v) => (
            <div key={v.name} className="glass-panel glass-card-interactive" style={{ padding: '1.25rem', borderRadius: '18px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(6, 182, 212, 0.15)', color: 'var(--cyan-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <VideoIcon size={20} />
                </div>
                <div>
                  <p style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{v.name}</p>
                  <span className="badge badge-amber">Pre-built Video</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={() => openVideoModal(v)} className="btn-secondary" style={{ flex: 1, justifyContent: 'center', fontSize: '0.8rem' }}>
                  <Play size={14} /> Play Video
                </button>
                <button onClick={() => navigate('/monitoring')} className="btn-primary" style={{ padding: '8px 12px', fontSize: '0.8rem' }}>
                  <Scan size={14} /> CCTV AI
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {media.images.map((img) => (
            <div key={img.name} className="glass-panel glass-card-interactive" style={{ padding: '1.25rem', borderRadius: '18px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--amber-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <ImageIcon size={20} />
                </div>
                <div>
                  <p style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{img.name}</p>
                  <span className="badge badge-cyan">Static Image</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <a href={img.url} target="_blank" rel="noreferrer" className="btn-secondary" style={{ flex: 1, justifyContent: 'center', textDecoration: 'none', fontSize: '0.8rem' }}>
                  View Image
                </a>
                <button onClick={() => navigate('/image-analysis')} className="btn-primary" style={{ padding: '8px 12px', fontSize: '0.8rem' }}>
                  <Scan size={14} /> Analyze
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Interactive Video Player Modal */}
      {playingVideo && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100
        }}>
          <div className="glass-panel" style={{ width: '680px', padding: '1.75rem', borderRadius: '24px', position: 'relative' }}>
            <button
              onClick={closeVideoModal}
              style={{ position: 'absolute', right: '1.5rem', top: '1.5rem', background: 'none', border: 'none', color: 'var(--text-dark-muted)', cursor: 'pointer' }}
            >
              <X size={22} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
              <VideoIcon color="var(--cyan-primary)" size={24} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                {playingVideo.name}
              </h3>
            </div>

            {/* Video Frame Display Box */}
            <div style={{
              width: '100%',
              height: '360px',
              backgroundColor: '#050811',
              borderRadius: '16px',
              overflow: 'hidden',
              border: '1px solid var(--border-dark)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}>
              {videoFrameData?.frame_b64 ? (
                <img
                  src={videoFrameData.frame_b64}
                  alt="Video Frame"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              ) : (
                <div style={{ color: 'var(--text-dark-muted)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                  <Activity className="animate-spin" size={32} color="var(--cyan-primary)" />
                  <p>Loading AI Stream Video Frames...</p>
                </div>
              )}

              {/* Controls Overlay */}
              <div style={{ position: 'absolute', bottom: '1rem', left: '1rem', right: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(15, 23, 42, 0.88)', padding: '8px 14px', borderRadius: '10px', border: '1px solid var(--border-dark)' }}>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="btn-primary"
                  style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                  <span>{isPlaying ? 'Pause' : 'Play'}</span>
                </button>

                <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dark-secondary)' }}>
                  Frame: {currentFrame}/60
                </span>

                <button
                  onClick={() => { closeVideoModal(); navigate('/monitoring'); }}
                  className="btn-secondary"
                  style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                >
                  <Scan size={14} /> Open in Live CCTV Station
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

