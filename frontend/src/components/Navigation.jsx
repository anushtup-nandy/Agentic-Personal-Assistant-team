import { Link, useLocation } from 'react-router-dom';
import { Brain, Users, MessageSquare, Home, FileText } from 'lucide-react';
import './Navigation.css';

export default function Navigation({ profile }) {
    const location = useLocation();

    const navItems = [
        { path: '/', icon: Home, label: 'Dashboard' },
        { path: '/documents', icon: FileText, label: 'Documents' },
        { path: '/agents', icon: Users, label: 'Agents' },
        { path: '/debate', icon: MessageSquare, label: 'Debate' },
    ];

    return (
        <nav className="navigation glass">
            <div className="container">
                <div className="nav-content">
                    <div className="nav-brand">
                        <Brain className="brand-icon" size={32} />
                        <div>
                            <h3 className="brand-title">Agent Decision Support</h3>
                            <p className="brand-subtitle">{profile.name}</p>
                        </div>
                    </div>

                    <div className="nav-links">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname === item.path;

                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`nav-link ${isActive ? 'active' : ''}`}
                                >
                                    <Icon size={20} />
                                    <span>{item.label}</span>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>
        </nav>
    );
}
