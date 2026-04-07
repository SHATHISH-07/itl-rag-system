import React, { useEffect, useRef } from 'react';
import { User, BotMessageSquare, ChevronRight, Layout } from 'lucide-react';

const MessageList = ({ messages, getRelevance, scrollRef, chatContainerRef, loading }) => {
  const renderContent = (text) => {
    if (!text) return null;
    const segments = text.split(/(?<=[.!?])\s+/);

    return (
      <div className="space-y-4">
        {segments.map((segment, idx) => {
          const trimmed = segment.trim();
          if (!trimmed) return null;

          const hasListStructure = trimmed.includes(':') || (trimmed.match(/,/g) || []).length > 2;
          const parts = trimmed.split(/:\s*/);
          const introText = parts[0];
          const listItems = parts[1]
            ? parts[1].split(/,|\band\b/).map(i => i.trim().replace(/[.]$/, '')).filter(i => i.length > 0)
            : [];

          if (hasListStructure && listItems.length > 1) {
            return (
              <div key={idx} className="group flex flex-col gap-2 animate-in fade-in slide-in-from-left-2 duration-400">
                <div className="flex gap-3 items-start">
                  <span className="text-zinc-900 mt-1.5 leading-none select-none text-lg">•</span>
                  <p className="text-zinc-800 font-bold text-sm md:text-base leading-snug">
                    {introText}{parts[1] ? ':' : ''}
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 ml-6">
                  {listItems.map((item, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 rounded-lg border border-zinc-100 bg-zinc-50/30">
                      <ChevronRight size={12} className="text-zinc-400" />
                      <span className="text-xs font-medium text-zinc-600">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          return (
            <div key={idx} className="flex gap-3 group animate-in fade-in duration-400 items-start">
              <span className="text-zinc-400 group-hover:text-zinc-900 mt-1.5 leading-none select-none transition-colors text-lg">•</span>
              <p className="text-zinc-700 leading-relaxed text-sm md:text-base font-medium">{trimmed}</p>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <main ref={chatContainerRef} className="flex-1 overflow-y-auto bg-white scroll-smooth">
      <div className="max-w-4xl mx-auto px-4 py-6 md:px-8 md:py-12 space-y-10 md:space-y-16 h-full">

        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 animate-in fade-in zoom-in duration-700 pt-20">
            <div className="space-y-1">
              <h1 className="text-xl font-semibold text-zinc-900 uppercase tracking-tight">Ready to Search?</h1>
              <p className="text-sm text-zinc-500 font-normal max-w-xs">
                Upload your documents or ask a question to begin the retrieval process.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex flex-col md:flex-row gap-3 md:gap-8 ${msg.role === 'user' ? 'md:flex-row-reverse items-end md:items-start' : 'items-start'}`}>
            <div className={`w-10 h-10 md:w-12 md:h-12 flex shrink-0 items-center justify-center rounded-xl border-2 shadow-sm ${msg.role === 'user' ? 'bg-white border-zinc-200 text-zinc-500' : 'bg-zinc-900 border-zinc-900 text-white'
              }`}>
              {msg.role === 'user' ? <User size={20} /> : <BotMessageSquare size={20} />}
            </div>

            <div className={`flex-1 w-full md:w-auto flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              {msg.role === 'user' ? (
                <div className="max-w-[95%] md:max-w-[85%] bg-gray-100/50 border border-zinc-200/50 p-4 md:p-5 rounded-2xl md:rounded-3xl md:rounded-tr-none text-zinc-800 text-sm md:text-base font-bold shadow-sm">
                  {msg.text}
                </div>
              ) : (
                <div className="w-full space-y-12">
                  {msg.sections?.map((section, sIdx) => {
                    const rel = getRelevance(section.score || "0%");
                    return (
                      <div key={sIdx} className="relative w-full">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="h-5 w-1 bg-zinc-900 rounded-full" />
                          <h2 className="text-lg md:text-xl font-black text-zinc-900 tracking-tight uppercase">{section.title}</h2>
                        </div>
                        <div className="md:pl-4">{renderContent(section.content)}</div>

                        <div className="flex flex-wrap items-center gap-3 mt-5 md:pl-4">
                          <div className={`px-2 py-1 rounded-md border text-[9px] font-semibold tracking-wider ${rel.color}`}>
                            {rel.label} Match • {section.score}
                          </div>

                          {section.source && (
                            <div className="inline-flex items-center gap-2 px-2 py-1 bg-zinc-50 border border-zinc-200 rounded-md">
                              <span className='text-[9px] font-bold text-zinc-500  tracking-tight'>Source:</span>
                              <span className="text-[9px] font-bold text-zinc-700 truncate max-w-37.5">{section.source}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {msg.metadata?.global_sources && (
                    <div className="pt-6 border-t border-zinc-100">
                      <div className="flex flex-col gap-2">
                        <span className='text-[10px] font-black text-zinc-400 uppercase tracking-widest ml-1'> Sources</span>
                        <div className="flex flex-wrap gap-2">
                          {msg.metadata.global_sources.split(',').map((source, idx) => (
                            <div key={idx} className="px-2.5 py-1 bg-zinc-50 border border-zinc-200 rounded-md shadow-sm">
                              <span className="text-xs font-bold text-zinc-700 break-all">
                                {source.trim()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex flex-col md:flex-row gap-4 md:gap-8 items-start animate-pulse">
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-zinc-100" />
            <div className="flex-1 space-y-3 pt-2 w-full">
              <div className="h-3 bg-zinc-100 rounded-full w-1/4" />
              <div className="h-2 bg-zinc-50 rounded-full w-full" />
            </div>
          </div>
        )}
        <div ref={scrollRef} className="h-4" />
      </div>
    </main>
  );
};

export default MessageList;