import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://wjrjpvrgmtbjpwzmmval.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndqcmpwdnJnbXRianB3em1tdmFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3MzExNzIsImV4cCI6MjEwMzMwNzE3Mn0.q6fsTpF9pRa9fHu1wX7U2ILjBfgZMiqbXiTwf7XCJnw';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
