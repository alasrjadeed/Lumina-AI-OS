import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import CodeGenerator from './pages/CodeGenerator';
import Agents from './pages/Agents';
import CRM from './pages/CRM';
import FileManager from './pages/FileManager';
import SEOToolkit from './pages/SEOToolkit';
import AndroidManager from './pages/AndroidManager';
import WhatsAppMessenger from './pages/WhatsAppMessenger';
import Automation from './pages/Automation';
import CodeReview from './pages/CodeReview';
import SettingsEditor from './pages/SettingsEditor';
import UserManagement from './pages/UserManagement';
import BrowserAgent from './pages/BrowserAgent';
import DataVault from './pages/DataVault';
import WhatsAppBusiness from './pages/WhatsAppBusiness';
import SocialManager from './pages/SocialManager';
import ContentWriter from './pages/ContentWriter';
import VoiceAssistant from './pages/VoiceAssistant';
import LearningAgent from './pages/LearningAgent';
import SelfTester from './pages/SelfTester';
import TaskQueue from './pages/TaskQueue';
import AutonomousEmployee from './pages/AutonomousEmployee';
import Vision from './pages/Vision';
import DesktopControl from './pages/DesktopControl';
import CodingAgent from './pages/CodingAgent';
import MultiAgent from './pages/MultiAgent';
import Projects from './pages/Projects';
import VisualFlows from './pages/VisualFlows';
import ToastContainer from './components/ui/Toast';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/code" element={<CodeGenerator />} />
          <Route path="/code/review" element={<CodeReview />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/crm" element={<CRM />} />
          <Route path="/files" element={<FileManager />} />
          <Route path="/seo" element={<SEOToolkit />} />
          <Route path="/android" element={<AndroidManager />} />
          <Route path="/whatsapp" element={<WhatsAppMessenger />} />
          <Route path="/automation" element={<Automation />} />
          <Route path="/settings" element={<SettingsEditor />} />
          <Route path="/users" element={<UserManagement />} />
          <Route path="/browser/agent" element={<BrowserAgent />} />
          <Route path="/vault" element={<DataVault />} />
          <Route path="/whatsapp/business" element={<WhatsAppBusiness />} />
          <Route path="/social" element={<SocialManager />} />
          <Route path="/writer" element={<ContentWriter />} />
          <Route path="/assistant" element={<VoiceAssistant />} />
          <Route path="/learning" element={<LearningAgent />} />
          <Route path="/tester" element={<SelfTester />} />
          <Route path="/queue" element={<TaskQueue />} />
          <Route path="/employee" element={<AutonomousEmployee />} />
          <Route path="/vision" element={<Vision />} />
          <Route path="/desktop" element={<DesktopControl />} />
          <Route path="/coding-agent" element={<CodingAgent />} />
          <Route path="/multi-agent" element={<MultiAgent />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/visual-flows" element={<VisualFlows />} />
        </Routes>
      </Layout>
      <ToastContainer />
    </BrowserRouter>
  );
}
