import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://lpiqmxfoinuxujxkxkgi.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwaXFteGZvaW51eHVqeGt4a2dpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAxOTU3NjUsImV4cCI6MjA4NTc3MTc2NX0.QBEOzQEMkNd_tF1jtjzOmVij5rxRDFzujYSIBY5oIQ0';

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  },
  global: {
    headers: {
      'x-client-info': 'deriverse-terminal',
    },
  },
});

// Helper to check if Supabase is properly configured
export function isSupabaseConfigured(): boolean {
  return Boolean(supabaseUrl && supabaseKey);
}

export { supabaseUrl, supabaseKey };
