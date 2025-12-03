import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Check, X, AlertCircle } from 'lucide-react';
import { utilityApi } from '../api';
import './PromptEditor.css';

export default function PromptEditor({ profile, agent, template, onSave, onCancel }) {
    const [formData, setFormData] = useState({
        name: '',
        role: '',
        description: '',
        model_provider: 'gemini',
        model_name: 'gemini-pro',
        system_prompt_raw: template,
        temperature: 0.7,
        max_tokens: 500,
    });
    const [validation, setValidation] = useState({ is_valid: true, variables: [], error_message: null });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (agent) {
            setFormData({
                name: agent.name,
                role: agent.role,
                description: agent.description || '',
                model_provider: agent.model_provider,
                model_name: agent.model_name,
                system_prompt_raw: agent.system_prompt_raw,
                temperature: agent.temperature,
                max_tokens: agent.max_tokens,
            });
        }
    }, [agent]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handlePromptChange = (value) => {
        setFormData({ ...formData, system_prompt_raw: value });
        validatePrompt(value);
    };

    const validatePrompt = async (prompt) => {
        try {
            const response = await utilityApi.validatePrompt(prompt);
            setValidation(response.data);
        } catch (error) {
            console.error('Error validating prompt:', error);
        }
    };

    const handleSubmit = async () => {
        if (!formData.name || !formData.role || !formData.system_prompt_raw) {
            alert('Please fill in all required fields');
            return;
        }

        if (!validation.is_valid) {
            alert('Please fix prompt errors before saving');
            return;
        }

        setLoading(true);
        try {
            await onSave(formData);
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to save agent');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="prompt-editor fade-in">
            <div className="editor-header">
                <div>
                    <h1>{agent ? 'Edit Agent' : 'Create New Agent'}</h1>
                    <p>Design your agent's personality and behavior</p>
                </div>
                <div className="flex gap-md">
                    <button className="btn btn-secondary" onClick={onCancel}>
                        <X size={20} />
                        Cancel
                    </button>
                    <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
                        {loading ? <div className="spinner" /> : <Check size={20} />}
                        {loading ? 'Saving...' : 'Save Agent'}
                    </button>
                </div>
            </div>

            <div className="editor-layout">
                <div className="editor-sidebar card">
                    <h3 className="card-title">Agent Configuration</h3>

                    <div className="form-group">
                        <label className="label">Name *</label>
                        <input
                            type="text"
                            name="name"
                            className="input"
                            placeholder="e.g., Critical Thinker"
                            value={formData.name}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Role *</label>
                        <input
                            type="text"
                            name="role"
                            className="input"
                            placeholder="e.g., devil's advocate"
                            value={formData.role}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Description</label>
                        <textarea
                            name="description"
                            className="input"
                            placeholder="Brief description of the agent's purpose"
                            value={formData.description}
                            onChange={handleInputChange}
                            rows={3}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Model Provider *</label>
                        <select
                            name="model_provider"
                            className="input"
                            value={formData.model_provider}
                            onChange={handleInputChange}
                        >
                            <option value="gemini">Gemini (AI Studio)</option>
                            <option value="ollama">Ollama (Local)</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="label">Model Name *</label>
                        <input
                            type="text"
                            name="model_name"
                            className="input"
                            placeholder={formData.model_provider === 'gemini' ? 'gemini-pro' : 'llama2'}
                            value={formData.model_name}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Temperature (0-2)</label>
                        <input
                            type="number"
                            name="temperature"
                            className="input"
                            min="0"
                            max="2"
                            step="0.1"
                            value={formData.temperature}
                            onChange={handleInputChange}
                        />
                        <small style={{ color: 'var(--color-text-tertiary)', fontSize: '0.8125rem' }}>
                            Higher = more creative, Lower = more focused
                        </small>
                    </div>

                    <div className="form-group">
                        <label className="label">Max Tokens</label>
                        <input
                            type="number"
                            name="max_tokens"
                            className="input"
                            min="1"
                            max="4000"
                            value={formData.max_tokens}
                            onChange={handleInputChange}
                        />
                    </div>
                </div>

                <div className="editor-main card">
                    <div className="card-header">
                        <div className="flex justify-between items-center">
                            <h3 className="card-title">System Prompt (YAML/XML) *</h3>
                            {validation.is_valid ? (
                                <span className="badge badge-success">
                                    <Check size={14} />
                                    Valid
                                </span>
                            ) : (
                                <span className="badge badge-error">
                                    <AlertCircle size={14} />
                                    Invalid
                                </span>
                            )}
                        </div>
                        {validation.error_message && (
                            <p style={{ color: 'var(--color-error)', fontSize: '0.875rem', marginTop: 'var(--spacing-sm)' }}>
                                {validation.error_message}
                            </p>
                        )}
                    </div>

                    <div className="monaco-wrapper">
                        <Editor
                            height="500px"
                            defaultLanguage="yaml"
                            theme="vs-dark"
                            value={formData.system_prompt_raw}
                            onChange={handlePromptChange}
                            options={{
                                minimap: { enabled: false },
                                fontSize: 13,
                                lineNumbers: 'on',
                                scrollBeyondLastLine: false,
                                automaticLayout: true,
                                tabSize: 2,
                            }}
                        />
                    </div>

                    {validation.variables && validation.variables.length > 0 && (
                        <div className="variables-info">
                            <div style={{ fontSize: '0.875rem', fontWeight: 500, marginBottom: 'var(--spacing-sm)' }}>
                                Available Variables:
                            </div>
                            <div className="flex gap-sm" style={{ flexWrap: 'wrap' }}>
                                {validation.variables.map((variable, index) => (
                                    <span key={index} className="badge badge-primary">
                                        {'{{'}{variable}{'}}'}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="prompt-help">
                        <h4>Template Structure:</h4>
                        <ul>
                            <li><code>&lt;persona&gt;</code> - Agent's personality and approach</li>
                            <li><code>&lt;context&gt;</code> - Dynamic context with variables</li>
                            <li><code>&lt;behavior&gt;</code> - Behavior guidelines</li>
                            <li><code>&lt;constraints&gt;</code> - Limitations and rules</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}
