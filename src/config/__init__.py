"""
Configuration Module

Loads and manages environment variables and configuration.
"""

import os
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration"""
    postgres_host: str
    postgres_port: int
    postgres_database: str
    postgres_user: str
    postgres_password: str
    redis_host: str
    redis_port: int
    redis_password: Optional[str] = None


@dataclass
class APIConfig:
    """API configuration"""
    api_url: str
    api_key: Optional[str] = None
    secret_key: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration"""
    # Database
    database: DatabaseConfig
    
    # API
    api: APIConfig
    
    # Security
    jwt_secret: str
    encryption_key: str
    
    # External Services
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Monitoring
    prometheus_port: int = 9090
    grafana_url: Optional[str] = None
    
    # Environment
    environment: str = "development"
    debug: bool = False


def load_config() -> AppConfig:
    """Load configuration from environment variables"""
    database_config = DatabaseConfig(
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_database=os.getenv("POSTGRES_DATABASE", "podcast_analytics"),
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        redis_password=os.getenv("REDIS_PASSWORD")
    )
    
    api_config = APIConfig(
        api_url=os.getenv("API_URL", "http://localhost:8000"),
        api_key=os.getenv("API_KEY"),
        secret_key=os.getenv("API_SECRET_KEY")
    )
    
    return AppConfig(
        database=database_config,
        api=api_config,
        jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production"),
        encryption_key=os.getenv("ENCRYPTION_KEY", "change-me-in-production"),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY"),
        stripe_publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"),
        sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
        grafana_url=os.getenv("GRAFANA_URL"),
        environment=os.getenv("ENVIRONMENT", "development"),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )


# Global config instance
config = load_config()
