import React, { useState, useEffect } from 'react';
import { Scan, Upload, Download, CheckCircle2, AlertTriangle, Image as ImageIcon, Activity, Info, ShieldAlert, AlertCircle } from 'lucide-react';
import api, { resolveMediaUrl } from '../services/api';

export default function ImageAnalysisPage() {
  const [selectedImageName, setSelectedImageName] = useState('real_construction_worker.jpg');
  const [uploadFile, setUploadFile] = useState(null);
  const [inputPreviewUrl, setInputPreviewUrl] = useState(resolveMediaUrl('/media/images/real_construction_worker.jpg'));
  const [fileError, setFileError] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const sampleImages = [
    { name: 'real_construction_worker.jpg', label: 'Real Site Photo (Worker on Site)' },
    { name: 'worker_with_helmet.jpg', label: 'Synthetic: Worker (Helmet & Vest)' },
    { name: 'worker_without_helmet.jpg', label: 'Synthetic: No Helmet' },
    { name: 'worker_without_vest.jpg', label: 'Synthetic: No Vest' },
    { name: 'fire.jpg', label: 'Synthetic: Fire Scene' },
  ];

  // Revoke object URL on unmount to avoid memory leak
  useEffect(() => {
    return () => {
      if (inputPreviewUrl && inputPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(inputPreviewUrl);
      }
    };
  }, [inputPreviewUrl]);

  const handleSelectSample = (name) => {
    setSelectedImageName(name);
    setUploadFile(null);
    setFileError('');
    setAnalysisResult(null);
    setInputPreviewUrl(resolveMediaUrl(`/media/images/${name}`));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate extension
    const validExtensions = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp'];
    if (!validExtensions.includes(file.type.toLowerCase())) {
      setFileError('Invalid file format. Please upload JPG, PNG, WEBP, or BMP image.');
      return;
    }

    // Validate size (15MB)
    if (file.size > 15 * 1024 * 1024) {
      setFileError('File size exceeds the 15MB maximum limit.');
      return;
    }

    setFileError('');
    setSelectedImageName('');
    setUploadFile(file);
    setAnalysisResult(null);

    const objectUrl = URL.createObjectURL(file);
    setInputPreviewUrl(objectUrl);
  };

  const handleRunAnalysis = async () => {
    if (!uploadFile && !selectedImageName) {
      setFileError('Please select a sample image or upload a photo to analyze.');
      return;
    }

    setLoading(true);
    setFileError('');
    setAnalysisResult(null);

    try {
      let res;
      if (uploadFile) {
        const formData = new FormData();
        formData.append('image', uploadFile);
        res = await api.post('/analysis/image/', formData);
      } else {
        res = await api.post('/analysis/image/', { image_name: selectedImageName });
      }
      setAnalysisResult(res.data);
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Image analysis request failed';
      setFileError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>AI Static Image Analysis Inspection</h1>
        <p style={{ color: 'var(--text-dark-secondary)', fontSize: '0.9rem' }}>
          Select or upload construction photos to execute YOLOv8 object detection, bounding box extraction, and confidence scoring.
        </p>
      </div>

      {/* Control Panel */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Choose Input Sample Image or Upload</h3>

        {/* Sample Image Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {sampleImages.map((item) => {
            const isSelected = selectedImageName === item.name && !uploadFile;
            return (
              <div
                key={item.name}
                onClick={() => handleSelectSample(item.name)}
                className="glass-card-interactive"
                style={{
                  padding: '12px',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  background: isSelected ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: isSelected ? '1px solid var(--cyan-primary)' : '1px solid var(--border-dark)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <ImageIcon size={20} color={isSelected ? 'var(--cyan-primary)' : 'var(--text-dark-muted)'} />
                <div>
                  <p style={{ fontSize: '0.85rem', fontWeight: 700 }}>{item.name}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-secondary)' }}>{item.label}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* File Upload Option */}
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp,.bmp,image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              className="input-field"
              style={{ padding: '8px' }}
            />
          </div>

          <button onClick={handleRunAnalysis} className="btn-primary" disabled={loading} style={{ padding: '10px 24px', minWidth: '220px', justifyContent: 'center' }}>
            {loading ? <Activity className="animate-spin" size={18} /> : <Scan size={18} />}
            <span>{loading ? 'Running AI Inference...' : 'Execute YOLOv8 Detection'}</span>
          </button>
        </div>

        {/* Inline Error Notification */}
        {fileError && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.12)', border: '1px solid rgba(244, 63, 94, 0.3)', color: 'var(--rose-primary)', fontSize: '0.85rem' }}>
            <AlertCircle size={18} />
            <span>{fileError}</span>
          </div>
        )}
      </div>

      {/* Input Preview Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: analysisResult ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        {/* Source Image Card */}
        <div className="glass-panel" style={{ padding: '1.25rem', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Source Input Image</h3>
            <span className="badge badge-cyan">{uploadFile ? uploadFile.name : selectedImageName}</span>
          </div>
          <div style={{ width: '100%', height: '360px', backgroundColor: '#050811', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {inputPreviewUrl ? (
              <img
                src={inputPreviewUrl}
                alt="Source Preview"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : (
              <div style={{ color: 'var(--text-dark-muted)', fontSize: '0.85rem' }}>No image selected</div>
            )}
          </div>
        </div>

        {/* AI Annotated Output Image */}
        {analysisResult && (
          <div className="glass-panel" style={{ padding: '1.25rem', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>AI Bounding Box Output Image</h3>
              <a
                href={resolveMediaUrl(analysisResult.output_url)}
                download
                target="_blank"
                rel="noreferrer"
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: '0.8rem', textDecoration: 'none' }}
              >
                <Download size={14} /> Download Annotated
              </a>
            </div>

            <div style={{ width: '100%', height: '360px', backgroundColor: '#050811', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src={resolveMediaUrl(analysisResult.output_url)}
                alt="YOLO Output"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Detections & Confidence Breakdown */}
      {analysisResult && (
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Detections & Compliance Analytics</h3>
            <span className="badge badge-emerald">Inference Success</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px', border: '1px solid var(--border-dark)' }}>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-muted)' }}>Site Safety Score</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 800, color: analysisResult.safety_score >= 80 ? 'var(--emerald-primary)' : 'var(--amber-primary)' }}>
                {analysisResult.safety_score}/100
              </p>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px', border: '1px solid var(--border-dark)' }}>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-muted)' }}>Total Objects Detected</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--cyan-primary)' }}>{analysisResult.total_objects}</p>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px', border: '1px solid var(--border-dark)' }}>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dark-muted)' }}>Confirmed Violations</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 800, color: analysisResult.violations.length > 0 ? 'var(--rose-primary)' : 'var(--emerald-primary)' }}>
                {analysisResult.violations.length}
              </p>
            </div>
          </div>

          {/* Detections Table */}
          {analysisResult.detections.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border-dark)' }}>
              <Info size={28} color="var(--text-dark-muted)" style={{ margin: '0 auto 8px' }} />
              <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>Zero Target Objects Detected</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-dark-secondary)', marginTop: '4px' }}>
                The loaded YOLO model did not detect any objects meeting the confidence threshold.
              </p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-dark)', color: 'var(--text-dark-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Class Label</th>
                    <th style={{ padding: '10px' }}>Confidence</th>
                    <th style={{ padding: '10px' }}>Bounding Box [X, Y, W, H]</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResult.detections.map((det, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-dark)' }}>
                      <td style={{ padding: '10px', fontWeight: 700, color: det.label === 'Worker' ? 'var(--cyan-primary)' : '#ffffff' }}>
                        {det.label}
                      </td>
                      <td style={{ padding: '10px' }}>
                        <span className={`badge ${det.confidence >= 70 ? 'badge-emerald' : 'badge-amber'}`}>
                          {det.confidence}%
                        </span>
                      </td>
                      <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-dark-secondary)' }}>
                        [{det.bbox.join(', ')}]
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Violations List */}
          {analysisResult.violations.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--rose-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={16} /> Identified Safety Hazards
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {analysisResult.violations.map((v, i) => (
                  <span key={i} className="badge badge-rose" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                    {v.type} ({v.severity} Severity)
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
