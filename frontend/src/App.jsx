import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import ProfileSetup from './components/ProfileSetup';
import AgentManagement from './components/AgentManagement';
import DebateInterface from './components/DebateInterface';
import Dashboard from './components/Dashboard';
import DocumentManagement from './components/DocumentManagement';
import { profileApi } from './api';

function App() {
    const [currentProfile, setCurrentProfile] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing profile in localStorage
        const savedProfileId = localStorage.getItem('currentProfileId');
        if (savedProfileId) {
            loadProfile(savedProfileId);
        } else {
            setLoading(false);
        }
    }, []);

    const loadProfile = async (profileId) => {
        try {
            const response = await profileApi.get(profileId);
            setCurrentProfile(response.data);
        } catch (error) {
            console.error('Error loading profile:', error);
            localStorage.removeItem('currentProfileId');
        } finally {
            setLoading(false);
        }
    };

    const handleProfileCreated = (profile) => {
        setCurrentProfile(profile);
        localStorage.setItem('currentProfileId', profile.id);
    };

    const handleProfileUpdated = (updatedProfile) => {
        setCurrentProfile(updatedProfile);
    };

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh'
            }}>
                <div className="spinner" style={{ width: '3rem', height: '3rem' }}></div>
            </div>
        );
    }

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            {currentProfile && <Navigation profile={currentProfile} />}

            <main style={{ flex: 1, padding: 'var(--spacing-xl) 0' }}>
                <div className="container">
                    {!currentProfile ? (
                        <ProfileSetup onProfileCreated={handleProfileCreated} />
                    ) : (
                        <Routes>
                            <Route path="/" element={<Dashboard profile={currentProfile} />} />
                            <Route
                                path="/documents"
                                element={<DocumentManagement profile={currentProfile} onProfileUpdated={handleProfileUpdated} />}
                            />
                            <Route
                                path="/agents"
                                element={<AgentManagement profile={currentProfile} />}
                            />
                            <Route
                                path="/debate"
                                element={<DebateInterface profile={currentProfile} />}
                            />
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;
