import React from 'react';
import { SlidersHorizontal, Minus, Plus } from 'lucide-react';

const TopKSettings = ({ topK, setTopK, showSettings, setShowSettings }) => {
  return (
    <div className="relative">
      <button 
        onClick={() => setShowSettings(!showSettings)}
        className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] md:text-[11px] font-bold uppercase tracking-widest transition-all ${showSettings ? 'bg-zinc-900 text-white border-zinc-900 shadow-lg' : 'bg-white text-zinc-500 border-zinc-200 hover:border-zinc-400'}`}
      >
        <SlidersHorizontal size={12} />
        <span className="hidden xs:inline">Top-K:</span> {topK}
      </button>

      {showSettings && (
        <div className="absolute bottom-full right-0 mb-3 w-36 md:w-40 bg-white border border-zinc-200 rounded-2xl shadow-xl p-3 md:p-4 animate-in fade-in slide-in-from-bottom-2 z-50">
          <div className="flex flex-col items-center gap-3">
            <span className="text-[9px] font-black text-zinc-400 uppercase tracking-widest text-center">Search Depth</span>
            <div className="flex items-center bg-zinc-50 border border-zinc-200 rounded-xl p-1 w-full justify-between">
              <button 
                onClick={() => setTopK(prev => Math.max(1, prev - 1))} 
                className="p-1 hover:bg-white rounded-lg text-zinc-400 hover:text-zinc-900 transition-all active:scale-90"
              >
                <Minus size={14}/>
              </button>
              <input 
                type="number" 
                value={topK}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  if (!isNaN(val)) setTopK(Math.max(1, Math.min(20, val)));
                }}
                className="w-8 text-center bg-transparent font-bold text-zinc-900 outline-none text-xs [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button 
                onClick={() => setTopK(prev => Math.min(20, prev + 1))} 
                className="p-1 hover:bg-white rounded-lg text-zinc-400 hover:text-zinc-900 transition-all active:scale-90"
              >
                <Plus size={14}/>
              </button>
            </div>
            <div className="flex justify-between w-full px-1 text-[8px] font-bold text-zinc-400">
              <span>FAST</span>
              <span>DEEP</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopKSettings;