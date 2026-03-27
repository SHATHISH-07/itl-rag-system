import React, { useState } from 'react';
import { MessageSquare, UploadCloud, Database } from 'lucide-react';
import ChatPage from './pages/ChatPage';
import UploadPage from './pages/UploadPage';

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="flex h-screen bg-white font-sans antialiased text-slate-900">
      {/* Sidebar - Fixed width 72 (18rem) */}
      <aside className="w-72 bg-slate-900 text-white flex flex-col shadow-xl z-30">
        <div className="p-8 flex items-center gap-3 border-b border-slate-800">
          <Database className="text-blue-400" size={24} />
          <h1 className="text-lg font-bold tracking-tight uppercase">Knowledge RAG</h1>
        </div>

        <nav className="flex-1 p-4 space-y-2 mt-4">
          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'chat' 
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <MessageSquare size={18} />
            <span className="font-medium text-sm">Ask Documents</span>
          </button>

          <button
            onClick={() => setActiveTab('upload')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'upload' 
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <UploadCloud size={18} />
            <span className="font-medium text-sm">Upload Knowledge</span>
          </button>
        </nav>

        <div className="p-6 border-t border-slate-800">
          <div className="flex items-center gap-2 text-[10px] text-slate-500 uppercase tracking-widest font-bold">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
            System Online
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-zinc-50">
        {activeTab === 'chat' ? <ChatPage /> : <UploadPage />}
      </main>
    </div>
  );
}

export default App;