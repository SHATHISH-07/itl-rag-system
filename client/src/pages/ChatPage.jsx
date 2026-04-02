import { useState, useEffect, useRef } from 'react';
import { askQuestion, getFiles } from '../api/api';
import { Send, User, BotMessageSquare, X, FileText } from 'lucide-react';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileDropdown, setShowFileDropdown] = useState(false);
  
  const scrollRef = useRef(null);

  useEffect(() => {
    fetchFileList();
  }, []);

  // Updated to scroll when loading starts/ends too
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchFileList = async () => {
    try {
      const res = await getFiles();
      setAvailableFiles(res.data.files || []);
    } catch (e) {
      console.error("Error fetching file list:", e);
    }
  };

  const simulateTyping = (fullText) => {
    setMessages((prev) => [...prev, { role: 'bot', text: '', isTyping: true }]);
    let index = 0;
    const speed = 2;

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
    const currentFilter = selectedFile; 
    
    setInput('');
    setLoading(true);

    try {
      const response = await askQuestion(currentInput, currentFilter);
      setLoading(false); // Stop loading dots
      simulateTyping(response.data.answer); // Start typing text
    } catch (error) {
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          text: "<div class='p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-xs'><strong>Error:</strong> Failed to get response.</div>"
        }
      ]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative overflow-hidden">
      
      <main className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-12 pb-40">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
              <h2 className="text-4xl font-bold text-zinc-900 mb-3 tracking-tight">What are we Referring Today?</h2>
              <p className="text-zinc-500 text-lg max-w-sm">Select a specific document from the list to narrow down the search.</p>
            </div>
          )}

          <div className="flex flex-col gap-8">
            {messages.map((msg, i) => (
              <div key={i} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-4 w-full sm:max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`h-10 w-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-black text-white' : 'bg-zinc-900 text-white'}`}>
                    {msg.role === 'user' ? <User size={18} /> : <BotMessageSquare size={18} />}
                  </div>
                  <div className={`rounded-3xl px-5 py-4 shadow-sm ${msg.role === 'user' ? 'bg-zinc-100 text-zinc-800' : 'bg-white border border-zinc-100 text-zinc-800'}`}>
                    {msg.role === 'bot' ? (
                      /* Using your .rendered-html class here */
                      <div className="rendered-html max-w-none" dangerouslySetInnerHTML={{ __html: msg.text }} />
                    ) : (
                      <p className="text-[15px] font-medium">{msg.text}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* --- LOADING BUBBLE --- */}
            {loading && (
              <div className="flex w-full justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex gap-4 w-full sm:max-w-[85%] flex-row">
                  <div className="h-10 w-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm bg-zinc-900 text-white">
                    <BotMessageSquare size={18} />
                  </div>
                  <div className="bg-white border border-zinc-100 rounded-3xl px-6 py-5 shadow-sm flex items-center gap-1.5">
                    <div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div ref={scrollRef} />
        </div>
      </main>

      {/* Input Footer */}
      <footer className="absolute bottom-0 inset-x-0 bg-white/80 backdrop-blur-md pt-10 pb-6 px-6 z-20">
        <div className="max-w-3xl mx-auto">
          
          {selectedFile && (
            <div className="flex items-center gap-2 mb-3 animate-in slide-in-from-bottom-2">
              <div className="flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-xs font-bold border border-blue-100 shadow-sm">
                <FileText size={14} />
                <span className="truncate max-w-50">Context: {selectedFile}</span>
                <button onClick={() => setSelectedFile(null)} className="ml-1 p-0.5 hover:bg-blue-200 rounded-full transition-colors cursor-pointer">
                  <X size={12} />
                </button>
              </div>
            </div>
          )}

          <div className="relative group flex items-end bg-zinc-100 rounded-3xl p-2 transition-all border border-blue-200 focus-within:border-blue-400 focus-within:bg-white focus-within:shadow-2xl">
            
            <div className="relative">
              <button 
                onClick={() => setShowFileDropdown(!showFileDropdown)}
                className={`p-3 rounded-full transition-all cursor-pointer ${selectedFile ? 'text-blue-600 bg-blue-50' : 'text-zinc-400 hover:text-blue-600 hover:bg-blue-50'}`}
                title="Select source file"
              >
                <FileText size={20} />
              </button>

              {showFileDropdown && (
                <div className="absolute bottom-full left-0 mb-4 w-72 bg-white rounded-2xl shadow-2xl border border-zinc-100 overflow-hidden z-50 animate-in fade-in zoom-in-95">
                  <div className="p-3 border-b border-zinc-50 bg-zinc-50 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    Available Sources
                  </div>
                  <div className="max-h-64 overflow-y-auto custom-scrollbar">
                    <button 
                      onClick={() => { setSelectedFile(null); setShowFileDropdown(false); }}
                      className="w-full text-left px-4 py-3 text-sm hover:bg-zinc-50 transition-colors border-b border-zinc-50 font-medium"
                    >
                      All Knowledge Base
                    </button>
                    {availableFiles.map((file) => (
                      <button 
                        key={file}
                        onClick={() => { setSelectedFile(file); setShowFileDropdown(false); }}
                        className={`w-full text-left px-4 py-3 text-sm hover:bg-zinc-50 transition-colors truncate ${selectedFile === file ? 'text-blue-600 bg-blue-50 font-bold' : 'text-zinc-600'}`}
                      >
                        {file}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <textarea
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={selectedFile ? `Ask about ${selectedFile}...` : "Ask anything..."}
              className="w-full border-none outline-none bg-transparent px-3 py-3 text-zinc-800 placeholder:text-zinc-500 resize-none min-h-11 max-h-48 text-[15px]"
            />

            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-zinc-900 text-white p-3 rounded-2xl hover:bg-zinc-800 transition-all disabled:opacity-20 cursor-pointer shadow-lg active:scale-95"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ChatPage;