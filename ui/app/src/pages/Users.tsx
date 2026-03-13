import { useState, useEffect } from 'react';
import { Shield, ShieldCheck, Mail, Trash2, UserPlus, Loader2, Edit2 } from 'lucide-react';
import Header from '../components/Header';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { useAuth } from '../context/AuthContext';
import type { UserResponse, UserCreateRequest, UserUpdateRequest, UserRole } from '../types';
import * as usersApi from '../api/users';
import { ApiError } from '../api/client';

export default function UsersPage() {
    const { isAdmin } = useAuth();
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
    const [confirmDialog, setConfirmDialog] = useState<{
        isOpen: boolean;
        userId: number | null;
    }>({ isOpen: false, userId: null });
    
    // Data state
    const [users, setUsers] = useState<UserResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await usersApi.listUsers();
            setUsers(response.users);
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to load users';
            setError(errorMsg);
            console.error('Error fetching users:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (data: UserCreateRequest) => {
        try {
            await usersApi.createUser(data);
            setShowAddModal(false);
            fetchUsers();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to create user';
            throw new Error(errorMsg);
        }
    };

    const handleUpdateUser = async (userId: number, data: UserUpdateRequest) => {
        try {
            await usersApi.updateUser(userId, data);
            setShowEditModal(false);
            setEditingUser(null);
            fetchUsers();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to update user';
            throw new Error(errorMsg);
        }
    };

    const handleDeleteUser = async (userId: number) => {
        setConfirmDialog({ isOpen: true, userId });
    };

    const confirmDeleteUser = async () => {
        if (!confirmDialog.userId) return;
        
        setConfirmDialog({ isOpen: false, userId: null });
        try {
            await usersApi.deleteUser(confirmDialog.userId);
            fetchUsers();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to delete user';
            alert(errorMsg);
        }
    };

    const handleEditClick = (user: UserResponse) => {
        setEditingUser(user);
        setShowEditModal(true);
    };

    if (!isAdmin) {
        return (
            <div>
                <Header title="Users" subtitle="Manage team members and access" />
                <div className="px-8"><div className="glass-card p-12 text-center"><Shield size={48} className="mx-auto mb-4 text-slate-500" /><h3 className="text-lg font-bold text-white mb-2">Access Restricted</h3><p className="text-sm text-slate-400">Only administrators can manage users.</p></div></div>
            </div>
        );
    }

    const roleColors = {
        Admin: { color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)', border: 'rgba(139,92,246,0.2)' },
        Staff: { color: '#06b6d4', bg: 'rgba(6,182,212,0.12)', border: 'rgba(6,182,212,0.2)' },
    };

    if (loading) {
        return (
            <div>
                <Header title="Users" subtitle="Manage team members and access" />
                <div className="flex items-center justify-center py-20">
                    <Loader2 size={32} className="text-blue-400 animate-spin" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <Header title="Users" subtitle="Manage team members and access" />
                <div className="text-center py-20">
                    <p className="text-rose-400 text-sm">{error}</p>
                    <button
                        onClick={fetchUsers}
                        className="mt-4 px-4 py-2 rounded-lg text-sm text-white bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div>
            <Header title="Users" subtitle={`${users.length} team members`} onAddNew={() => setShowAddModal(true)} addNewLabel="Add User" />

            <div className="px-8 pb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {users.map((u, i) => {
                    const rc = roleColors[u.role];
                    return (
                        <div key={u.id} className="glass-card glass-card-hover p-6 opacity-0 animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold text-white" style={{ background: u.role === 'Admin' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'linear-gradient(135deg, #06b6d4, #10b981)' }}>
                                        {u.name.split(' ').map(n => n[0]).join('')}
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-white">{u.name}</p>
                                        <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500"><Mail size={12} />{u.email}</div>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => handleEditClick(u)}
                                    className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-all"
                                >
                                    <Edit2 size={16} />
                                </button>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold" style={{ background: rc.bg, color: rc.color, border: `1px solid ${rc.border}` }}>
                                    {u.role === 'Admin' ? <ShieldCheck size={13} /> : <Shield size={13} />}{u.role}
                                </span>
                                <button 
                                    onClick={() => handleDeleteUser(u.id)}
                                    className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 transition-all" 
                                    title="Remove user"
                                >
                                    <Trash2 size={15} />
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>

            <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add New User">
                <UserForm
                    onSubmit={handleCreateUser}
                    onClose={() => setShowAddModal(false)}
                    roleColors={roleColors}
                />
            </Modal>

            <Modal isOpen={showEditModal} onClose={() => { setShowEditModal(false); setEditingUser(null); }} title="Edit User">
                <UserEditForm
                    user={editingUser}
                    onSubmit={handleUpdateUser}
                    onClose={() => { setShowEditModal(false); setEditingUser(null); }}
                    roleColors={roleColors}
                />
            </Modal>
            {/* Confirmation Dialog */}
            <ConfirmDialog
                isOpen={confirmDialog.isOpen}
                title="Delete User"
                message="Are you sure you want to delete this user?"
                onConfirm={confirmDeleteUser}
                onCancel={() => setConfirmDialog({ isOpen: false, userId: null })}
            />        </div>
    );
}

// UserForm component for creating new users
function UserForm({
    onSubmit,
    onClose,
    roleColors,
}: {
    onSubmit: (data: UserCreateRequest) => Promise<void>;
    onClose: () => void;
    roleColors: Record<UserRole, { color: string; bg: string; border: string }>;
}) {
    const [formData, setFormData] = useState<UserCreateRequest>({
        name: '',
        email: '',
        password: '',
        role: 'Staff',
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!formData.name || !formData.email || !formData.password) {
            setError('All fields are required');
            return;
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit(formData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create user');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-5">
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Full Name *</label>
                <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    placeholder="Enter name"
                />
            </div>
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Email *</label>
                <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    placeholder="email@company.com"
                />
            </div>
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Password *</label>
                <input
                    type="password"
                    required
                    minLength={6}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    placeholder="Minimum 6 characters"
                />
            </div>
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Role</label>
                <div className="grid grid-cols-2 gap-3">
                    {(['Admin', 'Staff'] as const).map(role => {
                        const rc = roleColors[role];
                        const isSelected = formData.role === role;
                        return (
                            <button
                                key={role}
                                type="button"
                                onClick={() => setFormData({ ...formData, role })}
                                className={`p-4 rounded-xl text-center transition-all ${isSelected ? 'ring-2' : ''}`}
                                style={{
                                    background: isSelected ? rc.bg : 'rgba(255,255,255,0.03)',
                                    border: `1px solid ${isSelected ? rc.border : 'rgba(255,255,255,0.05)'}`,
                                }}
                            >
                                {role === 'Admin' ? (
                                    <ShieldCheck size={20} className="mx-auto mb-2" style={{ color: rc.color }} />
                                ) : (
                                    <Shield size={20} className="mx-auto mb-2" style={{ color: rc.color }} />
                                )}
                                <p className="text-sm font-medium text-white">{role}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {role === 'Admin' ? 'Full access' : 'Limited access'}
                                </p>
                            </button>
                        );
                    })}
                </div>
            </div>

            {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
                    {error}
                </div>
            )}

            <div className="flex justify-end gap-3 pt-3">
                <button
                    type="button"
                    onClick={onClose}
                    disabled={submitting}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    style={{
                        background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                        boxShadow: '0 4px 16px rgba(59,130,246,0.3)',
                    }}
                >
                    {submitting && <Loader2 size={16} className="animate-spin" />}
                    {submitting ? 'Adding...' : <><UserPlus size={16} />Add User</>}
                </button>
            </div>
        </form>
    );
}

// UserEditForm component for editing existing users
function UserEditForm({
    user,
    onSubmit,
    onClose,
    roleColors,
}: {
    user: UserResponse | null;
    onSubmit: (userId: number, data: UserUpdateRequest) => Promise<void>;
    onClose: () => void;
    roleColors: Record<UserRole, { color: string; bg: string; border: string }>;
}) {
    const [formData, setFormData] = useState<UserUpdateRequest>({
        name: user?.name || '',
        role: user?.role || 'Staff',
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;

        setError(null);

        if (!formData.name) {
            setError('Name is required');
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit(user.id, formData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update user');
        } finally {
            setSubmitting(false);
        }
    };

    if (!user) return null;

    return (
        <form onSubmit={handleSubmit} className="space-y-5">
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Full Name *</label>
                <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    placeholder="Enter name"
                />
            </div>
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Email</label>
                <input
                    type="email"
                    disabled
                    value={user.email}
                    className="w-full px-4 py-3 rounded-xl text-sm text-slate-500 outline-none cursor-not-allowed"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}
                />
                <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
            </div>
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Role</label>
                <div className="grid grid-cols-2 gap-3">
                    {(['Admin', 'Staff'] as const).map(role => {
                        const rc = roleColors[role];
                        const isSelected = formData.role === role;
                        return (
                            <button
                                key={role}
                                type="button"
                                onClick={() => setFormData({ ...formData, role })}
                                className={`p-4 rounded-xl text-center transition-all ${isSelected ? 'ring-2' : ''}`}
                                style={{
                                    background: isSelected ? rc.bg : 'rgba(255,255,255,0.03)',
                                    border: `1px solid ${isSelected ? rc.border : 'rgba(255,255,255,0.05)'}`,
                                }}
                            >
                                {role === 'Admin' ? (
                                    <ShieldCheck size={20} className="mx-auto mb-2" style={{ color: rc.color }} />
                                ) : (
                                    <Shield size={20} className="mx-auto mb-2" style={{ color: rc.color }} />
                                )}
                                <p className="text-sm font-medium text-white">{role}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {role === 'Admin' ? 'Full access' : 'Limited access'}
                                </p>
                            </button>
                        );
                    })}
                </div>
            </div>

            {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
                    {error}
                </div>
            )}

            <div className="flex justify-end gap-3 pt-3">
                <button
                    type="button"
                    onClick={onClose}
                    disabled={submitting}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    style={{
                        background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                        boxShadow: '0 4px 16px rgba(59,130,246,0.3)',
                    }}
                >
                    {submitting && <Loader2 size={16} className="animate-spin" />}
                    {submitting ? 'Updating...' : 'Update User'}
                </button>
            </div>
        </form>
    );
}
