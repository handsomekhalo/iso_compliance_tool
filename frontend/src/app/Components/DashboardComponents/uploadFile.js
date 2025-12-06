// "use client";

// import { useState } from "react";
// import UploadFileButton from "./UploadFileComponent";

// export default function UploadPage() {
//   const [isUploading, setIsUploading] = useState(false);

//   const handleUpload = async (file) => {
//     setIsUploading(true);

//     const formData = new FormData();
//     formData.append("file", file);

//     // Send to backend API
//     const res = await fetch("/api/upload", {
//       method: "POST",
//       body: formData,
//     });

//     setIsUploading(false);
//   };

//   return (
//     <div className="max-w-md mx-auto mt-10">
//       <UploadFileButton onUpload={handleUpload} isUploading={isUploading} />
//     </div>
//   );
// }
"use client";
import React, { useState } from "react";
import Swal from "sweetalert2";
// import UploadFileButton from "./UploadFileButton";
import UploadFileButton from "./UploadFileComponent";

// import Swal from "sweetalert2";
import { useAuth }  from "./../../../../AuthContext"
import backendApi from "./../../../utils/backendApi";


export default function UploadPage({ onSuccess }) {
  const { authToken, isAuthenticated } = useAuth();
  const [isUploading, setIsUploading] = useState(false);
  

  const handleUpload = async (file) => {
    if (!authToken || !isAuthenticated) {
      Swal.fire("Error", "You must be logged in to upload files.", "error");
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      // formData.append("file", file);
      formData.append("file_name", file);
      

      const res = await backendApi.post("/compliance_management/upload_reconciliation/", formData, {
        headers: {
          Authorization: `Token ${authToken}`,
          "Content-Type": "multipart/form-data",
        },
      });

      console.log('res is', res)

      if (res.data.status === "success") {
        Swal.fire("Success", "File uploaded successfully!", "success");
        if (onSuccess) onSuccess(res.data.data);
      } else {
        Swal.fire("Error", res.data.message || "Upload failed.", "error");
      }
    } catch (error) {
      console.error("Upload error:", error);
      Swal.fire("Error", "Server error during upload.", "error");
    }

    setIsUploading(false);
  };

  return (
    <div className="p-4 bg-white rounded shadow-md">
      <h2 className="text-lg font-semibold mb-4">Upload Reconciliation File</h2>
      {/* ✅ Pass props correctly */}
      <UploadFileButton onUpload={handleUpload} isUploading={isUploading} />
    </div>
  );
}

// import React, { useState } from "react";
// import Swal from "sweetalert2";
// // import UploadFileButton from "./UploadFileButton";
// import UploadFileButton from "./UploadFileComponent";
// // import Swal from "sweetalert2";
// import { useAuth }  from "./../../../../AuthContext"
// import backendApi from "./../../../utils/backendApi";


// export default function UploadPage({ onSuccess }) {
//   const { authToken, isAuthenticated } = useAuth();
//   const [isUploading, setIsUploading] = useState(false);

//   const handleUpload = async (file) => {
//     if (!authToken || !isAuthenticated) {
//       Swal.fire("Error", "You must be logged in to upload files.", "error");
//       return;
//     }

//     setIsUploading(true);

//     try {
//       const formData = new FormData();
//       formData.append("file", file);

//       const res = await backendApi.post("/compliance_management/upload_reconciliation/", formData, {
//         headers: {
//           Authorization: `Token ${authToken}`,
//           "Content-Type": "multipart/form-data",
//         },
//       });

//       if (res.data.status === "success") {
//         Swal.fire("Success", "File uploaded successfully!", "success");
//         if (onSuccess) onSuccess(res.data.data);
//       } else {
//         Swal.fire("Error", res.data.message || "Upload failed.", "error");
//       }
//     } catch (error) {
//       console.error("Upload error:", error);
//       Swal.fire("Error", "Server error during upload.", "error");
//     }

//     setIsUploading(false);
//   };

//   return (
//     <div className="p-4 bg-white rounded shadow-md">
//       <h2 className="text-lg font-semibold mb-4">Upload Reconciliation File</h2>
//       <UploadFileButton onUpload={handleUpload} isUploading={isUploading} />
//     </div>
//   );
// }
