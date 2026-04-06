import { useState, useEffect, useRef } from 'react';
import { askQuestion, getFiles } from '../api/api';
import { Send, User, BotMessageSquare, X, FileText, Globe, Search } from 'lucide-react';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileDropdown, setShowFileDropdown] = useState(false);
  const scrollRef = useRef(null);
  const chatContainerRef = useRef(null);

  useEffect(() => { fetchFileList(); }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      const isNearBottom = scrollHeight - scrollTop <= clientHeight + 200;
      if (isNearBottom) {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [messages, isTyping]);

  const getRelevance = (scoreStr) => {
    const score = parseInt(scoreStr?.replace('%', '') || '0');
    if (score >= 80) return { label: 'High', color: 'text-emerald-700 bg-emerald-100/50 border-emerald-200' };
    if (score >= 50) return { label: 'Mid', color: 'text-amber-700 bg-amber-100/50 border-amber-200' };
    return { label: 'Low', color: 'text-zinc-500 bg-zinc-100 border-zinc-200' };
  };

  const fetchFileList = async () => {
    try {
      const res = await getFiles();
      setAvailableFiles(res.data.files || []);
    } catch (e) { console.error(e); }
  };

  const handleSend = async () => {
    if (!input.trim() || loading || isTyping) return;
    const userMsg = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    const currentFilter = selectedFile;
    setInput('');
    setLoading(true);

    try {
      const response = await askQuestion(currentInput, currentFilter);
      setLoading(false);
      simulateTyping(response.data.answer, response.data.metadata);
    } catch (error) {
      setLoading(false);
      setMessages(prev => [...prev, { role: 'bot', sections: [{ title: "Error", content: "The engine is currently unavailable." }] }]);
    }
  };

  const simulateTyping = (answerArray, metadata) => {
    if (!answerArray || !answerArray.length) return;

    setIsTyping(true);
    setMessages(prev => [...prev, {
      role: 'bot',
      sections: [],
      isTyping: true,
      scope: metadata?.filter_applied || 'Global',
      sources: metadata?.global_sources || ''
    }]);

    let sIdx = 0, cIdx = 0;

    const type = () => {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];

        // Ensure current section in answerArray exists
        const currentTarget = answerArray[sIdx];
        if (!currentTarget) return updated;

        // Initialize section shell if missing
        if (!last.sections[sIdx]) {
          last.sections[sIdx] = { ...currentTarget, content: '' };
        }

        const fullContent = currentTarget.content || "";

        if (cIdx < fullContent.length) {
          last.sections[sIdx].content = fullContent.slice(0, cIdx + 1);
          cIdx++;
          setTimeout(type, 12);
        } else if (sIdx < answerArray.length - 1) {
          sIdx++;
          cIdx = 0;
          setTimeout(type, 200);
        } else {
          last.isTyping = false;
          setIsTyping(false);
        }
        return updated;
      });
    };
    type();
  };

  const renderContent = (content) => {
    if (!content) return null;
    
    // Auto-detect comma lists involving "include" or "including"
    if (content.toLowerCase().includes("include") && content.includes(",")) {
      const parts = content.split(/include|including/i);
      const intro = parts[0];
      const items = parts[1].split(/,|\band\b/).map(item => item.trim().replace(/\.$/, ""));

      return (
        <>
          <p className="mb-4">{intro} include:</p>
          <ul className="space-y-2 mb-6">
            {items.filter(item => item.length > 0).map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="mt-2.5 w-1.5 h-1.5 rounded-full bg-zinc-400 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </>
      );
    }
    return <p className="whitespace-pre-wrap">{content}</p>;
  };

  return (
    <div className="flex flex-col h-full bg-[#FDFDFD] font-sans text-zinc-900 overflow-hidden relative">
      <main ref={chatContainerRef} className="flex-1 overflow-y-auto bg-white">
        <div className="max-w-4xl mx-auto px-4 md:px-10 py-12 pb-56">
          <div className="space-y-12 md:space-y-16">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col md:flex-row gap-3 md:gap-6 w-full animate-in fade-in slide-in-from-bottom-4 duration-500 ${msg.role === 'user' ? 'md:flex-row-reverse' : ''}`}
              >
                <div className={`flex shrink-0 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`w-8 h-8 md:w-9 md:h-9 rounded-lg flex items-center justify-center border ${msg.role === 'user' ? 'bg-zinc-50 border-zinc-200 text-zinc-500' : 'bg-zinc-900 border-zinc-900 text-white shadow-md'}`}>
                    {msg.role === 'user' ? <User size={16} /> : <BotMessageSquare size={16} />}
                  </div>
                </div>

                <div className={`flex flex-col w-full md:max-w-[85%] ${msg.role === 'user' ? 'md:items-end' : 'items-start'}`}>
                  {msg.role === 'user' ? (
                    <div className="bg-zinc-100/80 text-zinc-800 px-5 py-3 rounded-2xl md:rounded-tr-none text-base md:text-[17px] leading-relaxed border border-zinc-200/50 shadow-sm">
                      {msg.text}
                    </div>
                  ) : (
                    <div className="w-full space-y-10 md:space-y-12">
                      {msg.sections?.map((section, sIdx) => {
                        const rel = getRelevance(section.score || "0%");
                        return (
                          <div key={sIdx} className="group animate-in fade-in duration-700">
                            <h2 className="text-lg md:text-xl font-black uppercase tracking-widest text-black mb-4 border-l-4 border-zinc-200 pl-4">
                              {section.title}
                            </h2>
                            
                            <div className="text-md md:text-lg leading-[1.8] text-zinc-800 font-normal">
                              {renderContent(section.content)}
                            </div>

                            <div className="flex items-center gap-2 md:gap-3 flex-wrap mt-4">
                              <div className="flex items-center gap-2.5 px-4 py-2 bg-zinc-50 border border-zinc-200/60 rounded-full shadow-sm hover:bg-white transition-colors">
                                <FileText size={14} className="text-zinc-400" />
                                <span className="text-xs md:text-sm font-semibold text-zinc-600 truncate max-w-62.5">
                                  {section.source}
                                </span>
                              </div>
                              <div className={`flex items-center px-4 py-2 rounded-full border text-[10px] md:text-[11px] font-black uppercase tracking-wider ${rel.color}`}>
                                <div className={`w-1.5 h-1.5 rounded-full mr-2 animate-pulse ${rel.color.split(' ')[0].replace('text', 'bg')}`} />
                                {rel.label} Match • {section.score}
                              </div>
                            </div>
                          </div>
                        );
                      })}

                      {!msg.isTyping && msg.sources && (
                        <div className="pt-8 mt-6 border-t border-zinc-100 flex flex-wrap gap-4 md:gap-6 text-[10px] text-zinc-400 font-medium uppercase tracking-widest">
                          <div className="flex items-center gap-2"><Search size={12} /> Scope: <span className="text-zinc-900">{msg.scope}</span></div>
                          <div className="flex items-center gap-2"><Globe size={12} /> Citations: <span className="text-zinc-900">{msg.sources}</span></div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={scrollRef} className="h-4" />
          </div>
        </div>
      </main>

      <footer className="absolute bottom-0 left-0 right-0 p-4 md:p-10 bg-linear-to-t from-white via-white/90 to-transparent pointer-events-none">
        <div className="max-w-3xl mx-auto w-full pointer-events-auto">
          <div className="bg-white border md:border-2 border-gray-300 rounded-4xl shadow-2xl p-1.5 md:p-2 focus-within:border-zinc-500 transition-all">
            <div className="flex items-center gap-1 md:gap-2">
              <button onClick={() => setShowFileDropdown(!showFileDropdown)} className="p-3 md:p-4 text-zinc-600 hover:text-zinc-900 relative">
                <FileText size={20} />
              </button>
              <textarea
                className="flex-1 bg-transparent border-none outline-none py-3 px-1 text-base md:text-lg text-zinc-800 placeholder-zinc-600 resize-none max-h-32 min-h-11 font-medium"
                rows="1"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything..."
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              />
              <button onClick={handleSend} disabled={!input.trim() || loading || isTyping} className="p-3 md:p-4 bg-zinc-900 text-white rounded-3xl disabled:opacity-70 shadow-lg">
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ChatPage;