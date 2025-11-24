"use client";

import { useState } from "react";
import UploadFileButton from "./UploadFileComponent";

export default function UploadPage() {
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (file) => {
    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    // Send to backend API
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    setIsUploading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <UploadFileButton onUpload={handleUpload} isUploading={isUploading} />
    </div>
  );
}
