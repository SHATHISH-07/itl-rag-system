import React, { useState, useEffect, useRef } from 'react';
import { askQuestion, getFiles } from '../api/api';
import { Send, X } from 'lucide-react';
import MessageList from '../components/MessageList';
import TopKSettings from '../components/TopKSettings';
import FileSelector from '../components/FileSelector';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileDropdown, setShowFileDropdown] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [topK, setTopK] = useState(7);

  const scrollRef = useRef(null);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    const fetchFileList = async () => {
      try {
        const res = await getFiles();
        setAvailableFiles(res.data.files || []);
      } catch (e) { console.error("File fetch failed", e); }
    };
    fetchFileList();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading || isTyping) return;
    
    const userMsg = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    
    const currentInput = input;
    const currentFilter = selectedFile;
    const currentTopK = topK;
    
    setInput('');
    setLoading(true);

    try {
      const response = await askQuestion(currentInput, currentFilter, currentTopK);
      setLoading(false);
      // Pass the WHOLE data object so we have access to .metadata
      simulateTyping(response.data); 
    } catch (error) {
      setLoading(false);
      setMessages(prev => [...prev, { 
        role: 'bot', 
        sections: [{ title: "Error", content: "Service currently unavailable." }] 
      }]);
    }
  };

  const simulateTyping = (data) => {
    const answerArray = data.responses || data.answer;
    const metadata = data.metadata; // Catch the metadata here!

    if (!answerArray?.length) return;
    setIsTyping(true);

    // Save the metadata to the message object immediately
    setMessages(prev => [...prev, { 
      role: 'bot', 
      sections: [], 
      metadata: metadata, // Store it here
      isTyping: true 
    }]);

    let sIdx = 0, cIdx = 0;
    const type = () => {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (!last || !answerArray[sIdx]) return updated;
        if (!last.sections[sIdx]) last.sections[sIdx] = { ...answerArray[sIdx], content: '' };
        
        const fullContent = answerArray[sIdx].content || "";
        if (cIdx < fullContent.length) {
          last.sections[sIdx].content = fullContent.slice(0, cIdx + 1);
          cIdx++;
          setTimeout(type, 10);
        } else if (sIdx < answerArray.length - 1) {
          sIdx++; cIdx = 0;
          setTimeout(type, 150);
        } else {
          last.isTyping = false;
          setIsTyping(false);
        }
        return updated;
      });
    };
    type();
  };

  const getRelevance = (scoreStr) => {
    const score = parseInt(scoreStr?.replace('%', '') || '0');
    if (score >= 80) return { label: 'High', color: 'text-emerald-700 bg-emerald-100/50 border-emerald-200' };
    if (score >= 50) return { label: 'Mid', color: 'text-amber-700 bg-amber-100/50 border-amber-200' };
    return { label: 'Low', color: 'text-zinc-500 bg-zinc-100 border-zinc-200' };
  };

  const renderContent = (content) => {
    if (!content) return null;
    if (content.toLowerCase().includes("include") && content.includes(",")) {
      const parts = content.split(/include|including/i);
      const items = parts[1].split(/,|\band\b/).map(item => item.trim().replace(/\.$/, ""));
      return (
        <React.Fragment>
          <p className="mb-4">{parts[0]} include:</p>
          <ul className="space-y-2 mb-6">
            {items.filter(i => i.length > 0).map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="mt-2 w-1.5 h-1.5 rounded-full bg-zinc-300 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </React.Fragment>
      );
    }
    return <p className="whitespace-pre-wrap">{content}</p>;
  };

  return (
    <div className="flex flex-col h-screen font-sans text-zinc-900 overflow-hidden relative w-full">

      <div className="flex-1 overflow-y-auto" ref={chatContainerRef}>
         <MessageList 
            messages={messages} 
            renderContent={renderContent} 
            getRelevance={getRelevance} 
            scrollRef={scrollRef} 
            chatContainerRef={chatContainerRef} 
            loading={loading} 
          />
      </div>

      <footer className="sticky bottom-10 w-full z-40 px-4 md:px-6 lg:px-10 pb-6 md:pb-10 pointer-events-none">
        <div className="max-w-3xl mx-auto w-full pointer-events-auto">
        
          <div className="flex justify-between items-end px-2 mb-2 gap-2">
            <div className="flex-1 min-w-0">
              {selectedFile && (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-zinc-900 text-white rounded-xl text-[10px] font-bold uppercase border border-zinc-700 max-w-full shadow-lg animate-in fade-in slide-in-from-bottom-2">
                  <span className="truncate">{selectedFile}</span>
                  <button onClick={() => setSelectedFile(null)} className="hover:text-red-400 transition-colors">
                    <X size={12}/>
                  </button>
                </div>
              )}
            </div>
            <TopKSettings 
              topK={topK} 
              setTopK={setTopK} 
              showSettings={showSettings} 
              setShowSettings={setShowSettings} 
            />
          </div>

          <div className="bg-white border border-zinc-200 md:border-2 rounded-3xl md:rounded-[2.5rem]  p-1.5 md:p-2 flex items-center gap-1 transition-all focus-within:border-zinc-400">
            <FileSelector 
              showFileDropdown={showFileDropdown} 
              setShowFileDropdown={setShowFileDropdown} 
              selectedFile={selectedFile} 
              setSelectedFile={setSelectedFile} 
              availableFiles={availableFiles} 
            />

            <textarea
              className="flex-1 bg-transparent border-none outline-none py-3 px-1 text-sm md:text-lg text-zinc-800 placeholder-zinc-400 resize-none max-h-32 min-h-11 font-medium leading-tight"
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedFile ? "Search in file..." : "Ask anything..."}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            />
            
            <button 
              onClick={handleSend} 
              disabled={!input.trim() || loading} 
              className="p-3 md:p-4 bg-zinc-900 text-white rounded-full disabled:opacity-20 transition-all active:scale-95 flex items-center justify-center shrink-0 shadow-lg hover:bg-black"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ChatPage;