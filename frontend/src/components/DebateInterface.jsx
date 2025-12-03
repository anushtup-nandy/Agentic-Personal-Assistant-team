import { useState, useEffect, useRef } from 'react';
import { MessageSquare, Play, Download, Bot } from 'lucide-react';
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
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadAgents();
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

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'complete') {
                    eventSource.close();
                    setIsDebating(false);
                } else if (data.type === 'summary') {
                    setSummary(data.data);
                } else if (data.type === 'error') {
                    console.error('Debate error:', data.message);
                    alert('An error occurred during the debate');
                    eventSource.close();
                    setIsDebating(false);
                } else {
                    // Regular message
                    setMessages(prev => [...prev, data]);
                }
            };

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
                    <p>Get diverse perspectives from your AI agents on any decision</p>
                </div>
            </div>

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
                            onChange={(e) => setMaxTurns(parseInt(e.target.value))}
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
                                            <div className="message-text">{msg.content}</div>
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
                        <div className="debate-summary">
                            <h4>Summary & Insights</h4>
                            <p>{summary.summary}</p>
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
