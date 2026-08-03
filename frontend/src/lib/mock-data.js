// Temporary mock layer — replace with real backendApi calls during integration.
// Shapes match the real Django backend's actual response format:
//   POST /compliance_management_api/login_api/ -> { status, token, user: { email, role, bank } }
//   POST /compliance_management_api/register_bank_api/ -> similar, admin auto-logged in

function fakeDelay(ms = 500) {
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
    user: {
      email,
      role: roleFromEmail(email),
      bank: 'Rand Merchant Bank',
    },
  };
}

export async function mockRegister(bankName, adminEmail) {
  await fakeDelay();
  return {
    token: 'mock-token-' + Date.now(),
    csrf: 'mock-csrf-token',
    user: {
      email: adminEmail,
      role: 'INSTITUTION_ADMIN',
      bank: bankName,
    },
  };
}