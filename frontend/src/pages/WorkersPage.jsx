import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  Search, 
  Camera, 
  Edit, 
  Trash2, 
  Activity, 
  ShieldCheck, 
  Clock, 
  AlertTriangle,
  X,
  Phone,
  Briefcase,
  Building,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import api from '../services/api';

export default function WorkersPage() {
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editWorkerData, setEditWorkerData] = useState(null);
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [timelineData, setTimelineData] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    worker_id: '',
    full_name: '',
    phone_number: '',
    role: 'Laborer',
    department: 'Civil',
    joining_date: new Date().toISOString().split('T')[0],
  });
  const [photoFile, setPhotoFile] = useState(null);

  useEffect(() => {
    fetchWorkers();
  }, []);

  const fetchWorkers = async () => {
    try {
      const res = await api.get('/workers/');
      setWorkers(res.data);
    } catch (e) {
      console.error('Failed to fetch workers:', e);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (text, type = 'success') => {
    setActionMessage({ text, type });
    setTimeout(() => setActionMessage(null), 5000);
  };

  const handleCreateWorker = async (e) => {
    e.preventDefault();

    // Check duplicate ID
    const exists = workers.some(w => w.worker_id.toLowerCase() === formData.worker_id.trim().toLowerCase());
    if (exists) {
      alert(`Worker ID '${formData.worker_id}' is already registered. Please use a unique ID.`);
      return;
    }

    // Validate phone number
    if (formData.phone_number.trim().length < 7) {
      alert('Please enter a valid phone number with at least 7 digits.');
      return;
    }

    try {
      const payload = new FormData();
      Object.keys(formData).forEach(key => payload.append(key, formData[key].trim()));
      if (photoFile) {
        payload.append('photo', photoFile);
      }

      const res = await api.post('/workers/', payload);

      // Automatically register face if photo provided
      let faceMsg = '';
      if (photoFile) {
        const facePayload = new FormData();
        facePayload.append('photo', photoFile);
        try {
          await api.post(`/workers/${res.data.id}/register_face/`, facePayload);
          faceMsg = ' Biometric face embedding registered.';
        } catch (faceErr) {
          faceMsg = ' Worker saved, but no clear face was detected in photo. Biometrics can be enrolled later.';
        }
      }

      setShowAddModal(false);
      fetchWorkers();
      setFormData({
        worker_id: '',
        full_name: '',
        phone_number: '',
        role: 'Laborer',
        department: 'Civil',
        joining_date: new Date().toISOString().split('T')[0],
      });
      setPhotoFile(null);
      showNotification(`Worker ${res.data.full_name} created successfully.${faceMsg}`, 'success');
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : err.message;
      alert('Error saving worker: ' + msg);
    }
  };

  const handleOpenEdit = (worker) => {
    setEditWorkerData({
      id: worker.id,
      worker_id: worker.worker_id,
      full_name: worker.full_name,
      phone_number: worker.phone_number,
      role: worker.role,
      department: worker.department,
      safety_score: worker.safety_score,
      is_active: worker.is_active
    });
    setShowEditModal(true);
  };

  const handleUpdateWorker = async (e) => {
    e.preventDefault();
    if (!editWorkerData) return;

    try {
      await api.patch(`/workers/${editWorkerData.id}/`, {
        full_name: editWorkerData.full_name,
        phone_number: editWorkerData.phone_number,
        role: editWorkerData.role,
        department: editWorkerData.department,
        safety_score: Number(editWorkerData.safety_score),
        is_active: Boolean(editWorkerData.is_active)
      });
      setShowEditModal(false);
      fetchWorkers();
      showNotification(`Worker ${editWorkerData.full_name} updated successfully.`, 'success');
    } catch (err) {
      alert('Failed to update worker: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleDeleteWorker = async (id) => {
    if (window.confirm('Are you sure you want to remove this worker record?')) {
      try {
        await api.delete(`/workers/${id}/`);
        fetchWorkers();
        showNotification('Worker record removed.', 'info');
      } catch (e) {
        alert('Failed to delete worker');
      }
    }
  };

  const handleViewTimeline = async (worker) => {
    setSelectedWorker(worker);
    try {
      const res = await api.get(`/workers/${worker.id}/timeline/`);
      setTimelineData(res.data);
    } catch (e) {
      console.error('Timeline fetch error:', e);
    }
  };

  const filteredWorkers = workers.filter(w =>
    w.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    w.worker_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    w.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Worker Safety & Compliance Registry</h1>
          <p style={{ color: 'var(--text-dark-secondary)', fontSize: '0.9rem' }}>
            Manage worker IDs, roles, departments, ArcFace biometric face registration, and safety scores.
          </p>
        </div>

        <button onClick={() => setShowAddModal(true)} className="btn-primary">
          <UserPlus size={18} /> Register New Worker
        </button>
      </div>

      {/* Global Notification Banner */}
      {actionMessage && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: actionMessage.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(6, 182, 212, 0.15)',
          border: actionMessage.type === 'success' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(6, 182, 212, 0.3)',
          color: actionMessage.type === 'success' ? 'var(--emerald-primary)' : 'var(--cyan-primary)',
          fontSize: '0.85rem',
          fontWeight: 600
        }}>
          {actionMessage.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="glass-panel" style={{ padding: '1rem', borderRadius: '16px', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dark-muted)' }} />
          <input
            type="text"
            placeholder="Search workers by Name, Worker ID, or Department..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field"
            style={{ paddingLeft: '42px' }}
          />
        </div>
      </div>

      {/* Workers Table */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '20px', overflowX: 'auto' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}><Activity className="animate-spin" size={32} color="var(--cyan-primary)" /></div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-dark)', color: 'var(--text-dark-muted)', textAlign: 'left' }}>
                <th style={{ padding: '12px' }}>Worker ID</th>
                <th style={{ padding: '12px' }}>Full Name</th>
                <th style={{ padding: '12px' }}>Role</th>
                <th style={{ padding: '12px' }}>Department</th>
                <th style={{ padding: '12px' }}>Safety Score</th>
                <th style={{ padding: '12px' }}>Status</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredWorkers.map((w) => (
                <tr key={w.id} style={{ borderBottom: '1px solid var(--border-dark)' }}>
                  <td style={{ padding: '14px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan-primary)' }}>{w.worker_id}</td>
                  <td style={{ padding: '14px 12px', fontWeight: 600 }}>{w.full_name}</td>
                  <td style={{ padding: '14px 12px', color: 'var(--text-dark-secondary)' }}>{w.role}</td>
                  <td style={{ padding: '14px 12px', color: 'var(--text-dark-secondary)' }}>{w.department}</td>
                  <td style={{ padding: '14px 12px' }}>
                    <span className={`badge ${w.safety_score >= 90 ? 'badge-emerald' : w.safety_score >= 75 ? 'badge-amber' : 'badge-rose'}`}>
                      {w.safety_score}/100
                    </span>
                  </td>
                  <td style={{ padding: '14px 12px' }}>
                    <span className="badge badge-cyan">{w.is_active ? 'Active' : 'Inactive'}</span>
                  </td>
                  <td style={{ padding: '14px 12px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                      <button onClick={() => handleOpenEdit(w)} className="btn-secondary" title="Edit Worker" style={{ padding: '6px 10px', fontSize: '0.8rem' }}>
                        <Edit size={14} />
                      </button>
                      <button onClick={() => handleViewTimeline(w)} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                        <Clock size={14} /> Timeline
                      </button>
                      <button onClick={() => handleDeleteWorker(w.id)} style={{ background: 'none', border: 'none', color: 'var(--rose-primary)', cursor: 'pointer', padding: '4px' }}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add Worker Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass-panel" style={{ width: '500px', padding: '2rem', borderRadius: '20px', position: 'relative' }}>
            <button onClick={() => setShowAddModal(false)} style={{ position: 'absolute', right: '1.5rem', top: '1.5rem', background: 'none', border: 'none', color: 'var(--text-dark-muted)', cursor: 'pointer' }}>
              <X size={20} />
            </button>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem' }}>Register Worker & Face Profile</h2>

            <form onSubmit={handleCreateWorker} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Worker ID (e.g. W-005)</label>
                <input type="text" value={formData.worker_id} onChange={e => setFormData({ ...formData, worker_id: e.target.value })} className="input-field" required />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Full Name</label>
                <input type="text" value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} className="input-field" required />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Phone Number</label>
                  <input type="text" value={formData.phone_number} onChange={e => setFormData({ ...formData, phone_number: e.target.value })} className="input-field" required />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Role</label>
                  <select value={formData.role} onChange={e => setFormData({ ...formData, role: e.target.value })} className="input-field">
                    <option value="Laborer">Laborer</option>
                    <option value="Supervisor">Supervisor</option>
                    <option value="Engineer">Engineer</option>
                    <option value="Electrician">Electrician</option>
                    <option value="Operator">Operator</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Department</label>
                  <select value={formData.department} onChange={e => setFormData({ ...formData, department: e.target.value })} className="input-field">
                    <option value="Civil">Civil</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Mechanical">Mechanical</option>
                    <option value="Safety">Safety</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Joining Date</label>
                  <input type="date" value={formData.joining_date} onChange={e => setFormData({ ...formData, joining_date: e.target.value })} className="input-field" required />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Worker Photo (For ArcFace Embedding Registration)</label>
                <input type="file" accept="image/*" onChange={e => setPhotoFile(e.target.files[0])} className="input-field" style={{ padding: '6px' }} />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary" style={{ flex: 1 }}>Cancel</button>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Save & Register Face</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Worker Modal */}
      {showEditModal && editWorkerData && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass-panel" style={{ width: '500px', padding: '2rem', borderRadius: '20px', position: 'relative' }}>
            <button onClick={() => setShowEditModal(false)} style={{ position: 'absolute', right: '1.5rem', top: '1.5rem', background: 'none', border: 'none', color: 'var(--text-dark-muted)', cursor: 'pointer' }}>
              <X size={20} />
            </button>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem' }}>Edit Worker Profile ({editWorkerData.worker_id})</h2>

            <form onSubmit={handleUpdateWorker} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Full Name</label>
                <input
                  type="text"
                  value={editWorkerData.full_name}
                  onChange={e => setEditWorkerData({ ...editWorkerData, full_name: e.target.value })}
                  className="input-field"
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Phone Number</label>
                  <input
                    type="text"
                    value={editWorkerData.phone_number}
                    onChange={e => setEditWorkerData({ ...editWorkerData, phone_number: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Role</label>
                  <select
                    value={editWorkerData.role}
                    onChange={e => setEditWorkerData({ ...editWorkerData, role: e.target.value })}
                    className="input-field"
                  >
                    <option value="Laborer">Laborer</option>
                    <option value="Supervisor">Supervisor</option>
                    <option value="Engineer">Engineer</option>
                    <option value="Electrician">Electrician</option>
                    <option value="Operator">Operator</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Department</label>
                  <select
                    value={editWorkerData.department}
                    onChange={e => setEditWorkerData({ ...editWorkerData, department: e.target.value })}
                    className="input-field"
                  >
                    <option value="Civil">Civil</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Mechanical">Mechanical</option>
                    <option value="Safety">Safety</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-secondary)' }}>Safety Score (0-100)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editWorkerData.safety_score}
                    onChange={e => setEditWorkerData({ ...editWorkerData, safety_score: e.target.value })}
                    className="input-field"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="is_active"
                  checked={editWorkerData.is_active}
                  onChange={e => setEditWorkerData({ ...editWorkerData, is_active: e.target.checked })}
                  style={{ width: '18px', height: '18px' }}
                />
                <label htmlFor="is_active" style={{ fontSize: '0.85rem', fontWeight: 600 }}>Active Worker Status</label>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowEditModal(false)} className="btn-secondary" style={{ flex: 1 }}>Cancel</button>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Update Worker</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Worker Timeline Detail Modal */}
      {selectedWorker && timelineData && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass-panel" style={{ width: '560px', padding: '2rem', borderRadius: '20px', position: 'relative' }}>
            <button onClick={() => setSelectedWorker(null)} style={{ position: 'absolute', right: '1.5rem', top: '1.5rem', background: 'none', border: 'none', color: 'var(--text-dark-muted)', cursor: 'pointer' }}>
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ width: '50px', height: '50px', borderRadius: '50%', background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '1.2rem', color: '#ffffff' }}>
                {selectedWorker.full_name[0]}
              </div>
              <div>
                <h2 style={{ fontSize: '1.3rem', fontWeight: 800 }}>{selectedWorker.full_name}</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-dark-secondary)' }}>ID: {selectedWorker.worker_id} | {selectedWorker.role} ({selectedWorker.department})</p>
              </div>
            </div>

            {/* Safety Score Calculation Box */}
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px', border: '1px solid var(--border-dark)', marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--amber-primary)' }}>Safety Score Breakdown (100 Max)</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
                <div>Helmet Check: <strong style={{ color: 'var(--emerald-primary)' }}>✔ 25 pts</strong></div>
                <div>Safety Vest Check: <strong style={{ color: 'var(--emerald-primary)' }}>✔ 25 pts</strong></div>
                <div>Gloves Check: <strong style={{ color: 'var(--emerald-primary)' }}>✔ 25 pts</strong></div>
                <div>Boots Check: <strong style={{ color: 'var(--emerald-primary)' }}>✔ 25 pts</strong></div>
              </div>
            </div>

            {/* Timeline */}
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Shift Activity Timeline</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {timelineData.timeline_events.length === 0 ? (
                <p style={{ color: 'var(--text-dark-muted)', fontSize: '0.85rem' }}>No shift activity or violations recorded for this worker.</p>
              ) : (
                timelineData.timeline_events.map((ev, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 14px', borderRadius: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-dark)' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--cyan-primary)', fontWeight: 600 }}>{ev.time}</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, flex: 1 }}>{ev.title}</span>
                    <span className="badge badge-amber">{ev.date}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
