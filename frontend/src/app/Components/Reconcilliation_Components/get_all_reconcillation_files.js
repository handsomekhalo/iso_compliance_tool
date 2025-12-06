"use client";

// import React, { useState, useEffect } from "react";

// import { useAuth }  from "./../../../../AuthContext"
// import backendApi from "./../../../utils/backendApi";

// import Swal from "sweetalert2";

// export default function ReconciliationFiles() {
//   const { authToken, isAuthenticated, isLoading } = useAuth();

//   const [reconciliations, setReconciliations] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [pagination, setPagination] = useState({
//     limit: 10,
//     offset: 0,
//     has_more: false,
//   });

//   // Converts backend file URL to a viewable/downloadable format
//   const getFileUrl = (fileUrl) => {
//     if (!fileUrl) return "";

//     if (fileUrl.startsWith("http")) return fileUrl;

//     // fallback for relative paths
//     return `${process.env.NEXT_PUBLIC_BACKEND_URL}/${fileUrl}`;
//   };

//   // Fetch reconciliations
//   const fetchReconciliations = async (limit = 10, offset = 0) => {
//     setLoading(true);

//     try {
//       const res = await backendApi.get(
//         // `/compliance_management/list_reconciliations/?limit=${limit}&offset=${offset}`,
//         `/compliance_management/list_reconciliations/`,

//         {
//           headers: { Authorization: `Token ${authToken}` },
//         }
//       );

//       if (res.data.status === "success") {
//         setReconciliations((prev) =>
//           offset === 0
//             ? res.data.data
//             : [...prev, ...res.data.data] // append on load more
//         );

//         setPagination(res.data.pagination);
//       } else {
//         Swal.fire("Error", res.data.message || "Failed to fetch files.", "error");
//       }
//     } catch (error) {
//       console.error("Error fetching reconciliations:", error);
//       Swal.fire("Error", "Server error fetching reconciliation logs.", "error");
//     }

//     setLoading(false);
//   };

//   // Run on load
//   useEffect(() => {
//     if (!authToken || !isAuthenticated) return;

//     fetchReconciliations(10, 0);
//   }, [authToken, isAuthenticated]);

//   const loadMore = () => {
//     fetchReconciliations(
//       pagination.limit,
//       pagination.offset + pagination.limit
//     );
//   };

//   return (
//     <div className="p-4">
//       <h2 className="text-xl font-semibold mb-4">Reconciliation Files</h2>

//       {loading && reconciliations.length === 0 ? (
//         <p>Loading reconciliation logs...</p>
//       ) : reconciliations.length === 0 ? (
//         <p>No reconciliation logs found.</p>
//       ) : (
//         <table className="min-w-full bg-white rounded shadow-md">
//           <thead>
//             <tr className="border-b">
//               <th className="p-3 text-left">ID</th>
//               <th className="p-3 text-left">Uploaded File</th>
//               {/* <th className="p-3 text-left">Processed File</th> */}
              
//                 <th className="p-3 text-left">Transactions</th>
//                 <th className="p-3 text-left">Accuracy</th>

//               <th className="p-3 text-left">Date</th>
//               <th className="p-3 text-left">Status</th>
//             </tr>
//           </thead>

       
// <tbody>
//   {reconciliations.map((item) => (
//     <tr key={item.id} className="border-b">
//       <td className="p-3">{item.id}</td>

//       {/* Uploaded File */}
//       <td className="p-3">
//         {item.filename ? (
//           <span>{item.filename}</span>
//         ) : (
//           "N/A"
//         )}
//       </td>

//       {/* Processed File */}

//         <td className="p-3">{item.total_transactions}</td>
//         <td className="p-3">{item.accuracy_rate}%</td>

//       {/* Date */}
//       <td className="p-3">
//         {item.uploaded_at
//           ? new Date(item.uploaded_at).toLocaleString()
//           : "–"}
//       </td>

//       {/* Status */}
//       <td className="p-3">{item.status || "Unknown"}</td>
//     </tr>
//   ))}
// </tbody>

