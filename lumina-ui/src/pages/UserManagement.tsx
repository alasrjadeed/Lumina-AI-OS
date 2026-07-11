import { useState, useEffect } from 'react';
import {
  Users, UserPlus, LogIn, Search,
  Loader2, RefreshCw, Eye, EyeOff,
  Ban, Check, Copy, User,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/auth';

interface AppUser {
  username: string; roles: string[]; disabled?: boolean; created?: string;
}

export default function UserManagement() {
  const [tab, setTab] = useState('users');
  const [users, setUsers] = useState<AppUser[]>([]);
  const [loading, setLoading] = useState(false);

  // Register form
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirm, setRegConfirm] = useState('');
  const [regRoles, setRegRoles] = useState('user');
  const [regLoading, setRegLoading] = useState(false);

  // Login form
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const { addToast } = useToast();

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/users`);
      const data = await res.json();
      setUsers(data.users || []);
    } catch {} finally { setLoading(false); }
  };

  const register = async () => {
    if (regPassword !== regConfirm) { addToast('Passwords do not match', 'error'); return; }
    setRegLoading(true);
    try {
      const res = await fetch(`${BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: regUsername, password: regPassword, roles: regRoles.split(',').map(r => r.trim()) }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Registration failed');
      addToast('User registered', 'success');
      setRegUsername(''); setRegPassword(''); setRegConfirm(''); setRegRoles('user');
      loadUsers();
    } catch (e: any) { addToast(e.message, 'error'); }
    finally { setRegLoading(false); }
  };

  const login = async () => {
    setLoginLoading(true);
    try {
      const res = await fetch(`${BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Login failed');
      const data = await res.json();
      setToken(data.token || data.access_token || '');
      addToast('Login successful', 'success');
    } catch (e: any) { addToast(e.message, 'error'); }
    finally { setLoginLoading(false); }
  };

  const toggleUser = async (username: string, disable: boolean) => {
    try {
      const endpoint = disable ? '/users/disable' : '/users/enable';
      await fetch(`${BASE}${endpoint}?username=${encodeURIComponent(username)}`, { method: 'POST' });
      addToast(`${username} ${disable ? 'disabled' : 'enabled'}`, 'success');
      loadUsers();
    } catch (e: any) { addToast(e.message, 'error'); }
  };

  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Users} title="User Management" description="Register, login, and manage system users" />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['users', 'register', 'login'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'users' ? <Users className="w-3.5 h-3.5" /> : t === 'register' ? <UserPlus className="w-3.5 h-3.5" /> : <LogIn className="w-3.5 h-3.5" />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {tab === 'users' && (
          <CardSection label="System Users" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search users..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-40"
                />
              </div>
              <button onClick={loadUsers} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          }>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-5 h-5 text-lumina-400 animate-spin" />
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No users found</p>
                <p className="text-xs text-slate-600 mt-1">Register a user to get started</p>
              </div>
            ) : (
              <div className="space-y-1 divide-y divide-white/[0.03]">
                <div className="flex items-center gap-2 px-3 py-2 text-[10px] text-slate-500 uppercase tracking-wider">
                  <div className="flex-1">Username</div>
                  <div className="w-24">Roles</div>
                  <div className="w-20">Status</div>
                  <div className="w-24">Actions</div>
                </div>
                {filteredUsers.map(u => (
                  <div key={u.username} className="flex items-center gap-2 px-3 py-2.5 text-xs hover:bg-white/[0.02] transition-colors group">
                    <div className="w-8 h-8 rounded-full bg-lumina-500/10 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-lumina-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{u.username}</p>
                    </div>
                    <div className="w-24 flex flex-wrap gap-1">
                      {(u.roles || ['user']).map(r => (
                        <span key={r} className="text-[10px] px-1.5 py-0.5 rounded bg-lumina-500/10 text-lumina-300 capitalize">{r}</span>
                      ))}
                    </div>
                    <div className="w-20">
                      {u.disabled ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400">Disabled</span>
                      ) : (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">Active</span>
                      )}
                    </div>
                    <div className="w-24 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {u.disabled ? (
                        <button onClick={() => toggleUser(u.username, false)}
                          className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                        ><Check className="w-3 h-3" />Enable</button>
                      ) : (
                        <button onClick={() => toggleUser(u.username, true)}
                          className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                        ><Ban className="w-3 h-3" />Disable</button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardSection>
        )}

        {tab === 'register' && (
          <div className="max-w-md space-y-5">
            <Card>
              <CardSection label="Register New User">
                <div className="space-y-4">
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">Username</label>
                    <input type="text" value={regUsername} onChange={e => setRegUsername(e.target.value)}
                      placeholder="Choose a username" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">Password</label>
                    <input type="password" value={regPassword} onChange={e => setRegPassword(e.target.value)}
                      placeholder="Password" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">Confirm Password</label>
                    <input type="password" value={regConfirm} onChange={e => setRegConfirm(e.target.value)}
                      placeholder="Confirm password" className={`w-full bg-white/5 border rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors ${regConfirm && regPassword !== regConfirm ? 'border-red-500/50' : 'border-white/10 focus:border-lumina-500/50'}`}
                    />
                    {regConfirm && regPassword !== regConfirm && <p className="text-[10px] text-red-400 mt-1">Passwords do not match</p>}
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">Roles (comma-separated)</label>
                    <input type="text" value={regRoles} onChange={e => setRegRoles(e.target.value)}
                      placeholder="user, admin" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                    />
                  </div>
                  <button onClick={register} disabled={regLoading || !regUsername || !regPassword}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-lumina-500 to-lumina-600 rounded-xl text-sm font-medium text-white disabled:opacity-40 hover:from-lumina-400 hover:to-lumina-500 transition-all shadow-lg shadow-lumina-500/20"
                  >{regLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                    {regLoading ? 'Registering...' : 'Register'}
                  </button>
                </div>
              </CardSection>
            </Card>
          </div>
        )}

        {tab === 'login' && (
          <div className="max-w-md space-y-5">
            <Card>
              <CardSection label="Login">
                <div className="space-y-4">
                  <input type="text" value={loginUsername} onChange={e => setLoginUsername(e.target.value)}
                    placeholder="Username" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                  />
                  <input type="password" value={loginPassword} onChange={e => setLoginPassword(e.target.value)}
                    placeholder="Password" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                  />
                  <button onClick={login} disabled={loginLoading || !loginUsername}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-lumina-500 to-lumina-600 rounded-xl text-sm font-medium text-white disabled:opacity-40 hover:from-lumina-400 hover:to-lumina-500 transition-all shadow-lg shadow-lumina-500/20"
                  >{loginLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
                    {loginLoading ? 'Logging in...' : 'Login'}
                  </button>
                </div>
              </CardSection>
            </Card>

            {token && (
              <Card>
                <CardSection label="Authentication Token" action={
                  <button onClick={() => setShowToken(!showToken)} className="p-1 text-slate-500 hover:text-white">
                    {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                }>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 text-[10px] font-mono text-lumina-300 bg-white/[0.03] rounded-lg px-3 py-2 truncate">
                      {showToken ? token : token.slice(0, 20) + '...'}
                    </code>
                    <button onClick={() => { navigator.clipboard.writeText(token); addToast('Token copied', 'success'); }}
                      className="p-2 text-slate-400 hover:text-white"
                    ><Copy className="w-3.5 h-3.5" /></button>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-2">⚠ Store securely. This token grants API access.</p>
                </CardSection>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
