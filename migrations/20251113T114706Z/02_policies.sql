-- DELTA:20251113T114706Z RLS Policies
-- Only add policies if RLS is already enabled in the project

BEGIN;

-- Check if RLS is used (check if any table has RLS enabled)
DO $$
DECLARE
  v_rls_enabled boolean;
BEGIN
  -- Check if tenants table exists and has RLS (indicator that project uses RLS)
  SELECT EXISTS (
    SELECT 1 FROM pg_tables 
    WHERE schemaname='public' AND tablename='tenants'
  ) INTO v_rls_enabled;
  
  -- If tenants table exists, check if RLS is enabled on it
  IF v_rls_enabled THEN
    SELECT EXISTS (
      SELECT 1 FROM pg_tables t
      JOIN pg_class c ON c.relname = t.tablename
      WHERE t.schemaname='public' AND t.tablename='tenants'
      AND c.relrowsecurity = true
    ) INTO v_rls_enabled;
  END IF;
  
  -- Only proceed if RLS is used
  IF v_rls_enabled THEN
    -- Add tenant_id to matches if missing (for RLS)
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='matches' AND column_name='tenant_id'
    ) THEN
      ALTER TABLE public.matches ADD COLUMN tenant_id uuid;
    END IF;
    
    -- Enable RLS on matches if not already enabled
    ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
    
    -- Create RLS policies for matches (if not exist)
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies 
      WHERE schemaname='public' AND tablename='matches' AND policyname='org_select_matches'
    ) THEN
      CREATE POLICY org_select_matches ON public.matches
        FOR SELECT USING (
          tenant_id = current_setting('app.current_tenant', true)::uuid
          OR tenant_id IS NULL  -- Allow NULL for backward compatibility
        );
    END IF;
    
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies 
      WHERE schemaname='public' AND tablename='matches' AND policyname='org_insert_matches'
    ) THEN
      CREATE POLICY org_insert_matches ON public.matches
        FOR INSERT WITH CHECK (
          tenant_id = current_setting('app.current_tenant', true)::uuid
          OR tenant_id IS NULL  -- Allow NULL for backward compatibility
        );
    END IF;
    
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies 
      WHERE schemaname='public' AND tablename='matches' AND policyname='org_update_matches'
    ) THEN
      CREATE POLICY org_update_matches ON public.matches
        FOR UPDATE USING (
          tenant_id = current_setting('app.current_tenant', true)::uuid
          OR tenant_id IS NULL
        );
    END IF;
    
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies 
      WHERE schemaname='public' AND tablename='matches' AND policyname='org_delete_matches'
    ) THEN
      CREATE POLICY org_delete_matches ON public.matches
        FOR DELETE USING (
          tenant_id = current_setting('app.current_tenant', true)::uuid
          OR tenant_id IS NULL
        );
    END IF;
  END IF;
END$$;

COMMIT;
