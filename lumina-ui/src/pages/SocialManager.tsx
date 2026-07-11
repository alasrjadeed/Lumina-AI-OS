import { useEffect, useState } from 'react';
import {
  Globe, Camera, Plus, Send,
  BarChart3, Loader2, CheckCircle, XCircle,
  MessageSquare, Users,
  Search, RefreshCw, Heart, Share2, MessageCircle,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/social';

interface SPage {
  id: string; name: string; platform: string; url: string;
  category: string; followers: number; status: string;
}

interface SPost {
  id: string; platform: string; content: string; status: string;
  scheduled: number; engagement: { likes: number; comments: number; shares: number; };
}

const PLATFORM_ICONS: Record<string, typeof Globe> = { facebook: Globe, instagram: Camera, twitter: MessageSquare, linkedin: Users, tiktok: Camera, youtube: Camera };

export default function SocialManager() {
  const [tab, setTab] = useState('dashboard');
  const [pages, setPages] = useState<SPage[]>([]);
  const [posts, setPosts] = useState<SPost[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [newPostContent, setNewPostContent] = useState('');
  const [newPostPlatform, setNewPostPlatform] = useState('facebook');
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [pagesRes, postsRes] = await Promise.all([
        fetch(`${BASE}/pages`).then(r => r.json()).catch(() => ({ pages: [] })),
        fetch(`${BASE}/posts`).then(r => r.json()).catch(() => ({ posts: [] })),
      ]);
      setPages(pagesRes.pages || []);
      setPosts(postsRes.posts || []);
      const totalPages = (pagesRes.pages || []).length;
      const totalFollowers = (pagesRes.pages || []).reduce((a: number, p: SPage) => a + (p.followers || 0), 0);
      const publishedPosts = (postsRes.posts || []).filter((p: SPost) => p.status === 'published').length;
      const totalEngagement = (postsRes.posts || []).reduce((a: number, p: SPost) => a + (p.engagement?.likes || 0) + (p.engagement?.comments || 0) + (p.engagement?.shares || 0), 0);
      setStats({ totalPages, totalFollowers, publishedPosts, totalEngagement });
    } catch (e: any) {
      addToast(`Failed to load social data: ${e.message}`, 'error');
    } finally { setLoading(false); }
  };

  const createPost = async () => {
    if (!newPostContent.trim()) return;
    try {
      const res = await fetch(`${BASE}/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: newPostPlatform, content: newPostContent }),
      });
      if (!res.ok) throw new Error('Failed');
      addToast('Post created', 'success');
      setShowCreatePost(false);
      setNewPostContent('');
      loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  };

  const filteredPosts = posts.filter(p =>
    p.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader icon={Globe} title="Social Manager" description="Manage social media pages and posts" />
        <div className="flex items-center justify-center flex-1">
          <Loader2 className="w-6 h-6 text-lumina-400 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Globe} title="Social Manager" description="Manage social media pages and posts" />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['dashboard', 'pages', 'posts'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'dashboard' ? <BarChart3 className="w-3.5 h-3.5" /> : t === 'pages' ? <Globe className="w-3.5 h-3.5" /> : <MessageSquare className="w-3.5 h-3.5" />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 space-y-5">
        {tab === 'dashboard' && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Connected Pages', value: stats?.totalPages || 0, icon: Globe, color: 'from-lumina-500 to-lumina-700' },
                { label: 'Total Followers', value: (stats?.totalFollowers || 0).toLocaleString(), icon: Users, color: 'from-blue-500 to-blue-700' },
                { label: 'Published Posts', value: stats?.publishedPosts || 0, icon: Send, color: 'from-emerald-500 to-emerald-700' },
                { label: 'Total Engagement', value: (stats?.totalEngagement || 0).toLocaleString(), icon: Heart, color: 'from-rose-500 to-rose-700' },
              ].map(s => (
                <div key={s.label} className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${s.color} p-[1px]`}>
                  <div className="rounded-2xl bg-slate-950/90 backdrop-blur-sm p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-[10px] font-medium text-white/60 uppercase tracking-wider">{s.label}</p>
                        <p className="text-lg font-bold text-white mt-1">{s.value}</p>
                      </div>
                      <s.icon className="w-5 h-5 text-white/30" />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardSection label="Connected Pages">
                  {pages.length === 0 ? (
                    <p className="text-xs text-slate-500 py-4 text-center">No pages connected</p>
                  ) : (
                    <div className="space-y-2">
                      {pages.slice(0, 5).map(p => {
                        const Icon = PLATFORM_ICONS[p.platform] || Globe;
                        return (
                          <div key={p.id} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.02] text-xs">
                            <Icon className="w-4 h-4 text-slate-400" />
                            <span className="flex-1 text-slate-300 truncate">{p.name}</span>
                            <span className="text-slate-500">{p.followers?.toLocaleString() || 0}</span>
                            {p.status === 'active' ? <CheckCircle className="w-3 h-3 text-emerald-400" /> : <XCircle className="w-3 h-3 text-red-400" />}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardSection>
              </Card>

              <Card>
                <CardSection label="Recent Posts">
                  {posts.length === 0 ? (
                    <p className="text-xs text-slate-500 py-4 text-center">No posts yet</p>
                  ) : (
                    <div className="space-y-2">
                      {posts.slice(0, 5).map(p => (
                        <div key={p.id} className="px-3 py-2 rounded-lg bg-white/[0.02] text-xs">
                          <p className="text-slate-300 truncate">{p.content}</p>
                          <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-500">
                            <span className="flex items-center gap-1"><Heart className="w-3 h-3" />{p.engagement?.likes || 0}</span>
                            <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" />{p.engagement?.comments || 0}</span>
                            <span className="flex items-center gap-1"><Share2 className="w-3 h-3" />{p.engagement?.shares || 0}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardSection>
              </Card>
            </div>
          </>
        )}

        {tab === 'pages' && (
          <CardSection label="Connected Pages" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search pages..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-40"
                />
              </div>
              <button onClick={loadAll} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white"><RefreshCw className="w-3.5 h-3.5" /></button>
            </div>
          }>
            {pages.length === 0 ? (
              <div className="text-center py-12">
                <Globe className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No social pages connected</p>
                <p className="text-xs text-slate-600 mt-1">Connect your social media accounts to manage them here</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {pages.map(p => {
                  const Icon = PLATFORM_ICONS[p.platform] || Globe;
                  return (
                    <div key={p.id} className="p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-xl bg-lumina-500/10 flex items-center justify-center">
                          <Icon className="w-5 h-5 text-lumina-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white truncate">{p.name}</p>
                          <p className="text-[10px] text-slate-500 capitalize">{p.platform} · {p.category}</p>
                          <div className="flex items-center gap-3 mt-2 text-xs">
                            <span className="flex items-center gap-1 text-slate-400"><Users className="w-3 h-3" />{p.followers?.toLocaleString() || 0}</span>
                            {p.status === 'active' ? (
                              <span className="flex items-center gap-1 text-emerald-400"><CheckCircle className="w-3 h-3" />Active</span>
                            ) : (
                              <span className="flex items-center gap-1 text-red-400"><XCircle className="w-3 h-3" />Offline</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardSection>
        )}

        {tab === 'posts' && (
          <CardSection label="Posts" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search posts..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-40"
                />
              </div>
              <button onClick={() => setShowCreatePost(!showCreatePost)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
              ><Plus className="w-3.5 h-3.5" />New Post</button>
            </div>
          }>
            {showCreatePost && (
              <div className="p-4 mb-4 rounded-xl border border-lumina-500/20 bg-lumina-500/5 space-y-3">
                <select value={newPostPlatform} onChange={e => setNewPostPlatform(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lumina-500/50"
                >{['facebook','instagram','twitter','linkedin','tiktok'].map(p => <option key={p} value={p}>{p}</option>)}</select>
                <textarea value={newPostContent} onChange={e => setNewPostContent(e.target.value)}
                  placeholder="What do you want to share?"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 resize-none h-24"
                />
                <div className="flex gap-2">
                  <button onClick={createPost} disabled={!newPostContent.trim()}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 disabled:opacity-40 transition-colors"
                  ><Send className="w-3.5 h-3.5" />Publish</button>
                  <button onClick={() => setShowCreatePost(false)}
                    className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:bg-white/5"
                  >Cancel</button>
                </div>
              </div>
            )}

            {filteredPosts.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No posts yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredPosts.map(p => (
                  <div key={p.id} className="p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all">
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${p.status === 'published' ? 'bg-emerald-400' : p.status === 'scheduled' ? 'bg-amber-400' : 'bg-slate-500'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-slate-400 capitalize">{p.platform}</span>
                          <span className="text-[10px] text-slate-500 capitalize">{p.status}</span>
                          {p.scheduled && <span className="text-[10px] text-slate-500">{new Date(p.scheduled).toLocaleDateString()}</span>}
                        </div>
                        <p className="text-sm text-slate-300 whitespace-pre-wrap">{p.content}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                          <span className="flex items-center gap-1"><Heart className="w-3 h-3" />{p.engagement?.likes || 0}</span>
                          <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" />{p.engagement?.comments || 0}</span>
                          <span className="flex items-center gap-1"><Share2 className="w-3 h-3" />{p.engagement?.shares || 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardSection>
        )}
      </div>
    </div>
  );
}