//         </table>
//       )}

//       {/* Load more button */}
//       {pagination.has_more && (
//         <div className="flex justify-center mt-4">
//           <button
//             onClick={loadMore}
//             className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
//           >
//             {loading ? "Loading..." : "Load More"}
//           </button>
//         </div>
//       )}
//     </div>
//   );
// }

import React, { useEffect, useState } from "react";
import Swal from "sweetalert2";
import { useAuth }  from "./../../../../AuthContext"
import backendApi from "./../../../utils/backendApi";
import ReconciliationDetailModal from "./ReconcillationDSetailsModal";

export default function ReconciliationFiles() {
  const { authToken, isAuthenticated } = useAuth();

  const [reconciliations, setReconciliations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedItem, setSelectedItem] = useState(null);

  const [pagination, setPagination] = useState({
    limit: 10,
    offset: 0,
    has_more: false,
  });
  

  // Fetch reconciliations
  const fetchReconciliations = async (limit = 10, offset = 0) => {
    setLoading(true);

    try {
      const res = await backendApi.get(`/compliance_management/list_reconciliations/`, {
        headers: { Authorization: `Token ${authToken}` },
      });

      if (res.data.status === "success") {
        setReconciliations((prev) =>
          offset === 0 ? res.data.data : [...prev, ...res.data.data]
        );
        setPagination(res.data.pagination);
      } else {
        Swal.fire("Error", res.data.message || "Failed to fetch files.", "error");
      }
    } catch (error) {
      console.error("Error fetching reconciliations:", error);
      Swal.fire("Error", "Server error fetching reconciliation logs.", "error");
    }

    setLoading(false);
  };

  // Run on load
  useEffect(() => {
    if (!authToken || !isAuthenticated) return;
    fetchReconciliations(10, 0);
  }, [authToken, isAuthenticated]);

  const loadMore = () => {
    fetchReconciliations(pagination.limit, pagination.offset + pagination.limit);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Reconciliation Files</h2>

      {loading && reconciliations.length === 0 ? (
        <p>Loading reconciliation logs...</p>
      ) : reconciliations.length === 0 ? (
        <p>No reconciliation logs found.</p>
      ) : (
        <table className="min-w-full bg-white rounded shadow-md">
          <thead>
            <tr className="border-b">
              <th className="p-3 text-left">ID</th>
              <th className="p-3 text-left">Bank Name</th>
              <th className="p-3 text-left">Filename</th>
              <th className="p-3 text-left">Uploaded At</th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3 text-left">Transactions</th>
              <th className="p-3 text-left">Mismatches</th>
              <th className="p-3 text-left">Accuracy</th>
              <th className="p-3 text-left">Actions</th>
              
            </tr>
          </thead>

          <tbody>
            {reconciliations.map((item) => (
              <tr 


              
              key={item.id} className="border-b">
                <td className="p-3">{item.id}</td>
                <td className="p-3">{item.bank_name}</td>
                <td className="p-3">{item.filename}</td>
                <td className="p-3">
                  {item.uploaded_at
                    ? new Date(item.uploaded_at).toLocaleString()
                    : "–"}
                </td>
                <td className="p-3">{item.status || "Unknown"}</td>
                <td className="p-3">{item.total_transactions}</td>
                <td className="p-3">{item.mismatches}</td>
                <td className="p-3">{item.accuracy_rate}%</td>
                <td className="border-b cursor-pointer hover:bg-red-100"
                onClick={() => setSelectedItem(item)}
              > 
              {selectedItem && (
  <ReconciliationDetailModal
    item={selectedItem}
    onClose={() => setSelectedItem(null)}
  />
)}</td>
                            
                      
                
              </tr>
              
              
              
            ))}
            


            
          </tbody>
          
        </table>
      )}

      

      {/* Load more button */}
      {pagination.has_more && (
        <div className="flex justify-center mt-4">
          <button
            onClick={loadMore}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            {loading ? "Loading..." : "Load More"}
          </button>
        </div>
      )}
    </div>
  );
}
