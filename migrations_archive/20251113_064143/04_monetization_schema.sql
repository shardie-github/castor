-- DELTA:20251113_064143 Monetization Schema
-- Adds tables for agency/consultancy, affiliate marketing, AI tokens, white-labeling, API usage

BEGIN;

-- 1. AGENCIES TABLE (for agency/consultancy management)
CREATE TABLE IF NOT EXISTS agencies (
    agency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    commission_rate_percent NUMERIC(5,2) DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_agency_status CHECK (status IN ('active', 'inactive', 'suspended')),
    CONSTRAINT valid_commission_rate CHECK (commission_rate_percent >= 0 AND commission_rate_percent <= 100),
    UNIQUE(tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_agencies_tenant_id ON agencies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agencies_slug ON agencies(slug);
CREATE INDEX IF NOT EXISTS idx_agencies_status ON agencies(status);

-- 2. AFFILIATES TABLE (for affiliate marketing)
CREATE TABLE IF NOT EXISTS affiliates (
    affiliate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    agency_id UUID REFERENCES agencies(agency_id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    commission_rate_percent NUMERIC(5,2) DEFAULT 10.00,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    total_referrals INTEGER DEFAULT 0,
    total_commission_cents BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_affiliate_status CHECK (status IN ('active', 'inactive', 'suspended')),
    CONSTRAINT valid_affiliate_commission CHECK (commission_rate_percent >= 0 AND commission_rate_percent <= 100)
);

CREATE INDEX IF NOT EXISTS idx_affiliates_tenant_id ON affiliates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_affiliates_agency_id ON affiliates(agency_id);
CREATE INDEX IF NOT EXISTS idx_affiliates_referral_code ON affiliates(referral_code);
CREATE INDEX IF NOT EXISTS idx_affiliates_status ON affiliates(status);

-- 3. REFERRALS TABLE (track affiliate referrals)
CREATE TABLE IF NOT EXISTS referrals (
    referral_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    affiliate_id UUID NOT NULL REFERENCES affiliates(affiliate_id) ON DELETE CASCADE,
    referred_tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE SET NULL,
    referral_code VARCHAR(50) NOT NULL,
    conversion_status VARCHAR(50) DEFAULT 'pending',
    conversion_value_cents BIGINT DEFAULT 0,
    commission_cents BIGINT DEFAULT 0,
    converted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_conversion_status CHECK (conversion_status IN ('pending', 'converted', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_referrals_tenant_id ON referrals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_referrals_affiliate_id ON referrals(affiliate_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_tenant_id ON referrals(referred_tenant_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referral_code ON referrals(referral_code);
CREATE INDEX IF NOT EXISTS idx_referrals_conversion_status ON referrals(conversion_status);

-- 4. AI TOKEN USAGE TABLE (track AI token consumption)
CREATE TABLE IF NOT EXISTS ai_token_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    feature_type VARCHAR(100) NOT NULL, -- 'content_generation', 'ad_generation', 'analytics', 'transcript_analysis'
    tokens_used INTEGER NOT NULL,
    cost_cents INTEGER NOT NULL DEFAULT 0,
    request_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_tokens_used CHECK (tokens_used > 0)
);

CREATE INDEX IF NOT EXISTS idx_ai_token_usage_tenant_id ON ai_token_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_usage_user_id ON ai_token_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_usage_feature_type ON ai_token_usage(feature_type);
CREATE INDEX IF NOT EXISTS idx_ai_token_usage_created_at ON ai_token_usage(created_at DESC);

-- 5. AI TOKEN BALANCE TABLE (track token balances per tenant)
CREATE TABLE IF NOT EXISTS ai_token_balances (
    balance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    tokens_purchased INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    tokens_remaining INTEGER DEFAULT 0,
    last_purchase_at TIMESTAMP WITH TIME ZONE,
    last_usage_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_token_balances_tenant_id ON ai_token_balances(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_token_balances_tokens_remaining ON ai_token_balances(tokens_remaining);

-- 6. API USAGE TABLE (track API calls for billing)
CREATE TABLE IF NOT EXISTS api_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    api_key_id UUID,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    cost_cents INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status_code CHECK (status_code >= 100 AND status_code < 600)
);

CREATE INDEX IF NOT EXISTS idx_api_usage_tenant_id ON api_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_api_key_id ON api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at DESC);

-- 7. WHITE LABEL SETTINGS TABLE (for white-labeling)
CREATE TABLE IF NOT EXISTS white_label_settings (
    setting_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    brand_name VARCHAR(255),
    logo_url VARCHAR(500),
    primary_color VARCHAR(7), -- Hex color
    secondary_color VARCHAR(7),
    custom_domain VARCHAR(255),
    custom_css TEXT,
    email_from_name VARCHAR(255),
    email_from_address VARCHAR(255),
    support_email VARCHAR(255),
    support_url VARCHAR(500),
    enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_white_label_settings_tenant_id ON white_label_settings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_white_label_settings_custom_domain ON white_label_settings(custom_domain) WHERE custom_domain IS NOT NULL;

-- 8. SUBSCRIPTION TIERS TABLE (extend tenant subscription tiers)
CREATE TABLE IF NOT EXISTS subscription_tiers (
    tier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    tier_name VARCHAR(50) NOT NULL, -- 'free', 'starter', 'professional', 'enterprise', 'agency', 'white_label'
    monthly_price_cents BIGINT DEFAULT 0,
    ai_tokens_included INTEGER DEFAULT 0,
    api_calls_included INTEGER DEFAULT 0,
    advanced_analytics_enabled BOOLEAN DEFAULT false,
    white_label_enabled BOOLEAN DEFAULT false,
    max_podcasts INTEGER,
    max_episodes_per_month INTEGER,
    max_users INTEGER,
    features JSONB DEFAULT '{}',
    starts_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ends_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_tier_name CHECK (tier_name IN ('free', 'starter', 'professional', 'enterprise', 'agency', 'white_label'))
);

CREATE INDEX IF NOT EXISTS idx_subscription_tiers_tenant_id ON subscription_tiers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_tier_name ON subscription_tiers(tier_name);
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_starts_at ON subscription_tiers(starts_at DESC);

-- 9. BILLING TRANSACTIONS TABLE (track all monetization transactions)
CREATE TABLE IF NOT EXISTS billing_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'subscription', 'ai_tokens', 'api_usage', 'commission', 'affiliate_payout'
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_provider VARCHAR(50),
    external_transaction_id VARCHAR(255),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_transaction_type CHECK (transaction_type IN ('subscription', 'ai_tokens', 'api_usage', 'commission', 'affiliate_payout', 'refund')),
    CONSTRAINT valid_transaction_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_billing_transactions_tenant_id ON billing_transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_type ON billing_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_status ON billing_transactions(status);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_created_at ON billing_transactions(created_at DESC);

COMMIT;
