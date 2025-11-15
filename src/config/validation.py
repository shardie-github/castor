"""
Environment Variable Validation

Validates all environment variables using Pydantic schemas.
Ensures required variables are present and have correct types.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, validator, ValidationError
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Database configuration validation"""
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    postgres_database: str = Field(..., description="PostgreSQL database name")
    postgres_user: str = Field(..., description="PostgreSQL username")
    postgres_password: str = Field(..., description="PostgreSQL password")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")


class SecuritySettings(BaseModel):
    """Security configuration validation"""
    jwt_secret: str = Field(..., min_length=32, description="JWT secret key (min 32 chars)")
    encryption_key: str = Field(..., min_length=32, description="Encryption key (min 32 chars)")
    
    @validator("jwt_secret", "encryption_key")
    def validate_secret_not_default(cls, v):
        """Ensure secrets are not default values"""
        if v in ["change-me-in-production", "change-me-in-production-generate-random-secret", "change-me-in-production-generate-random-key"]:
            raise ValueError("Security keys must be changed from default values")
        return v


class ExternalServicesSettings(BaseModel):
    """External services configuration"""
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe secret key")
    stripe_publishable_key: Optional[str] = Field(default=None, description="Stripe publishable key")
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    
    supabase_url: Optional[str] = Field(default=None, description="Supabase project URL")
    supabase_service_role_key: Optional[str] = Field(default=None, description="Supabase service role key")
    supabase_anon_key: Optional[str] = Field(default=None, description="Supabase anonymous key")


class CORSSettings(BaseModel):
    """CORS configuration validation"""
    cors_allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_allowed_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_max_age: int = Field(default=3600, ge=0, description="CORS max age in seconds")
    
    @validator("cors_allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @validator("cors_allowed_methods", pre=True)
    def parse_cors_methods(cls, v):
        """Parse comma-separated HTTP methods"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",") if method.strip()]
        return v


class RateLimitSettings(BaseModel):
    """Rate limiting configuration"""
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Requests per minute")
    rate_limit_per_hour: int = Field(default=1000, ge=1, description="Requests per hour")
    rate_limit_per_day: int = Field(default=10000, ge=1, description="Requests per day")


class EnvironmentSettings(BaseSettings):
    """Complete environment settings with validation"""
    # Database
    database: DatabaseSettings
    
    # Security
    security: SecuritySettings
    
    # External Services
    external_services: ExternalServicesSettings
    
    # CORS
    cors: CORSSettings
    
    # Rate Limiting
    rate_limit: RateLimitSettings
    
    # Monitoring
    prometheus_port: int = Field(default=9090, ge=1, le=65535)
    grafana_url: Optional[str] = None
    
    # Environment
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Feature Flags
    enable_etl_csv_upload: bool = Field(default=False, alias="ENABLE_ETL_CSV_UPLOAD")
    enable_matchmaking: bool = Field(default=False, alias="ENABLE_MATCHMAKING")
    enable_io_bookings: bool = Field(default=False, alias="ENABLE_IO_BOOKINGS")
    enable_deal_pipeline: bool = Field(default=False, alias="ENABLE_DEAL_PIPELINE")
    enable_new_dashboard_cards: bool = Field(default=False, alias="ENABLE_NEW_DASHBOARD_CARDS")
    enable_orchestration: bool = Field(default=False, alias="ENABLE_ORCHESTRATION")
    enable_monetization: bool = Field(default=False, alias="ENABLE_MONETIZATION")
    enable_automation_jobs: bool = Field(default=False, alias="ENABLE_AUTOMATION_JOBS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        allow_population_by_field_name = True


def load_and_validate_env() -> EnvironmentSettings:
    """
    Load and validate environment variables.
    
    Raises:
        ValidationError: If required environment variables are missing or invalid
    
    Returns:
        EnvironmentSettings: Validated environment settings
    """
    try:
        # Parse database settings
        database = DatabaseSettings(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_database=os.getenv("POSTGRES_DATABASE", "podcast_analytics"),
            postgres_user=os.getenv("POSTGRES_USER", "postgres"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD")
        )
        
        # Parse security settings
        security = SecuritySettings(
            jwt_secret=os.getenv("JWT_SECRET", ""),
            encryption_key=os.getenv("ENCRYPTION_KEY", "")
        )
        
        # Parse external services
        external_services = ExternalServicesSettings(
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY"),
            stripe_publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"),
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Parse CORS settings
        cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
        cors_methods = os.getenv("CORS_ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS")
        
        cors = CORSSettings(
            cors_allowed_origins=cors_origins,
            cors_allowed_methods=cors_methods,
            cors_allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            cors_max_age=int(os.getenv("CORS_MAX_AGE", "3600"))
        )
        
        # Parse rate limit settings
        rate_limit = RateLimitSettings(
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            rate_limit_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
            rate_limit_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "10000"))
        )
        
        # Create complete settings
        settings = EnvironmentSettings(
            database=database,
            security=security,
            external_services=external_services,
            cors=cors,
            rate_limit=rate_limit,
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
            grafana_url=os.getenv("GRAFANA_URL"),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            enable_etl_csv_upload=os.getenv("ENABLE_ETL_CSV_UPLOAD", "false").lower() == "true",
            enable_matchmaking=os.getenv("ENABLE_MATCHMAKING", "false").lower() == "true",
            enable_io_bookings=os.getenv("ENABLE_IO_BOOKINGS", "false").lower() == "true",
            enable_deal_pipeline=os.getenv("ENABLE_DEAL_PIPELINE", "false").lower() == "true",
            enable_new_dashboard_cards=os.getenv("ENABLE_NEW_DASHBOARD_CARDS", "false").lower() == "true",
            enable_orchestration=os.getenv("ENABLE_ORCHESTRATION", "false").lower() == "true",
            enable_monetization=os.getenv("ENABLE_MONETIZATION", "false").lower() == "true",
            enable_automation_jobs=os.getenv("ENABLE_AUTOMATION_JOBS", "false").lower() == "true"
        )
        
        return settings
        
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_messages.append(f"{field}: {error['msg']}")
        
        raise ValueError(
            f"Environment validation failed:\n" + "\n".join(error_messages)
        ) from e


# Validate on import (can be disabled for testing)
if os.getenv("SKIP_ENV_VALIDATION", "false").lower() != "true":
    try:
        validated_env = load_and_validate_env()
    except ValueError as e:
        import logging
        logging.warning(f"Environment validation warning: {e}")
        # In development, we might want to continue with defaults
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise
