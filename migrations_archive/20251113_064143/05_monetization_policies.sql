-- DELTA:20251113_064143 RLS Policies for Monetization Tables

BEGIN;

-- Enable RLS on all monetization tables
ALTER TABLE agencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE affiliates ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_token_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_token_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE white_label_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_transactions ENABLE ROW LEVEL SECURITY;

-- Agencies policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'agencies' AND policyname = 'tenant_isolation_agencies'
    ) THEN
        CREATE POLICY tenant_isolation_agencies ON agencies
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- Affiliates policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'affiliates' AND policyname = 'tenant_isolation_affiliates'
    ) THEN
        CREATE POLICY tenant_isolation_affiliates ON affiliates
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- Referrals policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'referrals' AND policyname = 'tenant_isolation_referrals'
    ) THEN
        CREATE POLICY tenant_isolation_referrals ON referrals
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- AI Token Usage policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'ai_token_usage' AND policyname = 'tenant_isolation_ai_token_usage'
    ) THEN
        CREATE POLICY tenant_isolation_ai_token_usage ON ai_token_usage
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- AI Token Balances policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'ai_token_balances' AND policyname = 'tenant_isolation_ai_token_balances'
    ) THEN
        CREATE POLICY tenant_isolation_ai_token_balances ON ai_token_balances
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- API Usage policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'api_usage' AND policyname = 'tenant_isolation_api_usage'
    ) THEN
        CREATE POLICY tenant_isolation_api_usage ON api_usage
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- White Label Settings policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'white_label_settings' AND policyname = 'tenant_isolation_white_label_settings'
    ) THEN
        CREATE POLICY tenant_isolation_white_label_settings ON white_label_settings
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- Subscription Tiers policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'subscription_tiers' AND policyname = 'tenant_isolation_subscription_tiers'
    ) THEN
        CREATE POLICY tenant_isolation_subscription_tiers ON subscription_tiers
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

-- Billing Transactions policies
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'billing_transactions' AND policyname = 'tenant_isolation_billing_transactions'
    ) THEN
        CREATE POLICY tenant_isolation_billing_transactions ON billing_transactions
            USING (tenant_id = current_setting('app.current_tenant', TRUE)::UUID);
    END IF;
END $$;

COMMIT;
