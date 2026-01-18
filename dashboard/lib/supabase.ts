import { createClient, SupabaseClient } from '@supabase/supabase-js'

let supabaseClient: SupabaseClient | null = null

function getSupabaseClient(): SupabaseClient {
  if (supabaseClient) {
    return supabaseClient
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  // During build time, Next.js statically analyzes routes
  // If env vars are missing, use placeholders to allow build to complete
  // Runtime will validate and throw proper errors
  if (!supabaseUrl || !supabaseAnonKey) {
    // Detect build context: Next.js sets NEXT_PHASE during build
    const isBuildTime = typeof process !== 'undefined' && 
                       (process.env.NEXT_PHASE === 'phase-production-build' ||
                        (process.env.NODE_ENV === 'production' && !process.env.VERCEL_ENV))
    
    if (isBuildTime) {
      // Use placeholders during build - allows static analysis to complete
      supabaseClient = createClient(
        'https://build-placeholder.supabase.co',
        'build-placeholder-key'
      )
      return supabaseClient
    }
    
    // Runtime: throw clear error
    throw new Error(
      'Missing Supabase environment variables. ' +
      'Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel project settings.'
    )
  }

  supabaseClient = createClient(supabaseUrl, supabaseAnonKey)
  return supabaseClient
}

// Lazy initialization with Proxy - only creates client when actually accessed
export const supabase = new Proxy({} as SupabaseClient, {
  get(_target, prop) {
    const client = getSupabaseClient()
    const value = (client as any)[prop]
    if (typeof value === 'function') {
      return value.bind(client)
    }
    return value
  }
})

