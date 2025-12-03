import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Bot } from 'lucide-react';
import { agentApi, utilityApi } from '../api';
import PromptEditor from './PromptEditor';
import './AgentManagement.css';

export default function AgentManagement({ profile }) {
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showEditor, setShowEditor] = useState(false);
    const [editingAgent, setEditingAgent] = useState(null);
    const [template, setTemplate] = useState('');

    useEffect(() => {
        loadAgents();
        loadTemplate();
    }, [profile.id]);

    const loadAgents = async () => {
        try {
            const response = await agentApi.list(profile.id);
            setAgents(response.data);
        } catch (error) {
            console.error('Error loading agents:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadTemplate = async () => {
        try {
            const response = await utilityApi.getTemplate();
            setTemplate(response.data.template);
        } catch (error) {
            console.error('Error loading template:', error);
        }
    };

    const handleCreateAgent = () => {
        setEditingAgent(null);
        setShowEditor(true);
    };

    const handleEditAgent = (agent) => {
        setEditingAgent(agent);
        setShowEditor(true);
    };

    const handleDeleteAgent = async (agentId) => {
        if (!confirm('Are you sure you want to delete this agent?')) return;

        try {
            await agentApi.delete(agentId);
            setAgents(agents.filter(a => a.id !== agentId));
        } catch (error) {
            console.error('Error deleting agent:', error);
            alert('Failed to delete agent');
        }
    };

    const handleSaveAgent = async (agentData) => {
        try {
            if (editingAgent) {
                await agentApi.update(editingAgent.id, agentData);
            } else {
                await agentApi.create(profile.id, agentData);
            }
            setShowEditor(false);
            loadAgents();
        } catch (error) {
            console.error('Error saving agent:', error);
            throw error;
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center" style={{ minHeight: '400px' }}>
                <div className="spinner" style={{ width: '3rem', height: '3rem' }}></div>
            </div>
        );
    }

    if (showEditor) {
        return (
            <PromptEditor
                profile={profile}
                agent={editingAgent}
                template={template}
                onSave={handleSaveAgent}
                onCancel={() => setShowEditor(false)}
            />
        );
    }

    return (
        <div className="agent-management fade-in">
            <div className="page-header">
                <div>
                    <h1>AI Agent Management</h1>
                    <p>Create and manage agents with custom personas for decision-making</p>
                </div>
                <button className="btn btn-primary glow" onClick={handleCreateAgent}>
                    <Plus size={20} />
                    Create New Agent
                </button>
            </div>

            {agents.length === 0 ? (
                <div className="empty-state card">
                    <Bot size={64} style={{ color: 'var(--color-primary-light)', margin: '0 auto var(--spacing-lg)' }} />
                    <h3>No Agents Yet</h3>
                    <p>Create your first AI agent to start making collaborative decisions</p>
                    <button className="btn btn-primary" onClick={handleCreateAgent}>
                        <Plus size={20} />
                        Create Your First Agent
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-2">
                    {agents.map(agent => (
                        <div key={agent.id} className="agent-card card">
                            <div className="agent-header">
                                <div className="agent-avatar">
                                    <Bot size={24} />
                                </div>
                                <div className="flex-1">
                                    <h3 className="agent-name">{agent.name}</h3>
                                    <p className="agent-role">{agent.role}</p>
                                </div>
                                <div className="agent-actions">
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => handleEditAgent(agent)}
                                        title="Edit agent"
                                    >
                                        <Edit2 size={16} />
                                    </button>
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => handleDeleteAgent(agent.id)}
                                        title="Delete agent"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            {agent.description && (
                                <p className="agent-description">{agent.description}</p>
                            )}

                            <div className="agent-meta">
                                <div className="meta-item">
                                    <span className="meta-label">Model:</span>
                                    <span className="badge">
                                        {agent.model_provider} / {agent.model_name}
                                    </span>
                                </div>
                                <div className="meta-item">
                                    <span className="meta-label">Temperature:</span>
                                    <span className="badge">{agent.temperature}</span>
                                </div>
                                <div className="meta-item">
                                    <span className="meta-label">Max Tokens:</span>
                                    <span className="badge">{agent.max_tokens}</span>
                                </div>
                            </div>

                            {!agent.is_active && (
                                <div className="agent-inactive">
                                    <span className="badge badge-warning">Inactive</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
