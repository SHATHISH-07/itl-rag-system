import { useState } from 'react';
import Sidebar from './components/SideBar';
import Navbar from './components/Navbar';
import ChatPage from './pages/ChatPage';
import UploadPage from './pages/UploadPage';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <div className="flex h-screen bg-white font-sans antialiased text-zinc-900 overflow-hidden">
      <Sidebar 
        isCollapsed={isCollapsed} 
        setIsCollapsed={setIsCollapsed}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <Navbar 
          onMenuClick={() => setIsMobileOpen(true)} 
          setActiveTab={setActiveTab} 
        />
        
        <main className="flex-1 relative overflow-hidden bg-white">
          {activeTab === 'chat' ? (
            <ChatPage isCollapsed={isCollapsed} />
          ) : (
            <div className="p-4 md:p-8 h-full overflow-y-auto">
              <UploadPage />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;