import React, { useState, useRef } from "react";
import { Upload, Loader2 } from "lucide-react";
import UploadPage from "./uploadFile";

export default function UploadFileButton({ onUpload, isUploading }) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) onUpload(file);
    
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-6 text-center transition
        ${dragActive ? "border-amber-500 bg-amber-50" : "border-gray-300 bg-white"}
      `}
    >
      <div className="flex justify-center mb-3">
        {isUploading ? (
          <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
        ) : (
          <Upload className="w-8 h-8 text-gray-600" />
          // <Upload onSuccess={(data) => console.log("Uploaded:", data)} />
        )}
      </div>

      <p className="text-gray-800 font-semibold">Upload File</p>
      <p className="text-sm text-gray-500 mb-4">
        Drag & drop here or click to select
      </p>

      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className="px-4 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
      >
        {isUploading ? "Uploading..." : "Select File"}
      </button>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileSelect}
        accept=".xml,.csv,.json"
      />
    </div>
  );
}
