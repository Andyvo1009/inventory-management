import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Package,
    Warehouse as WarehouseIcon,
    ArrowLeftRight,
    Users,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Box,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Products', path: '/products', icon: Package },
    { label: 'Warehouses', path: '/warehouses', icon: WarehouseIcon },
    { label: 'Stock Movements', path: '/movements', icon: ArrowLeftRight },
    // { label: 'Reports', path: '/reports', icon: BarChart3 },
    { label: 'Users', path: '/users', icon: Users, adminOnly: true },
];

interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
    const { user, isAdmin, logout } = useAuth();

    const filteredItems = navItems.filter(item => !item.adminOnly || isAdmin);
    
    return (
        <aside
            className={`fixed top-0 left-0 h-screen z-40 flex flex-col transition-all duration-300 ease-in-out ${collapsed ? 'w-[72px]' : 'w-[260px]'
                }`}
            style={{
                background: 'linear-gradient(180deg, rgba(15, 22, 41, 0.98) 0%, rgba(10, 14, 23, 0.99) 100%)',
                borderRight: '1px solid rgba(255, 255, 255, 0.06)',
            }}
        >
            {/* Logo */}
            <div className="flex items-center gap-3 px-5 h-[72px] flex-shrink-0">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
                    <Box size={20} className="text-white" />
                </div>
                {!collapsed && (
                    <span className="text-lg font-bold tracking-tight text-white animate-fade-in">
                        Stock<span style={{ color: '#06b6d4' }}>Pilot</span>
                    </span>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {filteredItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/'}
                        className={({ isActive }) =>
                            `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
              ${isActive
                                ? 'text-white'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`
                        }
                        style={({ isActive }) =>
                            isActive
                                ? {
                                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1))',
                                    boxShadow: 'inset 0 0 0 1px rgba(59, 130, 246, 0.2)',
                                }
                                : {}
                        }
                    >
                        <item.icon size={20} className="flex-shrink-0" />
                        {!collapsed && <span>{item.label}</span>}
                    </NavLink>
                ))}
            </nav>

            {/* User profile */}
            <div className="px-3 pb-3 space-y-2">
                <div className="border-t border-white/5 pt-3" />
                <NavLink
                    to="/settings"
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-all"
                >
                    <Settings size={20} className="flex-shrink-0" />
                    {!collapsed && <span>Settings</span>}
                </NavLink>

                {/* User card */}
                {user && (
                    <div className={`flex items-center gap-3 px-3 py-3 rounded-xl ${collapsed ? 'justify-center' : ''}`}
                        style={{ background: 'rgba(255,255,255,0.03)' }}>
                        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
                            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
                            {user.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        {!collapsed && (
                            <div className="flex-1 min-w-0 animate-fade-in">
                                <p className="text-sm font-medium text-white truncate">{user.name}</p>
                                <p className="text-xs text-slate-500 truncate">{user.role}</p>
                            </div>
                        )}
                        {!collapsed && (
                            <button className="text-slate-500 hover:text-rose-400 transition-colors" title="Logout" onClick={logout}>
                                <LogOut size={16} />
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Collapse toggle */}
            <button
                onClick={onToggle}
                className="absolute top-[78px] -right-3 w-6 h-6 rounded-full flex items-center justify-center text-slate-400 hover:text-white transition-colors z-50"
                style={{
                    background: 'rgba(15, 22, 41, 0.95)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
            >
                {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>
        </aside>
    );
}
