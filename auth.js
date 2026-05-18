const SUPABASE_URL = 'https://qndawduxacbmzbeiqnpu.supabase.co';
const SUPABASE_KEY = 'sb_publishable_Va8-Hc-IT5fvM9AffLzR3g_xgklYfc8';

const { createClient } = supabase;
const sbClient = createClient(SUPABASE_URL, SUPABASE_KEY);

async function requireAuth() {
  const { data: { session } } = await sbClient.auth.getSession();
  if (!session) {
    window.location.replace('login.html');
    return null;
  }
  return session;
}

async function signOut() {
  await sbClient.auth.signOut();
  window.location.replace('login.html');
}
