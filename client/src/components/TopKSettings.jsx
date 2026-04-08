import React from 'react';
import { Layers, Settings2, Sparkles } from 'lucide-react';

const TopKSettings = ({ topK, setTopK, showSettings, setShowSettings }) => {
  return (
    <div className="relative group">
      
      <button 
        onClick={() => setShowSettings(!showSettings)}
        className={`flex items-center gap-2.5 px-4 py-1.5 rounded-2xl border transition-all duration-300 shadow-sm
          ${showSettings 
            ? 'bg-zinc-900 border-zinc-900 text-white ring-4 ring-zinc-100' 
            : 'bg-white border-zinc-200 text-zinc-600 hover:border-zinc-400 hover:text-zinc-900'
          }`}
      >
        
        <div className="flex flex-col items-start leading-none">
          
          <span className="text-xs font-bold">{topK} {topK === 1 ? 'Pick' : 'Picks'}</span>
        </div>
      </button>

      {/* Popover Settings */}
      {showSettings && (
        <>
         
          <div className="fixed inset-0 z-40" onClick={() => setShowSettings(false)} />
          
          <div className="absolute bottom-full right-0 mb-4 w-56 bg-white border border-zinc-200 rounded-3xl shadow-2xl p-5 animate-in fade-in zoom-in-95 slide-in-from-bottom-4 z-50">
            <div className="space-y-5">
             

              {/* Range Slider Container */}
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-tight">Retrieval Limit</span>
                  <span className="text-xl font-black text-zinc-900 leading-none">{topK}</span>
                </div>
                
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-zinc-100 rounded-lg appearance-none cursor-pointer accent-zinc-900"
                />

                <div className="flex justify-between w-full text-[9px] font-black text-zinc-400 uppercase tracking-tighter">
                  <div className="flex flex-col items-start">
                
                    <span className="font-medium">Fast</span>
                  </div>
                  <div className="flex flex-col items-end">
                    
                    <span className="font-medium">Detailed</span>
                  </div>
                </div>
              </div>

            
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TopKSettings;