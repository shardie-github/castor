#!/usr/bin/env python3
"""
Demo Data Seeding Script

Populates the database with sample data for demos and testing.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import asyncpg

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Demo data configuration
DEMO_TENANT_NAME = "Demo Podcast Network"
DEMO_TENANT_SLUG = "demo-podcast-network"
DEMO_USER_EMAIL = "demo@example.com"
DEMO_USER_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Yu"  # "demo123" (bcrypt)


async def seed_demo_data(database_url: str):
    """Seed database with demo data"""
    conn = await asyncpg.connect(database_url)
    
    try:
        # Create demo tenant
        tenant_id = await conn.fetchval("""
            INSERT INTO tenants (id, name, slug, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, uuid4(), DEMO_TENANT_NAME, DEMO_TENANT_SLUG)
        
        print(f"✅ Created tenant: {DEMO_TENANT_NAME} ({tenant_id})")
        
        # Create demo user
        user_id = await conn.fetchval("""
            INSERT INTO users (id, email, password_hash, tenant_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
            RETURNING id
        """, uuid4(), DEMO_USER_EMAIL, DEMO_USER_PASSWORD_HASH, tenant_id)
        
        print(f"✅ Created user: {DEMO_USER_EMAIL} ({user_id})")
        
        # Create sample podcasts
        podcast_names = [
            "Tech Talk Weekly",
            "Business Insights",
            "Creative Minds"
        ]
        
        podcast_ids = []
        for podcast_name in podcast_names:
            podcast_id = await conn.fetchval("""
                INSERT INTO podcasts (id, name, tenant_id, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                RETURNING id
            """, uuid4(), podcast_name, tenant_id)
            podcast_ids.append(podcast_id)
            print(f"✅ Created podcast: {podcast_name}")
        
        # Create sample episodes
        episode_titles = [
            "Introduction to AI",
            "Building Your First SaaS",
            "Design Thinking 101",
            "Scaling Your Business",
            "The Future of Work"
        ]
        
        episode_ids = []
        for i, title in enumerate(episode_titles):
            podcast_id = podcast_ids[i % len(podcast_ids)]
            episode_id = await conn.fetchval("""
                INSERT INTO episodes (id, podcast_id, title, published_at, created_at, updated_at)
                VALUES ($1, $2, $3, NOW() - INTERVAL '%s days', NOW(), NOW())
                RETURNING id
            """, uuid4(), podcast_id, title, i * 7)
            episode_ids.append(episode_id)
            print(f"✅ Created episode: {title}")
        
        # Create sample campaigns
        campaign_names = [
            "Q1 2024 Sponsorship",
            "Summer Promotion",
            "Holiday Campaign"
        ]
        
        campaign_ids = []
        for campaign_name in campaign_names:
            campaign_id = await conn.fetchval("""
                INSERT INTO campaigns (id, name, tenant_id, status, created_at, updated_at)
                VALUES ($1, $2, $3, 'active', NOW(), NOW())
                RETURNING id
            """, uuid4(), campaign_name, tenant_id)
            campaign_ids.append(campaign_id)
            print(f"✅ Created campaign: {campaign_name}")
        
        # Create sample listener events (last 30 days)
        print("✅ Creating listener events...")
        for day in range(30):
            date = datetime.now() - timedelta(days=day)
            for episode_id in episode_ids:
                # Random listener count (10-1000 per episode per day)
                listener_count = (day % 10 + 1) * 100
                
                await conn.execute("""
                    INSERT INTO listener_events (id, episode_id, event_type, event_data, created_at)
                    VALUES ($1, $2, 'download', $3::jsonb, $4)
                    ON CONFLICT DO NOTHING
                """, uuid4(), episode_id, {
                    "listener_count": listener_count,
                    "date": date.isoformat()
                }, date)
        
        print(f"✅ Created listener events for last 30 days")
        
        # Create sample attribution events
        print("✅ Creating attribution events...")
        for campaign_id in campaign_ids:
            for day in range(7):  # Last 7 days
                date = datetime.now() - timedelta(days=day)
                
                await conn.execute("""
                    INSERT INTO attribution_events (id, campaign_id, event_type, event_data, created_at)
                    VALUES ($1, $2, 'click', $3::jsonb, $4)
                    ON CONFLICT DO NOTHING
                """, uuid4(), campaign_id, {
                    "clicks": (day % 5 + 1) * 10,
                    "conversions": (day % 3 + 1) * 2,
                    "date": date.isoformat()
                }, date)
        
        print(f"✅ Created attribution events for campaigns")
        
        print("\n✅ Demo data seeding completed!")
        print(f"\nDemo credentials:")
        print(f"  Email: {DEMO_USER_EMAIL}")
        print(f"  Password: demo123")
        
    except Exception as e:
        print(f"❌ Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await conn.close()


def main():
    """Main entry point"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    print("🌱 Seeding demo data...")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print()
    
    asyncio.run(seed_demo_data(database_url))


if __name__ == "__main__":
    main()
