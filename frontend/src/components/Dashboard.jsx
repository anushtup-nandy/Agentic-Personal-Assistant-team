import { useState, useEffect } from 'react';
import { Users, Plus, Brain, Sparkles } from 'lucide-react';
import { agentApi, documentApi } from '../api';
import './Dashboard.css';

export default function Dashboard({ profile }) {
    const [agents, setAgents] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, [profile.id]);

    const loadData = async () => {
        try {
            const [agentsRes, docsRes] = await Promise.all([
                agentApi.list(profile.id),
                documentApi.list(profile.id)
            ]);
            setAgents(agentsRes.data);
            setDocuments(docsRes.data);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="dashboard-loading">
                <div className="spinner" style={{ width: '3rem', height: '3rem' }}></div>
            </div>
        );
    }

    const processedDocs = documents.filter(d => d.processed).length;

    return (
        <div className="dashboard fade-in">
            <div className="dashboard-header">
                <div>
                    <h1>Welcome back, {profile.name}! 👋</h1>
                    <p>Your AI-powered decision support system</p>
                </div>
            </div>

            <div className="grid grid-cols-3">
                <div className="stat-card card">
                    <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>
                        <Users size={24} style={{ color: 'var(--color-primary-light)' }} />
                    </div>
                    <div>
                        <div className="stat-value">{agents.length}</div>
                        <div className="stat-label">Active Agents</div>
                    </div>
                </div>

                <div className="stat-card card">
                    <div className="stat-icon" style={{ background: 'rgba(139, 92, 246, 0.2)' }}>
                        <Brain size={24} style={{ color: 'var(--color-secondary)' }} />
                    </div>
                    <div>
                        <div className="stat-value">{processedDocs}</div>
                        <div className="stat-label">Documents Processed</div>
                    </div>
                </div>

                <div className="stat-card card">
                    <div className="stat-icon" style={{ background: 'rgba(236, 72, 153, 0.2)' }}>
                        <Sparkles size={24} style={{ color: 'var(--color-accent)' }} />
                    </div>
                    <div>
                        <div className="stat-value">{profile.expertise_areas?.length || 0}</div>
                        <div className="stat-label">Expertise Areas</div>
                    </div>
                </div>
            </div>

            {profile.profile_summary && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Your Profile Summary</h3>
                    </div>
                    <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                        {profile.profile_summary}
                    </p>

                    {profile.expertise_areas && profile.expertise_areas.length > 0 && (
                        <div style={{ marginTop: 'var(--spacing-lg)' }}>
                            <div style={{ fontSize: '0.875rem', fontWeight: 500, marginBottom: 'var(--spacing-sm)' }}>
                                Expertise Areas:
                            </div>
                            <div className="flex gap-sm" style={{ flexWrap: 'wrap' }}>
                                {profile.expertise_areas.map((area, index) => (
                                    <span key={index} className="badge badge-primary">
                                        {area}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="grid grid-cols-2">
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Quick Actions</h3>
                    </div>
                    <div className="quick-actions">
                        <a href="/agents" className="action-btn">
                            <Plus size={20} />
                            <div>
                                <div className="action-title">Create New Agent</div>
                                <div className="action-desc">Design a custom AI agent persona</div>
                            </div>
                        </a>
                        <a href="/debate" className="action-btn">
                            <Brain size={20} />
                            <div>
                                <div className="action-title">Start a Debate</div>
                                <div className="action-desc">Get AI perspectives on a decision</div>
                            </div>
                        </a>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Recent Documents</h3>
                    </div>
                    {documents.length > 0 ? (
                        <div className="document-list">
                            {documents.slice(0, 5).map(doc => (
                                <div key={doc.id} className="document-item">
                                    <div>
                                        <div className="document-name">{doc.filename}</div>
                                        <div className="document-status">
                                            {doc.processed ? (
                                                <span className="badge badge-success">Processed</span>
                                            ) : (
                                                <span className="badge badge-warning">{doc.embedding_status}</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p style={{ color: 'var(--color-text-tertiary)', fontStyle: 'italic' }}>
                            No documents uploaded yet
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}
