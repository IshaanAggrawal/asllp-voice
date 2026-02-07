import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { agentsAPI, sessionsAPI } from '../lib/api';
import AgentCard from '../components/AgentCard';
import ProtectedRoute from '../components/ProtectedRoute';
import { useAuth } from '../hooks/useAuth';
import Link from 'next/link';

export default function Dashboard() {
    const router = useRouter();
    const { user, logout } = useAuth();
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadAgents();
    }, []);

    const loadAgents = async () => {
        try {
            setLoading(true);
            const response = await agentsAPI.list();
            setAgents(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load agents');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleStartCall = async (agentId: string) => {
        try {
            const response = await agentsAPI.startSession(agentId);
            const sessionId = response.data.id;
            router.push(`/call/${sessionId}`);
        } catch (err) {
            alert('Failed to start session');
            console.error(err);
        }
    };

    const handleDelete = async (agentId: string) => {
        if (!confirm('Are you sure you want to delete this agent?')) return;

        try {
            await agentsAPI.delete(agentId);
            loadAgents();
        } catch (err) {
            alert('Failed to delete agent');
            console.error(err);
        }
    };

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center text-red-600 bg-red-50 px-6 py-4 rounded-lg">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <ProtectedRoute>
            <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                        <div className="flex justify-between items-center">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900">AI Voice Agents</h1>
                                {user && (
                                    <p className="text-sm text-gray-600 mt-1">
                                        Welcome back, <span className="font-medium text-gray-900">{user.username}</span>
                                    </p>
                                )}
                            </div>
                            <div className="flex items-center gap-3">
                                <Link href="/agents/create">
                                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors duration-200 shadow-sm">
                                        + Create New Agent
                                    </button>
                                </Link>
                                <button
                                    onClick={handleLogout}
                                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-2.5 rounded-lg font-medium transition-colors duration-200"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {agents.length === 0 ? (
                        <div className="text-center py-20 bg-white rounded-2xl shadow-sm">
                            <div className="max-w-md mx-auto">
                                <svg
                                    className="mx-auto h-16 w-16 text-gray-400"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={1.5}
                                        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                                    />
                                </svg>
                                <h2 className="mt-6 text-2xl font-semibold text-gray-900">No agents yet</h2>
                                <p className="mt-2 text-gray-600">
                                    Create your first AI voice agent to get started
                                </p>
                                <Link href="/agents/create">
                                    <button className="mt-6 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors duration-200 shadow-sm">
                                        Create Your First Agent
                                    </button>
                                </Link>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {agents.map((agent: any) => (
                                <AgentCard
                                    key={agent.id}
                                    agent={agent}
                                    onDelete={handleDelete}
                                    onStartCall={handleStartCall}
                                />
                            ))}
                        </div>
                    )}
                </main>
            </div>
        </ProtectedRoute>
    );
}
