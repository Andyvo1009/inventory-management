import { useEffect, useState } from 'react';
import { Building2, User, Palette, Lock, Check, AlertCircle, Loader2 } from 'lucide-react';
import Header from '../components/Header';
import { useAuth } from '../context/AuthContext';
import { getCurrentUserProfile } from '../api/users';
import { getCurrentTenantProfile, type TenantResponse } from '../api/tenants';

type SettingsUser = {
    name: string;
    email: string;
    role: string;
};

export default function Settings() {
    const { user, changePassword } = useAuth();
    const [settingsUser, setSettingsUser] = useState<SettingsUser | null>(
        user ? { name: user.name, email: user.email, role: user.role } : null,
    );
    const [tenant, setTenant] = useState<TenantResponse | null>(null);
    const [isLoadingProfile, setIsLoadingProfile] = useState(true);
    const [profileError, setProfileError] = useState<string | null>(null);
    const [showChangePassword, setShowChangePassword] = useState(false);
    const [passwordData, setPasswordData] = useState({
        old_password: '',
        new_password: '',
        confirm_password: '',
    });
    const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [isChangingPassword, setIsChangingPassword] = useState(false);

    useEffect(() => {
        const fetchProfileData = async () => {
            try {
                setIsLoadingProfile(true);
                setProfileError(null);

                const [userResponse, tenantResponse] = await Promise.all([
                    getCurrentUserProfile(),
                    getCurrentTenantProfile(),
                ]);

                setSettingsUser({
                    name: userResponse.name,
                    email: userResponse.email,
                    role: userResponse.role,
                });
                setTenant(tenantResponse);
            } catch (error) {
                console.error('Failed to load settings profile data:', error);
                setProfileError('Failed to load profile information. Please refresh and try again.');
            } finally {
                setIsLoadingProfile(false);
            }
        };

        fetchProfileData();
    }, []);

    const formatDate = (isoDate: string | undefined) => {
        if (!isoDate) return '-';
        return new Date(isoDate).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        setPasswordMessage(null);

        if (passwordData.new_password !== passwordData.confirm_password) {
            setPasswordMessage({ type: 'error', text: 'New passwords do not match' });
            return;
        }

        if (passwordData.new_password.length < 6) {
            setPasswordMessage({ type: 'error', text: 'Password must be at least 6 characters long' });
            return;
        }

        setIsChangingPassword(true);
        try {
            await changePassword({
                old_password: passwordData.old_password,
                new_password: passwordData.new_password,
            });
            setPasswordMessage({ type: 'success', text: 'Password changed successfully' });
            setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
            setTimeout(() => {
                setShowChangePassword(false);
                setPasswordMessage(null);
            }, 2000);
        } catch (error: any) {
            setPasswordMessage({ type: 'error', text: error.message || 'Failed to change password' });
        } finally {
            setIsChangingPassword(false);
        }
    };

    const sections = [
        {
            title: 'Company Profile',
            icon: Building2,
            items: [
                { label: 'Company Name', value: tenant?.name || '-' },
                { label: 'Plan', value: 'Business Pro' },
                { label: 'Member Since', value: formatDate(tenant?.created_at) },
            ],
        },
        {
            title: 'Account',
            icon: User,
            items: settingsUser ? [
                { label: 'Name', value: settingsUser.name },
                { label: 'Email', value: settingsUser.email },
                { label: 'Role', value: settingsUser.role },
            ] : [],
        },
        {
            title: 'Preferences',
            icon: Palette,
            items: [
                { label: 'Theme', value: 'Dark' },
                { label: 'Language', value: 'English' },
                { label: 'Timezone', value: 'UTC+7' },
            ],
        },
    ];

    return (
        <div>
            <Header title="Settings" subtitle="Manage your account and preferences" />
            <div className="px-8 pb-8 max-w-3xl space-y-6">
                {isLoadingProfile && (
                    <div className="glass-card p-4 flex items-center gap-2 text-sm text-slate-300">
                        <Loader2 className="w-4 h-4 animate-spin text-accent-blue" />
                        Loading account and company details...
                    </div>
                )}

                {profileError && (
                    <div className="glass-card p-4 text-sm text-red-400">
                        {profileError}
                    </div>
                )}

                {sections.map((section, i) => {
                    const Icon = section.icon;
                    return (
                        <div key={section.title} className="glass-card overflow-hidden opacity-0 animate-fade-in" style={{ animationDelay: `${i * 100}ms` }}>
                            <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
                                <Icon size={18} className="text-accent-blue" />
                                <h3 className="text-sm font-bold text-white">{section.title}</h3>
                            </div>
                            <div className="divide-y divide-white/[0.03]">
                                {section.items.map(item => (
                                    <div key={item.label} className="px-6 py-4 flex items-center justify-between">
                                        <span className="text-sm text-slate-400">{item.label}</span>
                                        <span className="text-sm font-medium text-white">{item.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}

                {/* Change Password Section */}
                <div className="glass-card overflow-hidden opacity-0 animate-fade-in" style={{ animationDelay: '300ms' }}>
                    <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Lock size={18} className="text-accent-blue" />
                            <h3 className="text-sm font-bold text-white">Security</h3>
                        </div>
                        {!showChangePassword && (
                            <button
                                onClick={() => setShowChangePassword(true)}
                                className="text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
                            >
                                Change Password
                            </button>
                        )}
                    </div>

                    {showChangePassword ? (
                        <form onSubmit={handlePasswordChange} className="p-6 space-y-4">
                            {passwordMessage && (
                                <div
                                    className={`p-3 rounded-lg flex items-center gap-2 text-sm ${
                                        passwordMessage.type === 'success'
                                            ? 'bg-green-500/10 text-green-400'
                                            : 'bg-red-500/10 text-red-400'
                                    }`}
                                >
                                    {passwordMessage.type === 'success' ? (
                                        <Check size={16} />
                                    ) : (
                                        <AlertCircle size={16} />
                                    )}
                                    {passwordMessage.text}
                                </div>
                            )}

                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Current Password</label>
                                <input
                                    type="password"
                                    required
                                    value={passwordData.old_password}
                                    onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                                    className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                                    disabled={isChangingPassword}
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-slate-400 mb-2">New Password</label>
                                <input
                                    type="password"
                                    required
                                    minLength={6}
                                    value={passwordData.new_password}
                                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                                    className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                                    disabled={isChangingPassword}
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Confirm New Password</label>
                                <input
                                    type="password"
                                    required
                                    minLength={6}
                                    value={passwordData.confirm_password}
                                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                                    className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                                    disabled={isChangingPassword}
                                />
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    type="submit"
                                    disabled={isChangingPassword}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isChangingPassword ? 'Changing...' : 'Change Password'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowChangePassword(false);
                                        setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
                                        setPasswordMessage(null);
                                    }}
                                    disabled={isChangingPassword}
                                    className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    ) : (
                        <div className="px-6 py-4">
                            <p className="text-sm text-slate-400">••••••••••••</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
