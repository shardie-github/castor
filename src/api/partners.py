"""
Partnership API Endpoints

Referral program, marketplace, and partner portal APIs.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from src.partners.referral import ReferralProgram, ReferralStatus
from src.partners.marketplace import MarketplaceManager, MarketplaceType, ListingStatus
from src.partners.portal import PartnerPortal

router = APIRouter(prefix="/api/v1/partners", tags=["partners"])


# Referral Models
class ReferralCreate(BaseModel):
    referrer_id: str
    referral_code: Optional[str] = None
    first_year_rate: float = Field(0.20, ge=0, le=1)
    recurring_rate: float = Field(0.10, ge=0, le=1)
    metadata: Optional[dict] = {}


class ReferralConversion(BaseModel):
    referral_code: str
    customer_id: str
    customer_revenue: float


class ReferralResponse(BaseModel):
    referral_id: str
    referrer_id: str
    referred_customer_id: Optional[str]
    referral_code: str
    referral_link: str
    status: str
    first_year_commission_rate: float
    recurring_commission_rate: float
    total_commission_earned: float
    created_at: datetime
    converted_at: Optional[datetime]
    metadata: dict

    class Config:
        from_attributes = True


# Marketplace Models
class MarketplaceListingCreate(BaseModel):
    marketplace_type: MarketplaceType
    app_name: str
    app_description: str
    revenue_share_rate: float = Field(0.20, ge=0, le=1)
    metadata: Optional[dict] = {}


class MarketplaceInstall(BaseModel):
    listing_id: str
    customer_id: str
    revenue: float


class MarketplaceListingResponse(BaseModel):
    listing_id: str
    marketplace_type: str
    app_id: Optional[str]
    app_name: str
    app_description: str
    status: str
    revenue_share_rate: float
    total_revenue: float
    total_installs: int
    created_at: datetime
    published_at: Optional[datetime]
    metadata: dict

    class Config:
        from_attributes = True


# Dependencies
def get_referral_program() -> ReferralProgram:
    from src.main import referral_program
    return referral_program


def get_marketplace_manager() -> MarketplaceManager:
    from src.main import marketplace_manager
    return marketplace_manager


def get_partner_portal() -> PartnerPortal:
    from src.main import partner_portal
    return partner_portal


# Referral Endpoints
@router.post("/referrals", response_model=ReferralResponse, status_code=201)
async def create_referral(
    referral_data: ReferralCreate,
    referral_program: ReferralProgram = Depends(get_referral_program)
):
    """Create a new referral code"""
    try:
        referral = await referral_program.create_referral(
            referrer_id=referral_data.referrer_id,
            referral_code=referral_data.referral_code,
            first_year_rate=referral_data.first_year_rate,
            recurring_rate=referral_data.recurring_rate,
            metadata=referral_data.metadata
        )
        
        return ReferralResponse(
            referral_id=referral.referral_id,
            referrer_id=referral.referrer_id,
            referred_customer_id=referral.referred_customer_id,
            referral_code=referral.referral_code,
            referral_link=referral.referral_link,
            status=referral.status.value,
            first_year_commission_rate=referral.first_year_commission_rate,
            recurring_commission_rate=referral.recurring_commission_rate,
            total_commission_earned=referral.total_commission_earned,
            created_at=referral.created_at,
            converted_at=referral.converted_at,
            metadata=referral.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/referrals/convert")
async def convert_referral(
    conversion: ReferralConversion,
    referral_program: ReferralProgram = Depends(get_referral_program)
):
    """Track referral conversion"""
    referral = await referral_program.track_referral_conversion(
        referral_code=conversion.referral_code,
        customer_id=conversion.customer_id,
        customer_revenue=conversion.customer_revenue
    )
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    return {"status": "converted", "referral_id": referral.referral_id}


@router.get("/referrals/{referral_id}", response_model=ReferralResponse)
async def get_referral(
    referral_id: str,
    referral_program: ReferralProgram = Depends(get_referral_program)
):
    """Get a referral by ID"""
    referral = await referral_program.get_referral(referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    return ReferralResponse(
        referral_id=referral.referral_id,
        referrer_id=referral.referrer_id,
        referred_customer_id=referral.referred_customer_id,
        referral_code=referral.referral_code,
        referral_link=referral.referral_link,
        status=referral.status.value,
        first_year_commission_rate=referral.first_year_commission_rate,
        recurring_commission_rate=referral.recurring_commission_rate,
        total_commission_earned=referral.total_commission_earned,
        created_at=referral.created_at,
        converted_at=referral.converted_at,
        metadata=referral.metadata
    )


@router.get("/referrals", response_model=List[ReferralResponse])
async def list_referrals(
    referrer_id: Optional[str] = None,
    status: Optional[ReferralStatus] = None,
    limit: int = 100,
    offset: int = 0,
    referral_program: ReferralProgram = Depends(get_referral_program)
):
    """List referrals"""
    referrals = await referral_program.list_referrals(
        referrer_id=referrer_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return [
        ReferralResponse(
            referral_id=r.referral_id,
            referrer_id=r.referrer_id,
            referred_customer_id=r.referred_customer_id,
            referral_code=r.referral_code,
            referral_link=r.referral_link,
            status=r.status.value,
            first_year_commission_rate=r.first_year_commission_rate,
            recurring_commission_rate=r.recurring_commission_rate,
            total_commission_earned=r.total_commission_earned,
            created_at=r.created_at,
            converted_at=r.converted_at,
            metadata=r.metadata
        )
        for r in referrals
    ]


@router.get("/referrals/stats/{referrer_id}")
async def get_referral_stats(
    referrer_id: str,
    referral_program: ReferralProgram = Depends(get_referral_program)
):
    """Get referral statistics"""
    stats = await referral_program.get_referral_stats(referrer_id)
    return stats


# Marketplace Endpoints
@router.post("/marketplace/listings", response_model=MarketplaceListingResponse, status_code=201)
async def create_listing(
    listing_data: MarketplaceListingCreate,
    marketplace_manager: MarketplaceManager = Depends(get_marketplace_manager)
):
    """Create a marketplace listing"""
    try:
        listing = await marketplace_manager.create_listing(
            marketplace_type=listing_data.marketplace_type,
            app_name=listing_data.app_name,
            app_description=listing_data.app_description,
            revenue_share_rate=listing_data.revenue_share_rate,
            metadata=listing_data.metadata
        )
        
        return MarketplaceListingResponse(
            listing_id=listing.listing_id,
            marketplace_type=listing.marketplace_type.value,
            app_id=listing.app_id,
            app_name=listing.app_name,
            app_description=listing.app_description,
            status=listing.status.value,
            revenue_share_rate=listing.revenue_share_rate,
            total_revenue=listing.total_revenue,
            total_installs=listing.total_installs,
            created_at=listing.created_at,
            published_at=listing.published_at,
            metadata=listing.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/installs")
async def track_install(
    install: MarketplaceInstall,
    marketplace_manager: MarketplaceManager = Depends(get_marketplace_manager)
):
    """Track a marketplace install"""
    await marketplace_manager.track_install(
        listing_id=install.listing_id,
        customer_id=install.customer_id,
        revenue=install.revenue
    )
    
    return {"status": "tracked"}


@router.get("/marketplace/listings/{listing_id}", response_model=MarketplaceListingResponse)
async def get_listing(
    listing_id: str,
    marketplace_manager: MarketplaceManager = Depends(get_marketplace_manager)
):
    """Get a marketplace listing"""
    listing = await marketplace_manager.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return MarketplaceListingResponse(
        listing_id=listing.listing_id,
        marketplace_type=listing.marketplace_type.value,
        app_id=listing.app_id,
        app_name=listing.app_name,
        app_description=listing.app_description,
        status=listing.status.value,
        revenue_share_rate=listing.revenue_share_rate,
        total_revenue=listing.total_revenue,
        total_installs=listing.total_installs,
        created_at=listing.created_at,
        published_at=listing.published_at,
        metadata=listing.metadata
    )


@router.get("/marketplace/listings", response_model=List[MarketplaceListingResponse])
async def list_listings(
    marketplace_type: Optional[MarketplaceType] = None,
    status: Optional[ListingStatus] = None,
    limit: int = 100,
    offset: int = 0,
    marketplace_manager: MarketplaceManager = Depends(get_marketplace_manager)
):
    """List marketplace listings"""
    listings = await marketplace_manager.list_listings(
        marketplace_type=marketplace_type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return [
        MarketplaceListingResponse(
            listing_id=l.listing_id,
            marketplace_type=l.marketplace_type.value,
            app_id=l.app_id,
            app_name=l.app_name,
            app_description=l.app_description,
            status=l.status.value,
            revenue_share_rate=l.revenue_share_rate,
            total_revenue=l.total_revenue,
            total_installs=l.total_installs,
            created_at=l.created_at,
            published_at=l.published_at,
            metadata=l.metadata
        )
        for l in listings
    ]


@router.get("/marketplace/stats")
async def get_marketplace_stats(
    marketplace_manager: MarketplaceManager = Depends(get_marketplace_manager)
):
    """Get marketplace statistics"""
    stats = await marketplace_manager.get_marketplace_stats()
    return stats


# Partner Portal Endpoints
@router.get("/portal/dashboard/{partner_id}")
async def get_partner_dashboard(
    partner_id: str,
    partner_portal: PartnerPortal = Depends(get_partner_portal)
):
    """Get partner dashboard"""
    dashboard = await partner_portal.get_partner_dashboard(partner_id)
    return dashboard


@router.get("/portal/integrations/{integration_type}")
async def get_integration_docs(
    integration_type: str,
    partner_portal: PartnerPortal = Depends(get_partner_portal)
):
    """Get integration documentation"""
    docs = await partner_portal.get_integration_documentation(integration_type)
    return docs


@router.get("/portal/marketing-materials")
async def get_marketing_materials(
    partner_portal: PartnerPortal = Depends(get_partner_portal)
):
    """Get marketing materials"""
    materials = await partner_portal.get_marketing_materials()
    return materials
