import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle2, X, Clock } from 'lucide-react';

const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadTime, setUploadTime] = useState(null);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    setUploadTime(null);
    const startTime = performance.now();

    const formData = new FormData();
    files.forEach(f => formData.append("files", f));

    try {
      await axios.post("http://127.0.0.1:8000/files/upload-files", formData);
      
      const endTime = performance.now();
      const durationInMinutes = ((endTime - startTime) / 60000).toFixed(2);
      
      setUploadTime(durationInMinutes);
      setFiles([]);
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    /* Changed h-screen to min-h-screen and removed overflow-y-auto to stop double scrollbars */
    <div className="min-h-screen w-full bg-white selection:bg-blue-100">
      {/* Responsive padding: smaller on mobile (p-5), larger on desktop (md:p-16) */}
      <div className="max-w-2xl mx-auto p-5 sm:p-8 md:p-16">
        
        {/* Header Section */}
        <header className="mb-8 md:mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-zinc-900 tracking-tight">Knowledge Base</h2>
          <p className="text-zinc-500 mt-2 text-sm md:text-base">
            Upload documents to expand your AI's specialized knowledge. 
            Supported formats: <span className="font-medium text-zinc-700 underline decoration-zinc-200">PDF, TXT</span>
          </p>
        </header>

        {/* Upload Zone */}
        <div className="relative group">
          <input 
            type="file" 
            multiple 
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          />
          <div className="bg-zinc-50 border-2 border-zinc-200 rounded-3xl p-8 md:p-12 flex flex-col items-center justify-center transition-all group-hover:bg-zinc-100 group-hover:border-blue-400 border-dashed">
            <div className="w-12 h-12 md:w-14 md:h-14 bg-white rounded-2xl flex items-center justify-center text-blue-600 shadow-sm border border-zinc-100 mb-4 group-hover:scale-110 transition-transform">
              <Upload size={22} />
            </div>
            <p className="text-zinc-900 font-semibold text-base md:text-lg text-center">Click or drag files to upload</p>
            <p className="text-zinc-400 text-xs mt-1">Maximum 10MB per file</p>
          </div>
        </div>

        {/* File List Section */}
        {files.length > 0 && (
          <div className="mt-8 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 px-1">
              Selected Documents ({files.length})
            </h3>
            
            {/* Removed internal scrollbar area to keep page scrolling single and clean */}
            <div className="grid gap-2">
              {files.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white border border-zinc-100 p-3 md:p-4 rounded-2xl shadow-sm hover:border-zinc-200 transition-colors">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="p-2 bg-blue-50 text-blue-600 rounded-lg shrink-0">
                      <FileText size={16} />
                    </div>
                    <div className="overflow-hidden">
                      <p className="text-sm font-medium text-zinc-800 truncate">
                        {file.name}
                      </p>
                      <p className="text-[10px] text-zinc-400 uppercase">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => removeFile(idx)}
                    className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors shrink-0"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Button Container */}
        <div className="mt-8 md:mt-10 pb-10">
          <button 
            onClick={handleUpload}
            disabled={loading || files.length === 0}
            className="w-full bg-zinc-900 text-white py-4 rounded-2xl font-bold text-base hover:bg-blue-600 active:scale-[0.98] transition-all disabled:opacity-20 disabled:cursor-not-allowed shadow-xl shadow-zinc-200 disabled:shadow-none flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Ingesting Knowledge...</span>
              </>
            ) : (
              "Process and Store"
            )}
          </button>

          {/* Success Feedback */}
          {uploadTime && !loading && (
            <div className="mt-6 p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center gap-3 animate-in fade-in zoom-in duration-300">
              <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
              <div>
                <p className="text-emerald-800 text-sm font-semibold">Ingestion Complete</p>
                <div className="flex items-center gap-1 text-emerald-600/70 text-xs mt-0.5">
                  <Clock size={12} />
                  <span>Process took {uploadTime} minutes</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadPage;