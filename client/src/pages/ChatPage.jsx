import React, { useState, useEffect, useRef } from 'react';
import { askQuestion } from '../api/api';
import { Send, User, Bot, Sparkles } from 'lucide-react';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // --- TYPEWRITER EFFECT LOGIC ---
  const simulateTyping = (fullText) => {
    // Create an empty bot message first
    setMessages((prev) => [...prev, { role: 'bot', text: '', isTyping: true }]);
    
    let index = 0;
    const speed = 5; // Adjust this (ms) to make it faster/slower

    const interval = setInterval(() => {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        
        // We only type until the full length is reached
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
      const fullAnswer = response.data.answer;
      
      setLoading(false); // Stop loader before typing starts
      simulateTyping(fullAnswer); // Start the typing effect

    } catch (error) {
      setLoading(false);
      setMessages((prev) => [
        ...prev, 
        { role: 'bot', text: "<p style='color: #ef4444;'><strong>Error:</strong> Backend unreachable.</p>" }
      ]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-50 relative">
      <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-48 custom-scrollbar">
        <div className="max-w-4xl mx-auto space-y-6">
          
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="bg-blue-100 p-4 rounded-2xl text-blue-600 mb-4">
                <Sparkles size={32} />
              </div>
              <h2 className="text-xl font-bold text-slate-800">Knowledge Assistant</h2>
              <p className="text-slate-500 mt-2">Streaming responses enabled.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex mb-10 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-4 max-w-[95%] md:max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                
                <div className={`h-9 w-9 rounded-xl flex items-center justify-center shrink-0 shadow-sm border
                  ${msg.role === 'user' ? 'bg-blue-600 border-blue-700 text-white' : 'bg-white border-zinc-200 text-slate-600'}`}>
                  {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>

                <div className={`p-5 rounded-2xl shadow-sm leading-relaxed transition-all
                  ${msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none' 
                    : 'bg-white border border-zinc-200 text-slate-800 rounded-tl-none'
                  }`}
                >
                  {msg.role === 'bot' ? (
                    <div className="relative">
                      <div 
                        className="rendered-html text-sm" 
                        dangerouslySetInnerHTML={{ __html: msg.text }} 
                      />
                     
                    </div>
                  ) : (
                    <p className="text-sm font-medium whitespace-pre-wrap">{msg.text}</p>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start items-center gap-3">
              <div className="h-9 w-9 bg-zinc-200 rounded-xl animate-pulse border border-zinc-200"></div>
              <div className="bg-white border border-zinc-200 p-4 rounded-2xl shadow-sm flex gap-1.5">
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
              </div>
            </div>
          )}

          <div ref={scrollRef} className="h-10" />
        </div>
      </div>

      {/* Input Bar */}
      <div className="fixed bottom-0 right-0 left-0 md:left-72 bg-zinc-50 pb-4 z-20">
        <div className="mx-auto max-w-4xl px-4">
          <div className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Query your knowledge base..."
              className="w-full bg-white border border-zinc-300 rounded-2xl pl-6 pr-16 py-4 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="absolute right-2 bg-slate-900 text-white p-3 rounded-xl hover:bg-blue-600 transition-all active:scale-95 disabled:opacity-20 shadow-md"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;