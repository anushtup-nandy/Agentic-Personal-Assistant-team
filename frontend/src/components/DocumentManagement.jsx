import { useState, useEffect } from 'react';
import { Upload, FileText, RefreshCw, Sparkles, Trash2 } from 'lucide-react';
import { documentApi, profileApi } from '../api';
import './DocumentManagement.css';

export default function DocumentManagement({ profile, onProfileUpdated }) {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [generating, setGenerating] = useState(false);

    useEffect(() => {
        loadDocuments();
    }, [profile.id]);

    const loadDocuments = async () => {
        try {
            const response = await documentApi.list(profile.id);
            setDocuments(response.data);
        } catch (error) {
            console.error('Error loading documents:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = async (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        setUploading(true);
        try {
            for (const file of files) {
                await documentApi.upload(profile.id, file);
            }
            await loadDocuments();
        } catch (error) {
            console.error('Error uploading files:', error);
            alert('Failed to upload some files');
        } finally {
            setUploading(false);
        }
    };

    const handleRegenerateProfile = async () => {
        if (!confirm('This will regenerate your profile summary based on all uploaded documents. Continue?')) {
            return;
        }

        setGenerating(true);
        try {
            await documentApi.generateSummary(profile.id);
            const updatedProfile = await profileApi.get(profile.id);
            onProfileUpdated(updatedProfile.data);
            alert('Profile summary regenerated successfully!');
        } catch (error) {
            console.error('Error regenerating profile:', error);
            alert('Failed to regenerate profile summary');
        } finally {
            setGenerating(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center" style={{ minHeight: '400px' }}>
                <div className="spinner" style={{ width: '3rem', height: '3rem' }}></div>
            </div>
        );
    }

    const processedDocs = documents.filter(d => d.processed).length;

    return (
        <div className="document-management fade-in">
            <div className="page-header">
                <div>
                    <h1>Document Management</h1>
                    <p>Upload documents to enhance your AI agents' understanding</p>
                </div>
                <div className="flex gap-md">
                    <button
                        className="btn btn-secondary"
                        onClick={handleRegenerateProfile}
                        disabled={generating || processedDocs === 0}
                    >
                        {generating ? <div className="spinner" /> : <RefreshCw size={20} />}
                        Regenerate Profile
                    </button>
                </div>
            </div>

            <div className="document-grid">
                <div className="card upload-card">
                    <h3 className="card-title">Upload New Documents</h3>
                    <p style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-lg)' }}>
                        Add more documents to improve your profile summary and agent context
                    </p>

                    <div className="upload-area-compact">
                        <input
                            type="file"
                            id="doc-upload"
                            multiple
                            accept=".pdf,.txt,.docx"
                            onChange={handleFileSelect}
                            style={{ display: 'none' }}
                        />
                        <label htmlFor="doc-upload" className="upload-label-compact">
                            {uploading ? (
                                <>
                                    <div className="spinner" />
                                    <span>Uploading...</span>
                                </>
                            ) : (
                                <>
                                    <Upload size={32} />
                                    <span>Click to upload</span>
                                    <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-tertiary)' }}>
                                        PDF, TXT, or DOCX
                                    </span>
                                </>
                            )}
                        </label>
                    </div>

                    <div className="upload-stats">
                        <div className="stat-item">
                            <span className="stat-number">{documents.length}</span>
                            <span className="stat-label">Total Documents</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-number">{processedDocs}</span>
                            <span className="stat-label">Processed</span>
                        </div>
                    </div>
                </div>

                <div className="card documents-list-card">
                    <div className="card-header">
                        <h3 className="card-title">Your Documents</h3>
                    </div>

                    {documents.length === 0 ? (
                        <div className="empty-documents">
                            <FileText size={48} style={{ color: 'var(--color-text-tertiary)' }} />
                            <p>No documents uploaded yet</p>
                        </div>
                    ) : (
                        <div className="documents-list">
                            {documents.map(doc => (
                                <div key={doc.id} className="document-item">
                                    <FileText size={20} className="doc-icon" />
                                    <div className="doc-info">
                                        <div className="doc-name">{doc.filename}</div>
                                        <div className="doc-meta">
                                            <span>{doc.file_type.toUpperCase()}</span>
                                            {doc.file_size && (
                                                <>
                                                    <span>•</span>
                                                    <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                                                </>
                                            )}
                                            <span>•</span>
                                            <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                    <div className="doc-status">
                                        {doc.processed ? (
                                            <span className="badge badge-success">Processed</span>
                                        ) : doc.embedding_status === 'processing' ? (
                                            <span className="badge badge-warning">Processing</span>
                                        ) : doc.embedding_status === 'failed' ? (
                                            <span className="badge badge-error">Failed</span>
                                        ) : (
                                            <span className="badge">Pending</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {profile.profile_summary && (
                <div className="card profile-summary-card">
                    <div className="card-header">
                        <div className="flex justify-between items-center">
                            <h3 className="card-title">
                                <Sparkles size={20} style={{ color: 'var(--color-primary-light)' }} />
                                Current Profile Summary
                            </h3>
                            <span className="badge badge-primary">
                                {processedDocs} document{processedDocs !== 1 ? 's' : ''} analyzed
                            </span>
                        </div>
                    </div>
                    <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
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
        </div>
    );
}
