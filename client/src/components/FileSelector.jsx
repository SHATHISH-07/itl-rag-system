import React from 'react';
import { Search, X, Globe, FileText, Check } from 'lucide-react';

const FileSelector = ({ showFileDropdown, setShowFileDropdown, selectedFile, setSelectedFile, availableFiles }) => {
  return (
    <div className="relative">
      <button 
        onClick={() => setShowFileDropdown(!showFileDropdown)} 
        className={`p-3 md:p-4 rounded-full transition-all flex items-center justify-center ${
          selectedFile ? 'text-zinc-900 bg-zinc-100' : 'text-zinc-400 hover:text-zinc-900 hover:bg-zinc-50'
        }`}
      >
        <Search size={22} />
      </button>

      {showFileDropdown && (
        <div className="absolute bottom-full left-0 mb-4 w-[85vw] md:w-80 bg-white border border-zinc-200 rounded-3xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 z-50">
          <div className="p-4 border-b border-zinc-100 bg-zinc-50/50 flex justify-between items-center">
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Knowledge Base</span>
            <button onClick={() => setShowFileDropdown(false)}>
              <X size={14} className="text-zinc-400 hover:text-zinc-600"/>
            </button>
          </div>
          
          <div className="max-h-64 overflow-y-auto p-2 space-y-1">
            <button 
              onClick={() => { setSelectedFile(null); setShowFileDropdown(false); }}
              className={`w-full text-left px-4 py-3 rounded-2xl text-sm flex items-center justify-between transition-all ${
                !selectedFile ? 'bg-zinc-900 text-white shadow-md' : 'hover:bg-zinc-100 text-zinc-600'
              }`}
            >
              <div className="flex items-center gap-3"><Globe size={18} /> Global Search</div>
              {!selectedFile && <Check size={16} />}
            </button>
            
            {availableFiles.map((file, idx) => (
              <button
                key={idx}
                onClick={() => { setSelectedFile(file); setShowFileDropdown(false); }}
                className={`w-full text-left px-4 py-3 rounded-2xl text-sm flex items-center justify-between transition-all ${
                  selectedFile === file ? 'bg-zinc-900 text-white shadow-md' : 'hover:bg-zinc-100 text-zinc-600'
                }`}
              >
                <div className="flex items-center gap-3 truncate pr-4">
                  <FileText size={18} className={selectedFile === file ? 'text-white' : 'text-zinc-400'} /> 
                  <span className="truncate">{file}</span>
                </div>
                {selectedFile === file && <Check size={16} />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileSelector;