// Temporary mock layer — replace with real backendApi calls during integration.
// Shapes match the real Django backend's actual response format:
//   POST /compliance_management_api/login_api/ -> { status, token, user: { email, role, bank } }
//   GET  /compliance_management_api/list_reconciliations_api/ -> paginated ISOReconciliationLog rows
//   GET  /payment_management_api/list_payments_api/ -> paginated LightningPayment rows

function fakeDelay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function roleFromEmail(email) {
  if (email?.toLowerCase().startsWith('analyst')) return 'ANALYST';
  return 'INSTITUTION_ADMIN';
}

export async function mockLogin(email) {
  await fakeDelay();
  return {
    token: 'mock-token-' + Date.now(),
    csrf: 'mock-csrf-token',
    user: { email, role: roleFromEmail(email), bank: 'Rand Merchant Bank' },
  };
}

export async function mockRegister(bankName, adminEmail) {
  await fakeDelay();
  return {
    token: 'mock-token-' + Date.now(),
    csrf: 'mock-csrf-token',
    user: { email: adminEmail, role: 'INSTITUTION_ADMIN', bank: bankName },
  };
}

const MOCK_LOGS = [
  { id: 1, filename: 'pacs008_batch_04.xml', total_transactions: 42, mismatches: 2, avg_score: 0.94, status: 'completed', created_at: '2026-08-01T09:12:00Z' },
  { id: 2, filename: 'camt053_stmt_03.xml', total_transactions: 18, mismatches: 0, avg_score: 1.0, status: 'completed', created_at: '2026-07-30T14:05:00Z' },
  { id: 3, filename: 'pain001_batch_02.xml', total_transactions: 27, mismatches: 5, avg_score: 0.81, status: 'completed', created_at: '2026-07-28T11:40:00Z' },
];

const MOCK_PAYMENTS = [
  { id: 1, amount_zar: 1500.0, recipient_account: '+27821234567', status: 'settled', created_at: '2026-08-02T08:00:00Z' },
  { id: 2, amount_zar: 320.5, recipient_account: '+27835557890', status: 'sent', created_at: '2026-08-02T10:15:00Z' },
  { id: 3, amount_zar: 900.0, recipient_account: '+27607891234', status: 'failed', created_at: '2026-08-01T16:30:00Z' },
];

export async function fetchReconciliations(empty) {
  await fakeDelay();
  return empty ? [] : MOCK_LOGS;
}

export async function fetchPayments(empty) {
  await fakeDelay();
  return empty ? [] : MOCK_PAYMENTS;
}

export function zar(amount) {
  return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(amount);
}

export function dt(isoString) {
  return new Date(isoString).toLocaleString('en-ZA', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}


// // Temporary mock layer — replace with real backendApi calls during integration.
// // Shapes match the real Django backend's actual response format:
// //   POST /compliance_management_api/login_api/ -> { status, token, user: { email, role, bank } }
// //   POST /compliance_management_api/register_bank_api/ -> similar, admin auto-logged in

// function fakeDelay(ms = 500) {
//   return new Promise((resolve) => setTimeout(resolve, ms));
// }

// function roleFromEmail(email) {
//   if (email?.toLowerCase().startsWith('analyst')) return 'ANALYST';
//   return 'INSTITUTION_ADMIN';
// }

// export async function mockLogin(email) {
//   await fakeDelay();
//   return {
//     token: 'mock-token-' + Date.now(),
//     csrf: 'mock-csrf-token',
//     user: {
//       email,
//       role: roleFromEmail(email),
//       bank: 'Rand Merchant Bank',
//     },
//   };
// }

// export async function mockRegister(bankName, adminEmail) {
//   await fakeDelay();
//   return {
//     token: 'mock-token-' + Date.now(),
//     csrf: 'mock-csrf-token',
//     user: {
//       email: adminEmail,
//       role: 'INSTITUTION_ADMIN',
//       bank: bankName,
//     },
//   };
// }