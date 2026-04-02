import  { useState } from 'react';
import { MessageSquare, UploadCloud, Menu } from 'lucide-react';
import ChatPage from './pages/ChatPage';
import UploadPage from './pages/UploadPage';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'upload', label: 'Upload', icon: UploadCloud },
  ];

  return (
    <div className="flex h-screen bg-white font-sans antialiased text-zinc-900 overflow-hidden">
      
      {/* Sidebar */}
      <aside 
        className={`relative border-r border-zinc-200 flex flex-col transition-all duration-300 ease-in-out z-30 ${
          isCollapsed ? 'w-20' : 'w-72'
        }`}
      >
        {/* SIDEBAR HEADER: Aligned to match nav items below */}
        <div className={`px-6 h-20 flex items-center mb-2 ${!isCollapsed ? 'justify-between' : ''}`}>
          {!isCollapsed ? (
            <>
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-full border border-zinc-200 bg-black shadow-sm shrink-0">
                 
                </div>
              </div>
              <button 
                onClick={() => setIsCollapsed(true)}
                className="p-1.5 hover:bg-zinc-100 rounded-full text-black transition-colors cursor-pointer"
              >
                <Menu size={20} />
              </button>
            </>
          ) : (
            /* Using a fixed width container that matches the icon alignment of the nav buttons below */
            <div className="relative group w-8 h-8 flex items-center justify-center mx-auto">
              {/* Branding icon shown by default */}
              <div className="absolute inset-0 flex items-center justify-center bg-black w-8 h-8 rounded-full border border-zinc-200 shadow-sm transition-opacity duration-200 group-hover:opacity-0">
               
              </div>
              {/* Toggle icon shown on hover */}
              <button 
                onClick={() => setIsCollapsed(false)}
                className="absolute inset-0 flex items-center justify-center w-8 h-8text-black opacity-0 hover:bg-zinc-100 rounded-full group-hover:opacity-100 transition-all duration-200 cursor-pointer"
              >
                <Menu size={20} />
              </button>
            </div>
          )}
        </div>

        <nav className="flex-1 px-3 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 transition-all duration-200 ${
                isCollapsed ? 'justify-center px-0 py-4' : 'px-4 py-4'
              } rounded-xl ${
                activeTab === item.id 
                ? 'bg-gray-100 text-black' 
                : 'text-zinc-600 hover:bg-gray-50 hover:text-zinc-900'
              }`}
            >
              <item.icon size={20} />
              {!isCollapsed && <span className="font-medium text-sm">{item.label}</span>}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative bg-white overflow-hidden">
        
        {/* Global Header */}
        <header className="flex items-center justify-between px-8 py-4 border-b border-zinc-100 bg-white/80 backdrop-blur-md z-20">
          <div className="flex items-center gap-2">
            <h1 className="font-normal text-zinc-900 text-xl">Personal Assistant</h1>
          </div>
          
          <button 
            onClick={() => setActiveTab('upload')}
            className="flex items-center gap-2 px-4 py-2 cursor-pointer text-zinc-700 rounded-full transition-all text-lg font-semibold active:scale-95"
          >
            <UploadCloud size={16} />
            Upload
          </button>
        </header>

        {activeTab === 'chat' ? (
          <ChatPage isCollapsed={isCollapsed} />
        ) : (
          <UploadPage />
        )}
      </main>
    </div>
  );
}

export default App;