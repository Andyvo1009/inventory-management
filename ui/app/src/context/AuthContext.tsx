import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import * as authApi from '../api/auth';
import type { LoginRequest, RegisterRequest, ChangePasswordRequest } from '../api/auth';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isAdmin: boolean;
    isLoading: boolean;
    login: (credentials: LoginRequest) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => void;
    changePassword: (data: ChangePasswordRequest) => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Initialize - check if user is already authenticated
    useEffect(() => {
        const initAuth = async () => {
            if (authApi.isAuthenticated()) {
                try {
                    const userResponse = await authApi.getCurrentUser();
                    setUser(authApi.mapUserResponse(userResponse));
                } catch (error) {
                    console.error('Failed to load user:', error);
                    authApi.logout();
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = async (credentials: LoginRequest) => {
        setIsLoading(true);
        try {
            await authApi.login(credentials);
            const userResponse = await authApi.getCurrentUser();
            setUser(authApi.mapUserResponse(userResponse));
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (data: RegisterRequest) => {
        setIsLoading(true);
        try {
            await authApi.register(data);
            
            // After registration, automatically log in
            await authApi.login({
                email: data.email,
                password: data.password,
            });
            
            // Fetch the user data
            const currentUserResponse = await authApi.getCurrentUser();
            setUser(authApi.mapUserResponse(currentUserResponse));
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        authApi.logout();
        setUser(null);
    };

    const changePassword = async (data: ChangePasswordRequest) => {
        await authApi.changePassword(data);
    };

    const refreshUser = async () => {
        if (authApi.isAuthenticated()) {
            try {
                const userResponse = await authApi.getCurrentUser();
                setUser(authApi.mapUserResponse(userResponse));
            } catch (error) {
                console.error('Failed to refresh user:', error);
                logout();
            }
        }
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isAdmin: user?.role === 'Admin',
                isLoading,
                login,
                register,
                logout,
                changePassword,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}
