-- Partnerships Schema Migration
-- Adds referral program, marketplace, and partner portal tables

-- 1. Referrals Table
CREATE TABLE IF NOT EXISTS referrals (
    referral_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id VARCHAR(255) NOT NULL,
    referred_customer_id UUID REFERENCES tenants(tenant_id) ON DELETE SET NULL,
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    referral_link TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled')),
    first_year_commission_rate DECIMAL(5,4) NOT NULL DEFAULT 0.2000 CHECK (first_year_commission_rate >= 0 AND first_year_commission_rate <= 1),
    recurring_commission_rate DECIMAL(5,4) NOT NULL DEFAULT 0.1000 CHECK (recurring_commission_rate >= 0 AND recurring_commission_rate <= 1),
    total_commission_earned DECIMAL(12,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    converted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referral_code ON referrals(referral_code);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_customer ON referrals(referred_customer_id) WHERE referred_customer_id IS NOT NULL;

-- 2. Referral Commissions Table
CREATE TABLE IF NOT EXISTS referral_commissions (
    commission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_id UUID NOT NULL REFERENCES referrals(referral_id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    revenue_amount DECIMAL(12,2) NOT NULL,
    commission_rate DECIMAL(5,4) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'calculated' CHECK (status IN ('pending', 'calculated', 'paid', 'cancelled')),
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_referral_commissions_referral_id ON referral_commissions(referral_id);
CREATE INDEX IF NOT EXISTS idx_referral_commissions_status ON referral_commissions(status);
CREATE INDEX IF NOT EXISTS idx_referral_commissions_period ON referral_commissions(period_start, period_end);

-- 3. Marketplace Listings Table
CREATE TABLE IF NOT EXISTS marketplace_listings (
    listing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketplace_type VARCHAR(50) NOT NULL CHECK (marketplace_type IN ('shopify', 'woocommerce', 'bigcommerce', 'squarespace', 'wix', 'google_workspace', 'zapier')),
    app_id VARCHAR(255),
    app_name VARCHAR(255) NOT NULL,
    app_description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'approved', 'live', 'suspended', 'rejected')),
    revenue_share_rate DECIMAL(5,4) NOT NULL DEFAULT 0.2000 CHECK (revenue_share_rate >= 0 AND revenue_share_rate <= 1),
    total_revenue DECIMAL(12,2) DEFAULT 0.00,
    total_installs INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_marketplace_listings_type ON marketplace_listings(marketplace_type);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_status ON marketplace_listings(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_app_id ON marketplace_listings(app_id) WHERE app_id IS NOT NULL;

-- 4. Marketplace Revenue Table
CREATE TABLE IF NOT EXISTS marketplace_revenue (
    revenue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES marketplace_listings(listing_id) ON DELETE CASCADE,
    customer_id UUID REFERENCES tenants(tenant_id) ON DELETE SET NULL,
    total_revenue DECIMAL(12,2) NOT NULL,
    marketplace_share DECIMAL(12,2) NOT NULL,
    our_revenue DECIMAL(12,2) NOT NULL,
    revenue_share_rate DECIMAL(5,4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_marketplace_revenue_listing_id ON marketplace_revenue(listing_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_revenue_customer_id ON marketplace_revenue(customer_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_revenue_created_at ON marketplace_revenue(created_at DESC);

-- 5. Partners Table
CREATE TABLE IF NOT EXISTS partners (
    partner_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_name VARCHAR(255) NOT NULL,
    partner_type VARCHAR(50) NOT NULL CHECK (partner_type IN ('technology', 'distribution', 'co_marketing', 'strategic')),
    contact_email VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    partnership_start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    partnership_end_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partners_type ON partners(partner_type);
CREATE INDEX IF NOT EXISTS idx_partners_status ON partners(status);

-- 6. Partner Integrations Table
CREATE TABLE IF NOT EXISTS partner_integrations (
    integration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID NOT NULL REFERENCES partners(partner_id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL,
    integration_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (integration_status IN ('pending', 'active', 'inactive', 'error')),
    api_credentials JSONB,
    webhook_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_partner_integrations_partner_id ON partner_integrations(partner_id);
CREATE INDEX IF NOT EXISTS idx_partner_integrations_status ON partner_integrations(integration_status);

-- Add RLS policies for multi-tenancy (where applicable)
-- Referrals and marketplace revenue may reference tenant_id
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_revenue ENABLE ROW LEVEL SECURITY;

CREATE POLICY referrals_tenant_isolation ON referrals
    FOR ALL
    USING (
        referred_customer_id IS NULL OR 
        referred_customer_id = current_setting('app.current_tenant_id', TRUE)::UUID
    );

CREATE POLICY marketplace_revenue_tenant_isolation ON marketplace_revenue
    FOR ALL
    USING (
        customer_id IS NULL OR 
        customer_id = current_setting('app.current_tenant_id', TRUE)::UUID
    );
