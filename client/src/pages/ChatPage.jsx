import { useState, useEffect, useRef } from 'react';
import { askQuestion, getFiles } from '../api/api';
import { Send, User, BotMessageSquare, X, FileText } from 'lucide-react';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false); 
  
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileDropdown, setShowFileDropdown] = useState(false);
  
  const scrollRef = useRef(null);

  useEffect(() => {
    fetchFileList();
  }, []);

  // Auto-scroll when messages change or loading starts
  useEffect(() => {
    if (loading || isTyping) {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length, loading]); 

  const fetchFileList = async () => {
    try {
      const res = await getFiles();
      setAvailableFiles(res.data.files || []);
    } catch (e) {
      console.error("Error fetching file list:", e);
    }
  };

  /**
   * Time-based typing simulation.
   * This prevents the animation from pausing when the tab is in the background.
   */
  const simulateTyping = (fullText) => {
    setIsTyping(true);
    // Initialize the bot message entry
    setMessages((prev) => [...prev, { role: 'bot', text: '', isTyping: true }]);
    
    const startTime = Date.now();
    const charsPerSec = 120; // Adjust typing speed here

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const charIndex = Math.floor((elapsed / 1000) * charsPerSec);

      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];

        if (charIndex < fullText.length) {
          // Update text based on elapsed time (handles background tab throttling)
          lastMsg.text = fullText.slice(0, charIndex + 1);
          return [...updated];
        } else {
          // Animation complete
          lastMsg.text = fullText;
          lastMsg.isTyping = false;
          setIsTyping(false);
          clearInterval(interval);
          return [...updated];
        }
      });
    }, 25); // Check every 25ms
  };

  const handleSend = async () => {
    if (!input.trim() || loading || isTyping) return;

    const userMsg = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    
    const currentInput = input;
    const currentFilter = selectedFile; 
    
    setInput('');
    setLoading(true);

    try {
      const response = await askQuestion(currentInput, currentFilter);
      setLoading(false);
      simulateTyping(response.data.answer);
    } catch (error) {
      setLoading(false);
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          text: "<div class='p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-xs'><strong>Error:</strong> Failed to get response.</div>"
        }
      ]);
    }
  };

  const isInputDisabled = loading || isTyping;

  return (
    <div className="flex flex-col h-full bg-white relative overflow-hidden">
      
      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl mx-auto px-3 sm:px-6 pt-8 sm:pt-12 pb-44">
          
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
              <h2 className="text-xl sm:text-2xl font-bold text-zinc-900 mb-3 tracking-tight">What are we Referring Today?</h2>
              <p className="text-zinc-500 text-sm sm:text-md max-w-sm">Select a specific document from the list to narrow down the search.</p>
            </div>
          )}

          <div className="flex flex-col gap-8 sm:gap-10">
            {messages.map((msg, i) => (
              <div 
                key={i} 
                className={`flex w-full animate-in fade-in slide-in-from-bottom-3 duration-300 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div className={`flex flex-col sm:gap-4 ${
                  msg.role === 'user' 
                    ? 'items-end sm:flex-row-reverse w-[80%] sm:max-w-[50%] ml-auto' 
                    : 'items-start sm:flex-row w-full sm:max-w-[85%]'
                }`}>
                  
                  <div className={`h-8 w-8 sm:h-10 sm:w-10 mb-2 sm:mb-0 rounded-xl sm:rounded-2xl flex items-center justify-center shrink-0 shadow-sm ${
                    msg.role === 'user' ? 'bg-black text-white' : 'bg-zinc-900 text-white'
                  }`}>
                    {msg.role === 'user' ? <User size={16} /> : <BotMessageSquare size={16} />}
                  </div>

                  <div className={`w-full rounded-2xl sm:rounded-3xl px-4 py-3 sm:px-5 sm:py-4 shadow-sm overflow-hidden ${
                    msg.role === 'user' 
                      ? 'bg-zinc-100 text-zinc-800' 
                      : 'bg-white border border-zinc-100 text-zinc-800'
                  }`}>
                    {msg.role === 'bot' ? (
                      <div 
                        className="rendered-html max-w-none text-sm sm:text-[15px] leading-relaxed wrap-break-word" 
                        dangerouslySetInnerHTML={{ __html: msg.text }} 
                      />
                    ) : (
                      <p className="text-sm sm:text-[15px] font-normal leading-relaxed wrap-break-word text-right sm:text-left">
                        {msg.text}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex w-full justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex flex-col items-start sm:flex-row sm:gap-4 w-full sm:max-w-[85%]">
                  <div className="h-8 w-8 sm:h-10 sm:w-10 mb-2 sm:mb-0 rounded-xl sm:rounded-2xl flex items-center justify-center shrink-0 shadow-sm bg-zinc-900 text-white">
                    <BotMessageSquare size={16} />
                  </div>
                  <div className="w-full sm:w-auto bg-white border border-zinc-100 rounded-2xl sm:rounded-3xl px-5 py-4 sm:px-6 sm:py-5 shadow-sm flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-zinc-300 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-zinc-300 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-zinc-300 rounded-full animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div ref={scrollRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="absolute bottom-0 inset-x-0 bg-white/80 backdrop-blur-md pb-4 sm:pb-6 px-4 sm:px-6 z-20">
        <div className="max-w-3xl mx-auto">
          
          {selectedFile && (
            <div className="flex items-center gap-2 mb-1 animate-in slide-in-from-bottom-2">
              <div className="flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-[10px] sm:text-xs font-bold border border-blue-100 shadow-sm">
                <FileText size={12} />
                <span className="truncate max-w-37.5 sm:max-w-50">Context: {selectedFile}</span>
                <button onClick={() => setSelectedFile(null)} className="ml-1 p-0.5 hover:bg-blue-200 rounded-full transition-colors cursor-pointer">
                  <X size={12} />
                </button>
              </div>
            </div>
          )}

          <div className={`relative group flex items-end bg-zinc-100 rounded-3xl sm:rounded-4xl p-1.5 sm:p-2 transition-all border border-blue-200 focus-within:border-blue-400 focus-within:bg-white focus-within:shadow-2xl ${isInputDisabled ? 'opacity-60 cursor-not-allowed' : ''}`}>
            
            <div className="relative">
              <button 
                disabled={isInputDisabled}
                onClick={() => setShowFileDropdown(!showFileDropdown)}
                className={`p-2.5 sm:p-3 rounded-full transition-all cursor-pointer ${selectedFile ? 'text-blue-600 bg-blue-50' : 'text-zinc-400 hover:text-blue-600 hover:bg-blue-50'}`}
              >
                <FileText size={18} />
              </button>

              {showFileDropdown && (
                <div className="absolute bottom-full left-0 mb-4 w-70 sm:w-72 bg-white rounded-2xl shadow-2xl border border-zinc-100 overflow-hidden z-50 animate-in fade-in zoom-in-95">
                  <div className="p-3 border-b border-zinc-50 bg-zinc-50 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    Available Sources
                  </div>
                  <div className="max-h-60 sm:max-h-64 overflow-y-auto custom-scrollbar">
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
              disabled={isInputDisabled}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={isInputDisabled ? "AI is typing..." : (selectedFile ? `Ask about ${selectedFile}...` : "Ask anything...")}
              className="w-full border-none outline-none bg-transparent px-2 sm:px-3 py-3 text-zinc-800 placeholder:text-zinc-500 resize-none min-h-11 max-h-48 text-sm sm:text-[15px] disabled:cursor-not-allowed"
            />

            <button
              onClick={handleSend}
              disabled={isInputDisabled || !input.trim()}
              className="bg-zinc-900 text-white p-2.5 sm:p-3 rounded-full sm:rounded-4xl hover:bg-zinc-800 transition-all disabled:opacity-20 cursor-pointer shadow-lg active:scale-95"
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