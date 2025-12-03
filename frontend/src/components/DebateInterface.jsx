import { useState, useEffect, useRef } from 'react';
import { MessageSquare, Play, Download, Bot, Sparkles, History, Trash2, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { agentApi, debateApi } from '../api';
import './DebateInterface.css';

export default function DebateInterface({ profile }) {
    const [agents, setAgents] = useState([]);
    const [selectedAgents, setSelectedAgents] = useState([]);
    const [topic, setTopic] = useState('');
    const [title, setTitle] = useState('');
    const [maxTurns, setMaxTurns] = useState(5);
    const [isDebating, setIsDebating] = useState(false);
    const [messages, setMessages] = useState([]);
    const [summary, setSummary] = useState(null);
    const [debateHistory, setDebateHistory] = useState([]);
    const [selectedDebate, setSelectedDebate] = useState(null);
    const [showHistory, setShowHistory] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadAgents();
        loadDebateHistory();
    }, [profile.id]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const loadAgents = async () => {
        try {
            const response = await agentApi.list(profile.id, true);
            setAgents(response.data);
        } catch (error) {
            console.error('Error loading agents:', error);
        }
    };

    const loadDebateHistory = async () => {
        try {
            const response = await debateApi.list(profile.id);
            setDebateHistory(response.data);
        } catch (error) {
            console.error('Error loading debate history:', error);
        }
    };

    const handleDeleteDebate = async (sessionId) => {
        if (!confirm('Are you sure you want to delete this debate?')) {
            return;
        }

        try {
            await debateApi.delete(sessionId);
            await loadDebateHistory();
            if (selectedDebate?.id === sessionId) {
                setSelectedDebate(null);
                setMessages([]);
                setSummary(null);
            }
        } catch (error) {
            console.error('Error deleting debate:', error);
            alert('Failed to delete debate');
        }
    };

    const handleViewDebate = async (debate) => {
        try {
            const response = await debateApi.get(debate.id);
            setSelectedDebate(response.data);
            setMessages(response.data.messages || []);
            setSummary(response.data.decision_summary ? {
                summary: response.data.decision_summary,
                message_count: response.data.messages?.length || 0,
                agents_participated: new Set(response.data.messages?.map(m => m.agent_id) || []).size
            } : null);
            setShowHistory(false);
        } catch (error) {
            console.error('Error loading debate:', error);
            alert('Failed to load debate');
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const toggleAgentSelection = (agentId) => {
        setSelectedAgents(prev =>
            prev.includes(agentId)
                ? prev.filter(id => id !== agentId)
                : [...prev, agentId]
        );
    };

    const handleStartDebate = async () => {
        if (selectedAgents.length < 2) {
            alert('Please select at least 2 agents');
            return;
        }
        if (!topic.trim()) {
            alert('Please enter a topic');
            return;
        }

        setIsDebating(true);
        setMessages([]);
        setSummary(null);

        try {
            // Create debate session
            const sessionResponse = await debateApi.create(profile.id, {
                title: title || topic.substring(0, 100),
                topic,
                agent_ids: selectedAgents,
                debate_format: 'turn_based',
                max_turns: maxTurns,
            });

            const sessionId = sessionResponse.data.id;

            // Start SSE stream
            const eventSource = new EventSource(debateApi.start(sessionId));

            eventSource.addEventListener('message', (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'message') {
                    setMessages(prev => [...prev, {
                        agent_name: data.agent_name,
                        agent_role: data.agent_role,
                        content: data.content,
                        turn: data.turn
                    }]);
                } else if (data.type === 'summary') {
                    setSummary(data.data);
                } else if (data.type === 'complete') {
                    eventSource.close();
                    setIsDebating(false);
                    loadDebateHistory(); // Refresh history after debate completes
                } else if (data.type === 'error') {
                    console.error('Debate error:', data.message);
                    alert(`Error: ${data.message}`);
                    eventSource.close();
                    setIsDebating(false);
                }
            });

            eventSource.onerror = (error) => {
                console.error('SSE error:', error);
                eventSource.close();
                setIsDebating(false);
            };

        } catch (error) {
            console.error('Error starting debate:', error);
            alert('Failed to start debate');
            setIsDebating(false);
        }
    };

    const handleExport = () => {
        const text = messages.map(msg =>
            `${msg.agent_name} (${msg.agent_role}):\n${msg.content}\n`
        ).join('\n');

        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `debate-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="debate-interface fade-in">
            <div className="page-header">
                <div>
                    <h1>Multi-Agent Debate</h1>
                    <p>Engage multiple AI agents in collaborative decision-making</p>
                </div>
                <button
                    className="btn btn-secondary"
                    onClick={() => setShowHistory(!showHistory)}
                >
                    <History size={20} />
                    {showHistory ? 'Hide' : 'Show'} History
                </button>
            </div>

            {/* History Sidebar */}
            {showHistory && (
                <div className="history-sidebar">
                    <div className="history-header">
                        <h3>Debate History</h3>
                        <button className="btn btn-ghost btn-sm" onClick={() => setShowHistory(false)}>
                            <X size={18} />
                        </button>
                    </div>

                    {debateHistory.length === 0 ? (
                        <div className="empty-history">
                            <MessageSquare size={48} style={{ color: 'var(--color-text-tertiary)' }} />
                            <p>No debates yet</p>
                        </div>
                    ) : (
                        <div className="history-list">
                            {debateHistory.map(debate => (
                                <div
                                    key={debate.id}
                                    className={`history-item ${selectedDebate?.id === debate.id ? 'active' : ''}`}
                                >
                                    <div className="history-item-content" onClick={() => handleViewDebate(debate)}>
                                        <div className="history-item-title">{debate.title}</div>
                                        <div className="history-item-meta">
                                            <span>{new Date(debate.created_at).toLocaleDateString()}</span>
                                            <span className={`badge badge-${debate.status === 'completed' ? 'success' : 'warning'}`}>
                                                {debate.status}
                                            </span>
                                        </div>
                                    </div>
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteDebate(debate.id);
                                        }}
                                        title="Delete debate"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            <div className="debate-layout">
                <div className="debate-sidebar card">
                    <h3 className="card-title">Setup Debate</h3>

                    <div className="form-group">
                        <label className="label">Title (Optional)</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="Give this debate a title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            disabled={isDebating}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Topic / Decision *</label>
                        <textarea
                            className="input"
                            placeholder="What decision do you need help with?"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            disabled={isDebating}
                            rows={4}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Max Turns</label>
                        <input
                            type="number"
                            className="input"
                            min="1"
                            max="20"
                            value={maxTurns}
                            onChange={(e) => setMaxTurns(parseInt(e.target.value) || 5)}
                            disabled={isDebating}
                        />
                    </div>

                    <div className="form-group">
                        <label className="label">Select Agents (min. 2)</label>
                        <div className="agent-selection">
                            {agents.map(agent => (
                                <div
                                    key={agent.id}
                                    className={`agent-select-item ${selectedAgents.includes(agent.id) ? 'selected' : ''}`}
                                    onClick={() => !isDebating && toggleAgentSelection(agent.id)}
                                >
                                    <div className="agent-select-avatar">
                                        <Bot size={16} />
                                    </div>
                                    <div className="agent-select-info">
                                        <div className="agent-select-name">{agent.name}</div>
                                        <div className="agent-select-role">{agent.role}</div>
                                    </div>
                                    {selectedAgents.includes(agent.id) && (
                                        <div className="agent-select-check">✓</div>
                                    )}
                                </div>
                            ))}
                            {agents.length === 0 && (
                                <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem', fontStyle: 'italic' }}>
                                    No active agents. Create some first.
                                </p>
                            )}
                        </div>
                    </div>

                    <button
                        className="btn btn-primary w-full glow"
                        onClick={handleStartDebate}
                        disabled={isDebating || selectedAgents.length < 2 || !topic.trim()}
                    >
                        {isDebating ? (
                            <>
                                <div className="spinner" />
                                Debating...
                            </>
                        ) : (
                            <>
                                <Play size={20} />
                                Start Debate
                            </>
                        )}
                    </button>
                </div>

                <div className="debate-main card">
                    <div className="card-header">
                        <div className="flex justify-between items-center">
                            <h3 className="card-title">
                                <MessageSquare size={20} />
                                Conversation
                            </h3>
                            {messages.length > 0 && (
                                <button className="btn btn-ghost btn-sm" onClick={handleExport}>
                                    <Download size={16} />
                                    Export
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="messages-container">
                        {messages.length === 0 ? (
                            <div className="empty-messages">
                                <MessageSquare size={64} style={{ color: 'var(--color-text-tertiary)' }} />
                                <p>No messages yet. Start a debate to begin!</p>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg, index) => (
                                    <div key={index} className="message slide-in">
                                        <div className="message-avatar" style={{ background: getAgentColor(msg.agent_id) }}>
                                            <Bot size={20} />
                                        </div>
                                        <div className="message-content">
                                            <div className="message-header">
                                                <span className="message-name">{msg.agent_name}</span>
                                                <span className="message-role">{msg.agent_role}</span>
                                                <span className="message-turn">Turn {msg.turn + 1}</span>
                                            </div>
                                            <div className="message-text">
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {isDebating && (
                                    <div className="message">
                                        <div className="message-avatar" style={{ background: 'var(--color-surface)' }}>
                                            <div className="spinner" />
                                        </div>
                                        <div className="message-content">
                                            <div className="message-text" style={{ color: 'var(--color-text-tertiary)' }}>
                                                Agent is thinking...
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {summary && (
                        <div className="debate-summary master-summary">
                            <div className="master-header">
                                <Sparkles size={24} style={{ color: 'var(--color-primary-light)' }} />
                                <h4>Master Synthesis</h4>
                            </div>
                            <div className="summary-content">
                                <ReactMarkdown>{summary.summary}</ReactMarkdown>
                            </div>
                            <div className="summary-stats">
                                <div className="summary-stat">
                                    <span className="summary-stat-value">{summary.message_count}</span>
                                    <span className="summary-stat-label">Messages</span>
                                </div>
                                <div className="summary-stat">
                                    <span className="summary-stat-value">{summary.agents_participated}</span>
                                    <span className="summary-stat-label">Agents</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Helper function to assign consistent colors to agents
const agentColors = [
    'linear-gradient(135deg, #6366f1, #8b5cf6)',
    'linear-gradient(135deg, #ec4899, #f43f5e)',
    'linear-gradient(135deg, #3b82f6, #06b6d4)',
    'linear-gradient(135deg, #10b981, #14b8a6)',
    'linear-gradient(135deg, #f59e0b, #f97316)',
];

function getAgentColor(agentId) {
    return agentColors[agentId % agentColors.length];
}
