import React, { useState, useEffect, useRef } from 'react';
import { askQuestion } from '../api/api';
import { Send, User, Bot, Plus, X, Loader2 } from 'lucide-react';
import UploadPage from './UploadPage';

const ChatPage = ({ isCollapsed }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const simulateTyping = (fullText) => {
    setMessages((prev) => [...prev, { role: 'bot', text: '', isTyping: true }]);
    let index = 0;
    const speed = 2; // Increased speed for better UX

    const interval = setInterval(() => {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (index < fullText.length) {
          lastMsg.text = fullText.slice(0, index + 1);
          index++;
          return updated;
        } else {
          lastMsg.isTyping = false;
          clearInterval(interval);
          return updated;
        }
      });
    }, speed);
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const response = await askQuestion(currentInput);
      setLoading(false);
      simulateTyping(response.data.answer);
    } catch (error) {
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          text: "<div class='p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-xs'><strong>Error:</strong> Knowledge base connection timed out.</div>"
        }
      ]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      
      {/* Upload Modal Overlay */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <div className="absolute inset-0 bg-zinc-900/60 backdrop-blur-md animate-in fade-in duration-300" onClick={() => setShowUploadModal(false)}></div>
          <div className="relative bg-white w-full max-w-2xl max-h-[90vh] rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-zinc-100">
              <h3 className="text-lg font-bold text-zinc-900">Knowledge Base</h3>
              <button onClick={() => setShowUploadModal(false)} className="p-2 hover:bg-zinc-100 rounded-full text-zinc-400 transition-colors cursor-pointer"><X size={20} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <UploadPage isModal={true} onUploadSuccess={() => setShowUploadModal(false)} />
            </div>
          </div>
        </div>
      )}

      <main className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl mx-auto px-6 pt-12 pb-35">
          
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center animate-in fade-in zoom-in duration-700">
            
              <h2 className="text-4xl font-bold text-zinc-900 tracking-tight mb-3">What are we Refering Today ?</h2>
              <p className="text-zinc-500 text-lg max-w-sm mx-auto leading-relaxed">
                Your AI assistant is ready to process your documents and answer questions.
              </p>
            </div>
          )}

          <div className="flex flex-col gap-8">
            {messages.map((msg, i) => (
              <div 
                key={i} 
                className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-500`}
              >
                <div className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  {/* Avatar */}
                  <div className={`h-10 w-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm
                    ${msg.role === 'user' ? 'bg-zinc-900 text-white' : 'bg-zinc-900 text-white'}`}>
                    {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                  </div>

                  {/* Message Content */}
                  <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1 px-1">
                      {msg.role === 'user' ? 'You' : 'Assistant'}
                    </span>
                    
                    <div className={`rounded-3xl px-5 py-4 shadow-sm leading-relaxed
                      ${msg.role === 'user' 
                        ? 'bg-zinc-100 text-zinc-800 rounded-tr-none' 
                        : 'bg-white border border-zinc-100 text-zinc-800 rounded-tl-none'}`}>
                      
                      {msg.role === 'bot' ? (
                        <div 
                          className="prose prose-zinc prose-sm max-w-none rendered-html" 
                          dangerouslySetInnerHTML={{ __html: msg.text }} 
                        />
                      ) : (
                        <p className="text-[15px]">{msg.text}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
               <div className="flex justify-start animate-in fade-in duration-300">
                 <div className="flex gap-4 items-center bg-zinc-50 px-6 py-4 rounded-3xl border border-zinc-100">
                    <Loader2 className="text-blue-600 animate-spin" size={20} />
                    <span className="text-sm font-medium text-zinc-500 italic">Thinking...</span>
                 </div>
               </div>
            )}
          </div>
          <div ref={scrollRef} className="h-1" />
        </div>
      </main>

      {/* Input Section */}
      <footer className="absolute bottom-0 right-0 left-0 bg-linear-to-t from-white via-white/95 to-transparent pt-10 pb-2 px-6 z-20">
        <div className="max-w-3xl mx-auto">
          <div className="relative group flex items-end bg-zinc-100 rounded-4xl p-2.5 transition-all border border-zinc-200/50 focus-within:border-blue-300 focus-within:bg-white focus-within:shadow-2xl focus-within:shadow-blue-100/50">
            
            <button 
              onClick={() => setShowUploadModal(true)}
              className="p-3 text-zinc-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-all cursor-pointer"
              title="Upload files"
            >
              <Plus size={22} />
            </button>

            <textarea
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask your knowledge base anything..."
              className="w-full border-none outline-none bg-transparent px-3 py-3 focus:ring-0 text-zinc-800 placeholder:text-zinc-500 resize-none min-h-12 max-h-48 text-[16px]"
            />

            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-zinc-900 text-white p-3.5 rounded-2xl hover:bg-zinc-800 transition-all disabled:opacity-20 mb-0.5 mr-0.5 active:scale-95 cursor-pointer shadow-lg shadow-zinc-200 disabled:shadow-none"
            >
              <Send size={20} />
            </button>
          </div>
          <div className="flex items-center justify-center gap-2 mt-5">
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Based on your Context</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ChatPage;