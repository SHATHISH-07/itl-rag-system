import React, { useState } from 'react';
import axios from 'axios';

const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadTime, setUploadTime] = useState(null); // State to store the duration

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    setUploadTime(null); // Reset previous time
    const startTime = performance.now(); // Start high-resolution timer

    const formData = new FormData();
    Array.from(files).forEach(f => formData.append("files", f));

    try {
      await axios.post("http://127.0.0.1:8000/files/upload-files", formData);
      
      // Calculate duration
      const endTime = performance.now();
      const durationInMinutes = ((endTime - startTime) / 60000).toFixed(2);
      
      setUploadTime(durationInMinutes);
      alert(`Files successfully ingested! Time taken: ${durationInMinutes} minutes.`);
      setFiles([]);
    } catch (error) {
      console.error(error);
      alert("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-12 max-w-4xl mx-auto w-full">
      <header className="mb-10 text-center">
        <h2 className="text-4xl font-extrabold text-slate-900">Knowledge Base</h2>
        <p className="text-slate-500 mt-2 text-lg">Upload PDF or Text files to train your AI.</p>
      </header>

      <div className="bg-white border-2 border-dashed border-slate-200 rounded-3xl p-16 flex flex-col items-center justify-center hover:border-blue-400 transition-colors bg-opacity-50">
        <input 
          type="file" 
          multiple 
          onChange={(e) => setFiles(e.target.files)}
          className="block w-full text-sm text-slate-500 file:mr-4 file:py-3 file:px-6 file:rounded-full file:border-0 file:text-sm file:font-bold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
        />
        <p className="mt-4 text-slate-400 font-medium italic">Selected: {files.length} files</p>
      </div>

      <button 
        onClick={handleUpload}
        disabled={loading || files.length === 0}
        className="mt-8 w-full bg-slate-900 text-white py-4 rounded-2xl font-bold text-lg hover:bg-blue-600 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Ingesting Documents..." : "Process and Store"}
      </button>

      {/* Visual Feedback for the user */}
      {uploadTime && (
        <p className="mt-4 text-center text-green-600 font-semibold">
          Last upload took: {uploadTime} minutes
        </p>
      )}
    </div>
  );
};

export default UploadPage;