import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://lpiqmxfoinuxujxkxkgi.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwaXFteGZvaW51eHVqeGt4a2dpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAxOTU3NjUsImV4cCI6MjA4NTc3MTc2NX0.QBEOzQEMkNd_tF1jtjzOmVij5rxRDFzujYSIBY5oIQ0';

export const supabase = createClient(supabaseUrl, supabaseKey);
