#!/usr/bin/env python3
"""
Sentry Error Tracking Setup

Configures Sentry for error tracking and performance monitoring.
"""

import os
from pathlib import Path


def setup_sentry_config():
    """Generate Sentry configuration"""
    
    config = """# Sentry Configuration
# Add to your .env file

# Sentry DSN (get from https://sentry.io)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Environment
SENTRY_ENVIRONMENT=production  # or development, staging

# Release version (optional)
SENTRY_RELEASE=1.0.0

# Sample rate for performance monitoring (0.0 to 1.0)
SENTRY_TRACES_SAMPLE_RATE=0.1

# Sample rate for profiling (0.0 to 1.0)
SENTRY_PROFILES_SAMPLE_RATE=0.1

# Enable Sentry (set to false to disable)
SENTRY_ENABLED=true
"""
    
    env_example = Path(".env.example")
    if env_example.exists():
        content = env_example.read_text()
        if "SENTRY_DSN" not in content:
            content += "\n# Sentry Error Tracking\n" + config
            env_example.write_text(content)
            print("✅ Added Sentry configuration to .env.example")
    else:
        print("⚠️  .env.example not found")
    
    # Create Sentry initialization file
    sentry_init = Path("src/telemetry/sentry.py")
    sentry_init.parent.mkdir(parents=True, exist_ok=True)
    
    sentry_code = '''"""
Sentry Error Tracking Integration

Provides error tracking and performance monitoring via Sentry.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_sentry_sdk: Optional[object] = None


def init_sentry():
    """Initialize Sentry SDK"""
    global _sentry_sdk
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn or os.getenv("SENTRY_ENABLED", "false").lower() != "true":
        logger.info("Sentry not configured or disabled")
        return None
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            release=os.getenv("SENTRY_RELEASE"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
                AsyncioIntegration(),
            ],
            # Filter out sensitive data
            before_send=lambda event, hint: filter_sensitive_data(event),
        )
        
        _sentry_sdk = sentry_sdk
        logger.info("Sentry initialized successfully")
        return sentry_sdk
        
    except ImportError:
        logger.warning("sentry-sdk not installed. Install with: pip install sentry-sdk")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return None


def filter_sensitive_data(event):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive fields
    if "request" in event and "data" in event["request"]:
        sensitive_keys = ["password", "secret", "token", "api_key", "authorization"]
        for key in sensitive_keys:
            if key in event["request"]["data"]:
                event["request"]["data"][key] = "[Filtered]"
    
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header.lower() in [h.lower() for h in event["request"]["headers"].keys()]:
                event["request"]["headers"][header] = "[Filtered]"
    
    return event


def capture_exception(error: Exception, **kwargs):
    """Capture an exception in Sentry"""
    if _sentry_sdk:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(error, **kwargs)
        except Exception:
            pass  # Don't fail if Sentry fails


def capture_message(message: str, level: str = "info", **kwargs):
    """Capture a message in Sentry"""
    if _sentry_sdk:
        try:
            import sentry_sdk
            sentry_sdk.capture_message(message, level=level, **kwargs)
        except Exception:
            pass


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **kwargs):
    """Add a breadcrumb to Sentry"""
    if _sentry_sdk:
        try:
            import sentry_sdk
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                **kwargs
            )
        except Exception:
            pass
'''
    
    sentry_init.write_text(sentry_code)
    print("✅ Created src/telemetry/sentry.py")
    
    # Update requirements.txt
    requirements = Path("requirements.txt")
    if requirements.exists():
        content = requirements.read_text()
        if "sentry-sdk" not in content:
            content += "\n# Error Tracking\nsentry-sdk==1.38.0\n"
            requirements.write_text(content)
            print("✅ Added sentry-sdk to requirements.txt")
    
    # Update main.py to initialize Sentry
    main_py = Path("src/main.py")
    if main_py.exists():
        content = main_py.read_text()
        if "init_sentry" not in content:
            # Add import after other imports
            import_line = "from src.telemetry.sentry import init_sentry\n"
            if "from src.lifespan import lifespan" in content:
                content = content.replace(
                    "from src.lifespan import lifespan",
                    f"from src.telemetry.sentry import init_sentry\nfrom src.lifespan import lifespan"
                )
                # Initialize in lifespan startup
                if "@asynccontextmanager" in content and "async def lifespan" in content:
                    # Find the startup section
                    if "Startup" in content or "startup" in content.lower():
                        # Add after structured_logger initialization
                        if "structured_logger = StructuredLogger" in content:
                            content = content.replace(
                                "structured_logger = StructuredLogger",
                                "# Initialize Sentry\n    init_sentry()\n    \n    structured_logger = StructuredLogger"
                            )
                            main_py.write_text(content)
                            print("✅ Updated src/main.py to initialize Sentry")
    
    print("\n📋 Next Steps:")
    print("1. Sign up at https://sentry.io")
    print("2. Create a new project")
    print("3. Copy your DSN")
    print("4. Add SENTRY_DSN to your .env file")
    print("5. Install dependencies: pip install sentry-sdk")
    print("6. Restart your application")


if __name__ == "__main__":
    setup_sentry_config()
