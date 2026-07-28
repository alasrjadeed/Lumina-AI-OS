import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { ThemeProvider } from './components/ui/ThemeToggle';
import Layout from './components/Layout';
import ToastContainer from './components/ui/Toast';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Chat = lazy(() => import('./pages/Chat'));
const CodeGenerator = lazy(() => import('./pages/CodeGenerator'));
const Agents = lazy(() => import('./pages/Agents'));
const CRM = lazy(() => import('./pages/CRM'));
const FileManager = lazy(() => import('./pages/FileManager'));
const SEOToolkit = lazy(() => import('./pages/SEOToolkit'));
const AndroidManager = lazy(() => import('./pages/AndroidManager'));
const WhatsAppMessenger = lazy(() => import('./pages/WhatsAppMessenger'));
const Automation = lazy(() => import('./pages/Automation'));
const CodeReview = lazy(() => import('./pages/CodeReview'));
const SettingsEditor = lazy(() => import('./pages/SettingsEditor'));
const UserManagement = lazy(() => import('./pages/UserManagement'));
const BrowserAgent = lazy(() => import('./pages/BrowserAgent'));
const DataVault = lazy(() => import('./pages/DataVault'));
const WhatsAppBusiness = lazy(() => import('./pages/WhatsAppBusiness'));
const SocialManager = lazy(() => import('./pages/SocialManager'));
const ContentWriter = lazy(() => import('./pages/ContentWriter'));
const VoiceAssistant = lazy(() => import('./pages/VoiceAssistant'));
const LearningAgent = lazy(() => import('./pages/LearningAgent'));
const SelfTester = lazy(() => import('./pages/SelfTester'));
const TaskQueue = lazy(() => import('./pages/TaskQueue'));
const AutonomousEmployee = lazy(() => import('./pages/AutonomousEmployee'));
const Vision = lazy(() => import('./pages/Vision'));
const DesktopControl = lazy(() => import('./pages/DesktopControl'));
const CodingAgent = lazy(() => import('./pages/CodingAgent'));
const MultiAgent = lazy(() => import('./pages/MultiAgent'));
const Projects = lazy(() => import('./pages/Projects'));
const VisualFlows = lazy(() => import('./pages/VisualFlows'));
const Help = lazy(() => import('./pages/Help'));
const SkillsPresets = lazy(() => import('./pages/SkillsPresets'));
const LeadGen = lazy(() => import('./pages/LeadGen'));
const EmailCampaigns = lazy(() => import('./pages/EmailCampaigns'));
const MarketingHub = lazy(() => import('./pages/MarketingHub'));
const AnalyticsDashboard = lazy(() => import('./pages/AnalyticsDashboard'));
const AuditLog = lazy(() => import('./pages/AuditLog'));
const VideoStudio = lazy(() => import('./pages/VideoStudio'));
const About = lazy(() => import('./pages/About'));
const Goals = lazy(() => import('./pages/Goals'));
const MemoryTree = lazy(() => import('./pages/MemoryTree'));
const WorkflowEditor = lazy(() => import('./pages/WorkflowEditor'));
const MeetingAgents = lazy(() => import('./pages/MeetingAgents'));
const MessagingChannels = lazy(() => import('./pages/MessagingChannels'));
const ModelRouting = lazy(() => import('./pages/ModelRouting'));
const AgentMemory = lazy(() => import('./pages/AgentMemory'));
const MultiModal = lazy(() => import('./pages/MultiModal'));
const RAGPipeline = lazy(() => import('./pages/RAGPipeline'));
const AgentChaining = lazy(() => import('./pages/AgentChaining'));
const ToolFramework = lazy(() => import('./pages/ToolFramework'));
const AgentBuilder = lazy(() => import('./pages/AgentBuilder'));
const Brain = lazy(() => import('./pages/Brain'));

function PageLoader() {
  return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-3 border-[var(--border-primary)] border-t-[var(--brand-500)] rounded-full animate-spin" /></div>;
}

const pages: Record<string, React.LazyExoticComponent<React.ComponentType<any>>> = {
  '/': Dashboard, '/chat': Chat, '/code': CodeGenerator, '/agents': Agents,
  '/crm': CRM, '/files': FileManager, '/seo': SEOToolkit, '/android': AndroidManager,
  '/whatsapp': WhatsAppMessenger, '/automation': Automation, '/code/review': CodeReview,
  '/settings': SettingsEditor, '/users': UserManagement, '/browser/agent': BrowserAgent,
  '/vault': DataVault, '/whatsapp/business': WhatsAppBusiness, '/social': SocialManager,
  '/writer': ContentWriter, '/assistant': VoiceAssistant, '/learning': LearningAgent,
  '/tester': SelfTester, '/queue': TaskQueue, '/employee': AutonomousEmployee,
  '/vision': Vision, '/desktop': DesktopControl, '/coding-agent': CodingAgent,
  '/multi-agent': MultiAgent, '/projects': Projects, '/visual-flows': VisualFlows,
  '/help': Help, '/skills': SkillsPresets, '/leads': LeadGen, '/email': EmailCampaigns,
  '/marketing': MarketingHub, '/analytics': AnalyticsDashboard, '/audit': AuditLog,
  '/video-studio': VideoStudio, '/about': About,   '/goals': Goals, '/memory-tree': MemoryTree, '/workflow-editor': WorkflowEditor,
  '/meetings': MeetingAgents, '/channels': MessagingChannels,   '/model-routing': ModelRouting, '/agent-memory': AgentMemory,
  '/multi-modal': MultiModal, '/rag-pipeline': RAGPipeline,
  '/agent-chaining': AgentChaining, '/tools': ToolFramework,
  '/agent-builder': AgentBuilder,
  '/brain': Brain,
};

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            {Object.entries(pages).map(([path, Component]) => (
              <Route key={path} path={path} element={<Suspense fallback={<PageLoader />}><Component /></Suspense>} />
            ))}
          </Routes>
        </Layout>
        <ToastContainer />
      </BrowserRouter>
    </ThemeProvider>
  );
}
