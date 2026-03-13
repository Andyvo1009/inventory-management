import { useState } from 'react';
import { Search, Plus, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
    title: string;
    subtitle?: string;
    onAddNew?: () => void;
    addNewLabel?: string;
}

export default function Header({ title, subtitle, onAddNew, addNewLabel }: HeaderProps) {
    const [searchFocused, setSearchFocused] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const { user, logout, isAdmin } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <header className="flex items-center justify-between py-6 px-8 flex-wrap gap-4">
            {/* Left: Title */}
            <div className="animate-fade-in">
                <h1 className="text-2xl font-bold text-white tracking-tight">{title}</h1>
                {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-3 animate-fade-in">
                {/* Search */}
                <div
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all duration-300 ${searchFocused ? 'w-72' : 'w-56'
                        }`}
                    style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: searchFocused
                            ? '1px solid rgba(59, 130, 246, 0.4)'
                            : '1px solid rgba(255, 255, 255, 0.08)',
                    }}
                >
                    <Search size={16} className="text-slate-400 flex-shrink-0" />
                    <input
                        type="text"
                        placeholder="Search..."
                        className="bg-transparent text-sm text-white placeholder-slate-500 outline-none w-full"
                        onFocus={() => setSearchFocused(true)}
                        onBlur={() => setSearchFocused(false)}
                    />
                </div>

                {/* Notifications */}
                {/* <button
                    className="relative w-10 h-10 rounded-xl flex items-center justify-center text-slate-400 hover:text-white transition-all"
                    style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                    }}
                >
                    <Bell size={18} />
                    <span
                        className="absolute top-2 right-2 w-2 h-2 rounded-full"
                        style={{ background: '#f43f5e' }}
                    />
                </button> */}

                {/* Add New button */}
                {onAddNew && (
                    <button
                        onClick={onAddNew}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                        style={{
                            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                            boxShadow: '0 4px 16px rgba(59, 130, 246, 0.3)',
                        }}
                    >
                        <Plus size={18} />
                        {addNewLabel || 'Add New'}
                    </button>
                )}

                {/* User Menu */}
                {user && (
                    <div className="relative">
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-white transition-all hover:bg-white/10"
                            style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid rgba(255, 255, 255, 0.08)',
                            }}
                        >
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
                                {user.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="text-left">
                                <p className="text-sm font-medium">{user.name}</p>
                                <p className="text-xs text-slate-400">{user.role}</p>
                            </div>
                            <ChevronDown size={16} className="text-slate-400" />
                        </button>

                        {/* Dropdown Menu */}
                        {showUserMenu && (
                            <>
                                <div
                                    className="fixed inset-0 z-10"
                                    onClick={() => setShowUserMenu(false)}
                                />
                                <div
                                    className="absolute right-0 mt-2 w-56 rounded-xl shadow-xl z-20 overflow-visible"
                                    style={{
                                        background: 'rgba(30, 41, 59, 0.95)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)'
                                    }}
                                >
                                    <div className="p-4 border-b border-white/10">
                                        <p className="text-sm text-white font-medium">{user.name}</p>
                                        <p className="text-xs text-slate-400 mt-1">{user.email}</p>
                                        {isAdmin && (
                                            <span className="inline-block mt-2 px-2 py-1 text-xs font-medium bg-blue-500/20 text-blue-400 rounded">
                                                Admin
                                            </span>
                                        )}
                                    </div>
                                    <div className="py-2">
                                        <button
                                            onClick={() => {
                                                setShowUserMenu(false);
                                                navigate('/settings');
                                            }}
                                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5 transition-colors"
                                        >
                                            <Settings size={16} />
                                            Settings
                                        </button>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                                        >
                                            <LogOut size={16} />
                                            Logout
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}
            </div>
        </header>
    );
}
