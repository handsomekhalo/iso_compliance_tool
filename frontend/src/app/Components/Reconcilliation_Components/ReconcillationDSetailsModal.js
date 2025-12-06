
import React from "react";

export default function ReconciliationDetailModal({ item, onClose }) {
  if (!item) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg shadow-lg">
        <h3 className="text-xl font-semibold mb-4">Reconciliation Details</h3>

        <div className="space-y-2">
          <p><strong>ID:</strong> {item.id}</p>
          <p><strong>Bank:</strong> {item.bank_name}</p>
          <p><strong>Filename:</strong> {item.filename}</p>
          <p><strong>Uploaded At:</strong> {new Date(item.uploaded_at).toLocaleString()}</p>
          <p><strong>Status:</strong> {item.status}</p>
          <p><strong>Total Transactions:</strong> {item.total_transactions}</p>
          <p><strong>Mismatches:</strong> {item.mismatches}</p>
          <p><strong>Accuracy Rate:</strong> {item.accuracy_rate}%</p>
          <p><strong>XRPL Hash:</strong> {item.xrpl_hash}</p>
          <p><strong>Processing Time:</strong> {item.processing_time_ms} ms</p>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
