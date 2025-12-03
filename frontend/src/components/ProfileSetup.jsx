import { useState } from 'react';
import { Upload, FileText, Link as LinkIcon, Sparkles } from 'lucide-react';
import { profileApi, documentApi } from '../api';
import './ProfileSetup.css';

export default function ProfileSetup({ onProfileCreated }) {
    const [mode, setMode] = useState('choice'); // 'choice', 'login', 'signup'
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        portfolio_links: [''],
    });
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [profileId, setProfileId] = useState(null);
    const [uploadProgress, setUploadProgress] = useState({ total: 0, completed: 0 });
    const [loginEmail, setLoginEmail] = useState('');

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handlePortfolioLinkChange = (index, value) => {
        const newLinks = [...formData.portfolio_links];
        newLinks[index] = value;
        setFormData({ ...formData, portfolio_links: newLinks });
    };

    const addPortfolioLink = () => {
        setFormData({
            ...formData,
            portfolio_links: [...formData.portfolio_links, '']
        });
    };

    const handleCreateProfile = async () => {
        if (!formData.name || !formData.email) {
            alert('Please fill in your name and email');
            return;
        }

        setLoading(true);
        try {
            const links = formData.portfolio_links.filter(link => link.trim() !== '');
            const response = await profileApi.create({
                name: formData.name,
                email: formData.email,
                portfolio_links: links,
            });
            setProfileId(response.data.id);
            setMode('signup');
            setStep(2);
        } catch (error) {
            console.error('Error creating profile:', error);
            alert(error.response?.data?.detail || 'Failed to create profile');
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async () => {
        if (!loginEmail.trim()) {
            alert('Please enter your email');
            return;
        }

        setLoading(true);
        try {
            const response = await profileApi.getByEmail(loginEmail);
            onProfileCreated(response.data);
        } catch (error) {
            console.error('Error logging in:', error);
            if (error.response?.status === 404) {
                alert('No profile found with this email. Please create a new account.');
            } else {
                alert('Failed to log in');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = (e) => {
        const selectedFiles = Array.from(e.target.files);
        setFiles(prev => [...prev, ...selectedFiles]);
    };

    const handleUploadDocuments = async () => {
        if (files.length === 0) {
            setStep(3);
            return;
        }

        setLoading(true);
        setUploadProgress({ total: files.length, completed: 0 });

        try {
            for (let i = 0; i < files.length; i++) {
                await documentApi.upload(profileId, files[i]);
                setUploadProgress(prev => ({ ...prev, completed: i + 1 }));
            }
            setStep(3);
        } catch (error) {
            console.error('Error uploading documents:', error);
            alert('Failed to upload some documents');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateSummary = async () => {
        setLoading(true);
        try {
            await documentApi.generateSummary(profileId);
            const profile = await profileApi.get(profileId);
            onProfileCreated(profile.data);
        } catch (error) {
            console.error('Error generating summary:', error);
            alert('Failed to generate profile summary');
        } finally {
            setLoading(false);
        }
    };

    const handleSkipUpload = () => {
        profileApi.get(profileId).then(response => {
            onProfileCreated(response.data);
        });
    };

    return (
        <div className="profile-setup fade-in">
            {mode === 'choice' && (
                <>
                    <div className="setup-header">
                        <h1>Welcome! Let's Get Started</h1>
                        <p>Your AI-powered decision support system</p>
                    </div>

                    <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
                        <div className="choice-container">
                            <button
                                className="choice-btn"
                                onClick={() => setMode('signup')}
                            >
                                <h3>Create New Profile</h3>
                                <p>Set up your profile and teach your AI agents about you</p>
                            </button>

                            <div className="choice-divider">OR</div>

                            <button
                                className="choice-btn"
                                onClick={() => setMode('login')}
                            >
                                <h3>Sign In</h3>
                                <p>Access your existing profile</p>
                            </button>
                        </div>
                    </div>
                </>
            )}

            {mode === 'login' && (
                <>
                    <div className="setup-header">
                        <h1>Welcome Back!</h1>
                        <p>Sign in to access your profile</p>
                    </div>

                    <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
                        <div className="setup-content">
                            <h3>Enter Your Email</h3>

                            <div className="form-group">
                                <label className="label">Email</label>
                                <input
                                    type="email"
                                    className="input"
                                    placeholder="your@email.com"
                                    value={loginEmail}
                                    onChange={(e) => setLoginEmail(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                                />
                            </div>

                            <button
                                className="btn btn-primary w-full"
                                onClick={handleLogin}
                                disabled={loading}
                            >
                                {loading ? <div className="spinner" /> : 'Sign In'}
                            </button>

                            <button
                                className="btn btn-ghost w-full"
                                onClick={() => setMode('choice')}
                                style={{ marginTop: 'var(--spacing-md)' }}
                            >
                                Back
                            </button>
                        </div>
                    </div>
                </>
            )}

            {mode === 'signup' && (
                <>
                    <div className="setup-header">
                        <h1>Welcome! Let's Get to Know You</h1>
                        <p>Help your AI agents understand you better by sharing your background and expertise</p>
                    </div>

                    <div className="setup-steps">
                        <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                            <div className="step-number">1</div>
                            <span>Basic Info</span>
                        </div>
                        <div className="step-line"></div>
                        <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
                            <div className="step-number">2</div>
                            <span>Documents</span>
                        </div>
                        <div className="step-line"></div>
                        <div className={`step ${step >= 3 ? 'active' : ''}`}>
                            <div className="step-number">3</div>
                            <span>Learn</span>
                        </div>
                    </div>

                    <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
                        {step === 1 && (
                            <div className="setup-content">
                                <h3>Tell us about yourself</h3>

                                <div className="form-group">
                                    <label className="label">Name *</label>
                                    <input
                                        type="text"
                                        name="name"
                                        className="input"
                                        placeholder="Your full name"
                                        value={formData.name}
                                        onChange={handleInputChange}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="label">Email *</label>
                                    <input
                                        type="email"
                                        name="email"
                                        className="input"
                                        placeholder="your@email.com"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="label">Portfolio Links (Optional)</label>
                                    {formData.portfolio_links.map((link, index) => (
                                        <div key={index} style={{ marginBottom: 'var(--spacing-sm)' }}>
                                            <input
                                                type="url"
                                                className="input"
                                                placeholder="https://your-portfolio.com"
                                                value={link}
                                                onChange={(e) => handlePortfolioLinkChange(index, e.target.value)}
                                            />
                                        </div>
                                    ))}
                                    <button className="btn btn-ghost btn-sm" onClick={addPortfolioLink}>
                                        <LinkIcon size={16} />
                                        Add Another Link
                                    </button>
                                </div>

                                <button
                                    className="btn btn-primary w-full"
                                    onClick={handleCreateProfile}
                                    disabled={loading}
                                >
                                    {loading ? <div className="spinner" /> : 'Continue'}
                                </button>
                            </div>
                        )}

                        {step === 2 && (
                            <div className="setup-content">
                                <h3>Upload Documents</h3>
                                <p style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-lg)' }}>
                                    Share documents like your resume, portfolio, or any other files that describe your expertise
                                </p>

                                <div className="upload-area">
                                    <input
                                        type="file"
                                        id="file-upload"
                                        multiple
                                        accept=".pdf,.txt,.docx"
                                        onChange={handleFileSelect}
                                        style={{ display: 'none' }}
                                    />
                                    <label htmlFor="file-upload" className="upload-label">
                                        <Upload size={48} />
                                        <span>Click to upload or drag and drop</span>
                                        <span style={{ fontSize: '0.875rem', color: 'var(--color-text-tertiary)' }}>
                                            PDF, TXT, or DOCX files
                                        </span>
                                    </label>
                                </div>

                                {files.length > 0 && (
                                    <div className="file-list">
                                        {files.map((file, index) => (
                                            <div key={index} className="file-item">
                                                <FileText size={20} />
                                                <span>{file.name}</span>
                                                <span className="file-size">
                                                    {(file.size / 1024).toFixed(1)} KB
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {loading && uploadProgress.total > 0 && (
                                    <div className="upload-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill"
                                                style={{
                                                    width: `${(uploadProgress.completed / uploadProgress.total) * 100}%`
                                                }}
                                            />
                                        </div>
                                        <span>
                                            Uploaded {uploadProgress.completed} of {uploadProgress.total} files
                                        </span>
                                    </div>
                                )}

                                <div className="flex gap-md">
                                    <button
                                        className="btn btn-secondary flex-1"
                                        onClick={handleSkipUpload}
                                        disabled={loading}
                                    >
                                        Skip for Now
                                    </button>
                                    <button
                                        className="btn btn-primary flex-1"
                                        onClick={handleUploadDocuments}
                                        disabled={loading}
                                    >
                                        {loading ? <div className="spinner" /> : 'Continue'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {step === 3 && (
                            <div className="setup-content text-center">
                                <Sparkles size={64} style={{ color: 'var(--color-primary-light)', margin: '0 auto var(--spacing-lg)' }} />
                                <h3>Generate Your Profile Summary</h3>
                                <p style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--spacing-xl)' }}>
                                    {files.length > 0
                                        ? 'We\'ll analyze your documents and create a comprehensive profile to help your AI agents understand you better.'
                                        : 'Create your profile to start using the decision support system.'}
                                </p>

                                <button
                                    className="btn btn-primary glow"
                                    onClick={handleGenerateSummary}
                                    disabled={loading}
                                >
                                    {loading ? <div className="spinner" /> : 'Generate Profile & Get Started'}
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
