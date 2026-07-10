import { useEffect, useState, useRef, useCallback } from 'react';
import { Mic, Send, Bot, User, Loader2, Sparkles, Globe, FileText, BarChart3, Search, Smartphone, Terminal, MessageSquare, ShoppingBag, PenTool, Zap, Volume2, Ear, Radio, Square } from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';

const actionIcons: Record<string, React.FC<{ className?: string }>> = {
  content: PenTool, browser: Globe, crm: BarChart3, seo: Search,
  social: MessageSquare, whatsapp: ShoppingBag, vault: FileText,
  android: Smartphone, files: Terminal, chat: Bot, code: PenTool,
  pipeline: Zap, email: MessageSquare, system: Terminal,
};

interface VoiceMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  action?: string;
  audioUrl?: string;
  timestamp: number;
}

export default function VoiceAssistant() {
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [continuousMode, setContinuousMode] = useState(false);
  const [wakeWordMode, setWakeWordMode] = useState(true);
  const [audioLevel, setAudioLevel] = useState(0);
  const [status, setStatus] = useState('Ready');
  const [voiceStatus, setVoiceStatus] = useState<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const listeningRef = useRef(false);
  const animFrameRef = useRef<number>(0);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    fetch('/voice/status').then(r => r.json()).then(setVoiceStatus).catch(() => {});
  }, []);

  const addMessage = useCallback((msg: VoiceMessage) => {
    setMessages(m => [...m, msg]);
  }, []);

  useEffect(() => {
    listeningRef.current = listening;
  }, [listening]);

  const startAudioRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      mediaRecorderRef.current = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      mediaRecorderRef.current.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        await sendAudio(blob);
      };

      mediaRecorderRef.current.start();
      setListening(true);

      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      source.connect(analyser);
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateLevel = () => {
        if (!listeningRef.current) return;
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
        setAudioLevel(Math.min(100, avg * 2));
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
    } catch {
      setStatus('Mic error');
    }
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach(t => t.stop());
    audioContextRef.current?.close();
    cancelAnimationFrame(animFrameRef.current);
    setListening(false);
    setAudioLevel(0);
    setStatus('Processing...');
  };

  const sendAudio = async (blob: Blob) => {
    const form = new FormData();
    form.append('file', blob, 'voice.webm');
    addMessage({ id: Date.now().toString(), role: 'user', content: '🎤 Audio recording...', timestamp: Date.now() });
    setLoading(true);
    try {
      const res = await fetch('/voice/listen', { method: 'POST', body: form });
      const data = await res.json();
      setMessages(m => m.slice(0, -1));
      if (data.text) {
        addMessage({ id: Date.now().toString(), role: 'user', content: data.text, timestamp: Date.now() });
      }
      addMessage({
        id: (Date.now() + 1).toString(), role: 'assistant', content: data.reply || 'Done.',
        action: data.intent?.category, timestamp: Date.now(),
      });
      setStatus(`Done (${data.intent?.action || 'completed'})`);
    } catch {
      setStatus('Error processing audio');
    }
    setLoading(false);
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    addMessage({ id: Date.now().toString(), role: 'user', content: text, timestamp: Date.now() });
    setLoading(true);
    setStatus('Processing command...');
    try {
      const res = await fetch('/voice/command', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, play: false }),
      });
      const data = await res.json();
      addMessage({
        id: (Date.now() + 1).toString(), role: 'assistant',
        content: data.reply || 'Done.', action: data.intent?.category,
        timestamp: Date.now(),
      });
      setStatus(`Done (${data.intent?.action || 'completed'})`);
    } catch {
      addMessage({ id: Date.now().toString(), role: 'assistant', content: 'Error processing command', timestamp: Date.now() });
      setStatus('Error');
    }
    setLoading(false);
  };

  const toggleContinuousMode = async () => {
    if (!continuousMode) {
      setContinuousMode(true);
      setStatus(`Starting voice control (wake: ${wakeWordMode})...`);
      try {
        const res = await fetch(`/voice/listen/start?wake_word=${wakeWordMode}`, { method: 'GET' });
        const data = await res.json();
        setStatus(data.message || 'Listening...');
      } catch {
        setStatus('Failed to start');
        setContinuousMode(false);
      }
    } else {
      await fetch('/voice/listen/stop', { method: 'POST' });
      setContinuousMode(false);
      setStatus('Stopped');
    }
  };

  return (
    <div className="flex gap-6 h-full p-6">
      <div className="flex-1 flex flex-col min-w-0">
        <PageHeader
          icon={Ear}
          title="Voice Control"
          description={status}
          status={
            <div className="flex items-center gap-2">
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                voiceStatus?.recorder_available ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {voiceStatus?.recorder_available ? 'Mic Ready' : 'No Mic'}
              </span>
              {loading && <Loader2 className="w-4 h-4 text-lumina-400 animate-spin" />}
            </div>
          }
        />

        {listening && (
          <div className="flex items-center justify-center gap-0.5 py-4 animate-fade-in">
            {Array.from({ length: 32 }).map((_, i) => (
              <div key={i} className="w-1 bg-red-400 rounded-full transition-all duration-75"
                style={{
                  height: `${Math.max(4, (audioLevel / 100) * (Math.sin(i * 0.5 + Date.now() * 0.01) * 0.5 + 0.5) * 40)}px`,
                  opacity: 0.3 + (audioLevel / 100) * 0.7,
                }}
              />
            ))}
            <span className="text-xs text-red-400 ml-3 animate-pulse">Recording...</span>
          </div>
        )}

        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="text-center mt-12 animate-fade-in">
              <Sparkles className="w-12 h-12 mx-auto mb-3 text-lumina-400/50" />
              <p className="text-slate-400 text-sm mb-3">Try speaking or typing:</p>
              <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
                {[
                  'Add my new products to WhatsApp Business',
                  'Create a School ERP system',
                  'Build an Amazon Clone',
                  'Analyze SEO for my website',
                  'Send an email to the team',
                ].map((ex, i) => (
                  <button key={i} onClick={() => setInput(ex)}
                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-slate-400 transition-colors border border-white/5">
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) => {
            const Icon = actionIcons[m.action || ''] || (m.role === 'assistant' ? Bot : User);
            return (
              <div key={m.id} className={`flex gap-3 animate-fade-in ${m.role === 'assistant' ? '' : 'flex-row-reverse'}`}>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${
                  m.role === 'assistant' ? 'bg-lumina-600 shadow-lumina-500/20' : 'bg-slate-700'
                }`}>
                  {m.role === 'assistant' && m.action === 'pipeline' ? (
                    <Zap className="w-4 h-4 text-yellow-300" />
                  ) : (
                    <Icon className="w-4 h-4 text-white" />
                  )}
                </div>
                <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === 'assistant'
                    ? 'bg-white/5 border border-white/5 text-slate-200'
                    : 'bg-lumina-600/20 text-lumina-200 border border-lumina-500/20'
                }`}>
                  {m.content}
                  {m.audioUrl && (
                    <button className="ml-2 text-lumina-400 hover:text-lumina-300 inline-flex items-center gap-1 text-xs">
                      <Volume2 className="w-3 h-3" /> Play
                    </button>
                  )}
                </div>
              </div>
            );
          })}
          {loading && !listening && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-xl bg-lumina-600 flex items-center justify-center shadow-lg shadow-lumina-500/20">
                <Loader2 className="w-4 h-4 text-white animate-spin" />
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl px-4 py-3 flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="space-y-2 pt-3 border-t border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <button
              onClick={toggleContinuousMode}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                continuousMode
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : 'bg-white/5 text-slate-400 hover:text-slate-300 border border-white/5'
              }`}
            >
              <Radio className={`w-3 h-3 ${continuousMode ? 'animate-pulse' : ''}`} />
              {continuousMode ? 'Stop Listening' : 'Continuous Mode'}
            </button>
            {continuousMode && (
              <button
                onClick={() => {
                  setWakeWordMode(!wakeWordMode);
                  fetch(`/voice/listen/start?wake_word=${!wakeWordMode}`, { method: 'GET' });
                }}
                className={`px-2 py-1 rounded text-[10px] ${
                  wakeWordMode ? 'bg-lumina-600/20 text-lumina-400' : 'bg-white/5 text-slate-500'
                }`}
              >
                Wake: "{wakeWordMode ? 'Lumina' : 'off'}"
              </button>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onMouseDown={startAudioRecording}
              onMouseUp={stopAudioRecording}
              onMouseLeave={() => listening && stopAudioRecording()}
              onTouchStart={startAudioRecording}
              onTouchEnd={stopAudioRecording}
              className={`p-2.5 rounded-xl transition-all select-none ${
                listening
                  ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 scale-110'
                  : 'bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10'
              }`}
            >
              {listening ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50 placeholder:text-slate-600"
              placeholder={listening ? 'Recording...' : 'Type a command or hold mic to speak...'}
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()} />
            <button onClick={send} disabled={loading || !input.trim()}
              className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-4 py-2.5 transition-all">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      <div className="w-56 shrink-0 hidden lg:block space-y-3">
        <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider mb-3">Voice System</p>
        <Card hover={false}>
          <div className="space-y-1.5">
            <p className="text-[10px] text-slate-500 uppercase">Status</p>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${voiceStatus?.listening ? 'bg-green-400 animate-pulse' : 'bg-slate-600'}`} />
              <span className="text-xs text-slate-300">{voiceStatus?.listening ? 'Listening' : 'Idle'}</span>
            </div>
            <p className="text-[10px] text-slate-500">STT: {voiceStatus?.stt_providers?.[0]?.model || voiceStatus?.stt_providers?.[0]?.model_size || 'None'}</p>
            <p className="text-[10px] text-slate-500">Voices: {Object.keys(voiceStatus?.tts_voices || {}).length} available</p>
          </div>
        </Card>

        <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider mt-4">Smart Actions</p>
        {[
          { name: 'Pipeline', desc: 'Build entire projects from description', icon: Zap },
          { name: 'Code', desc: 'Generate, review, and fix code', icon: PenTool },
          { name: 'Browser', desc: 'Navigate, extract, automate', icon: Globe },
          { name: 'WhatsApp', desc: 'Send messages, manage catalog', icon: ShoppingBag },
          { name: 'Email', desc: 'Draft, send, manage inbox', icon: MessageSquare },
          { name: 'System', desc: 'Orchestrate multi-agent tasks', icon: Terminal },
        ].map(({ name, desc, icon: Icon }) => (
          <div key={name} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
            <Icon className="w-3.5 h-3.5 text-lumina-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-slate-300 font-medium">{name}</p>
              <p className="text-[10px] text-slate-500 leading-tight">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
