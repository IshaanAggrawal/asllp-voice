import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../lib/api';

interface User {
    id: number;
    username: string;
    email: string;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string, passwordConfirm: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Load user on mount
    useEffect(() => {
        const loadUser = async () => {
            const token = localStorage.getItem('access_token');

            if (!token) {
                setLoading(false);
                return;
            }

            try {
                const response = await authAPI.getCurrentUser();
                setUser(response.data);
            } catch (error) {
                console.error('Failed to load user:', error);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
            } finally {
                setLoading(false);
            }
        };

        loadUser();
    }, []);

    const login = async (username: string, password: string) => {
        const response = await authAPI.login(username, password);
        const { access, refresh } = response.data;

        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);

        // Load user data
        const userResponse = await authAPI.getCurrentUser();
        setUser(userResponse.data);
    };

    const register = async (username: string, email: string, password: string, passwordConfirm: string) => {
        // Register user
        await authAPI.register(username, email, password, passwordConfirm);

        // Auto-login after registration
        await login(username, password);
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    };

    const value: AuthContextType = {
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
