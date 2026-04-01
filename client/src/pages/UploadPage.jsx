import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle2, X, AlertCircle, Clock } from 'lucide-react';

const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadTime, setUploadTime] = useState(null);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
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
      console.error(error);
      // Using a silent console error; a real UI would use a toast notification here
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white p-8 md:p-16">
      <div className="max-w-2xl mx-auto">
        {/* Header Section */}
        <header className="mb-12">
          <h2 className="text-3xl font-bold text-zinc-900 tracking-tight">Knowledge Base</h2>
          <p className="text-zinc-500 mt-2 text-base">
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
          <div className="bg-zinc-50 border border-zinc-200 rounded-4xl p-12 flex flex-col items-center justify-center transition-all group-hover:bg-zinc-100 group-hover:border-zinc-300 border-dashed">
            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center text-blue-600 shadow-sm border border-zinc-100 mb-4 group-hover:scale-110 transition-transform">
              <Upload size={24} />
            </div>
            <p className="text-zinc-900 font-semibold text-lg">Click or drag files to upload</p>
          </div>
        </div>

        {/* File List / Preview */}
        {files.length > 0 && (
          <div className="mt-8 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
            <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 px-1">Selected Documents ({files.length})</h3>
            <div className="grid gap-2">
              {files.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white border border-zinc-100 p-4 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                      <FileText size={18} />
                    </div>
                    <div className="overflow-hidden">
                      <p className="text-sm font-medium text-zinc-800 truncate max-w-50 md:max-w-md">{file.name}</p>
                      <p className="text-[10px] text-zinc-400 uppercase">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => removeFile(idx)}
                    className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <div className="mt-10">
          <button 
            onClick={handleUpload}
            disabled={loading || files.length === 0}
            className="w-full bg-zinc-900 text-white py-4 rounded-2xl font-bold text-base hover:bg-blue-600 active:scale-[0.98] transition-all disabled:opacity-20 disabled:cursor-not-allowed shadow-xl shadow-zinc-200 disabled:shadow-none flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Ingesting Knowledge...
              </>
            ) : (
              "Process and Store"
            )}
          </button>
        </div>

        {/* Success / Feedback Message */}
        {uploadTime && !loading && (
          <div className="mt-6 p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center gap-3 animate-in fade-in zoom-in duration-300">
            <CheckCircle2 size={20} className="text-emerald-600" />
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
  );
};

export default UploadPage;