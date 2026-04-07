import React from 'react';
import { User, BotMessageSquare, FileText, Globe, ShieldCheck, Loader2 } from 'lucide-react';

const MessageList = ({ messages, renderContent, getRelevance, scrollRef, chatContainerRef, loading }) => {
  return (
    <main ref={chatContainerRef} className="flex-1 overflow-y-auto pt-6 md:pt-12">
      <div className="max-w-4xl mx-auto px-4 md:px-10 ">
        <div className="space-y-10 md:space-y-16">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex flex-col md:flex-row gap-3 md:gap-6 w-full animate-in fade-in slide-in-from-bottom-4 duration-500 ${msg.role === 'user' ? 'md:flex-row-reverse' : ''}`}
            >
              <div className={`flex shrink-0 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center border shadow-sm ${msg.role === 'user'
                    ? 'bg-zinc-50 border-zinc-200 text-zinc-500'
                    : 'bg-zinc-900 border-zinc-900 text-white shadow-md'
                  }`}>
                  {msg.role === 'user' ? <User size={18} /> : <BotMessageSquare size={18} />}
                </div>
              </div>

              <div className={`flex flex-col w-full md:max-w-[85%] ${msg.role === 'user' ? 'md:items-end' : 'items-start'}`}>
                {msg.role === 'user' ? (
                  <div className="bg-zinc-100/80 text-zinc-800 px-4 py-2.5 md:px-5 md:py-3 rounded-2xl md:rounded-tr-none text-sm md:text-base border border-zinc-200/50 shadow-sm font-medium">
                    {msg.text}
                  </div>
                ) : (
                  <div className="w-full space-y-8 md:space-y-12">
                    {msg.sections?.map((section, sIdx) => {
                      const rel = getRelevance(section.score || "0%");
                      return (
                        <div key={sIdx} className="group animate-in fade-in duration-700">
                          <h2 className="text-lg md:text-xl font-black uppercase tracking-widest mb-3 border-l-4 border-zinc-200 pl-4">
                            {section.title}
                          </h2>
                          <div className="text-md md:text-lg leading-relaxed text-zinc-800 font-normal">
                            {renderContent(section.content)}
                          </div>
                          <div className="flex items-center gap-2 flex-wrap mt-4">
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-50 border border-zinc-200/60 rounded-full">
                              <FileText size={12} className="text-zinc-400" />
                              <span className="text-[10px] md:text-xs font-semibold text-zinc-600 truncate max-w-40 md:max-w-xs">
                                {section.source}
                              </span>
                            </div>
                            <div className={`flex items-center px-3 py-1.5 rounded-full border text-[9px] md:text-[10px] font-black uppercase tracking-wider ${rel.color}`}>
                              {rel.label} Match • {section.score}
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {/* METADATA FOOTER */}
                    {!msg.isTyping && msg.metadata && (
                      <div className="mt-12 pt-6 border-t border-zinc-200">
                        <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-8">

                          {/* Filter Applied */}
                          <div className="shrink-0">
                            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400 block mb-1">
                              Filter
                            </span>
                            <span className="text-xs font-bold text-zinc-600  uppercase">
                              {msg.metadata.filter_applied}
                            </span>
                          </div>

                          {/* Global Sources */}
                          <div className="flex-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400 block mb-1">
                              Global Sources
                            </span>
                            <p className="text-xs text-zinc-600 leading-relaxed font-medium">
                              {msg.metadata.global_sources}
                            </p>
                          </div>

                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* LOADING SKELETON */}
          {loading && (
            <div className="flex flex-col md:flex-row gap-3 md:gap-6 w-full animate-pulse">
              <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-zinc-100 border border-zinc-200 flex items-center justify-center">
                <Loader2 size={18} className="text-zinc-300 animate-spin" />
              </div>
              <div className="flex-1 space-y-4 pt-2">
                <div className="h-4 bg-zinc-200/50 rounded-lg w-1/4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-zinc-100 rounded w-full"></div>
                  <div className="h-3 bg-zinc-100 rounded w-[85%]"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={scrollRef} className="h-4" />
        </div>
      </div>
    </main>
  );
};

export default MessageList;