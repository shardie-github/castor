#!/usr/bin/env python3
"""
Observability Setup

Configures centralized logging and APM (Application Performance Monitoring).
"""

import os
from pathlib import Path


def setup_centralized_logging():
    """Set up centralized logging configuration"""
    
    logging_config = """# Centralized Logging Configuration
# Add to your .env file

# Log Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log Format (json, text)
LOG_FORMAT=json

# Log Output (console, file, syslog)
LOG_OUTPUT=console

# Log File Path (if LOG_OUTPUT includes file)
LOG_FILE_PATH=/var/log/app.log

# Syslog Host (if LOG_OUTPUT includes syslog)
SYSLOG_HOST=localhost
SYSLOG_PORT=514

# Log Aggregation Service (optional)
# Options: loki, datadog, cloudwatch, elasticsearch
LOG_AGGREGATION_SERVICE=

# Loki URL (if using Loki)
LOKI_URL=http://localhost:3100

# Datadog API Key (if using Datadog)
DATADOG_API_KEY=

# CloudWatch Log Group (if using CloudWatch)
CLOUDWATCH_LOG_GROUP=podcast-analytics

# Elasticsearch URL (if using Elasticsearch)
ELASTICSEARCH_URL=http://localhost:9200
"""
    
    env_example = Path(".env.example")
    if env_example.exists():
        content = env_example.read_text()
        if "LOG_LEVEL" not in content:
            content += "\n# Centralized Logging\n" + logging_config
            env_example.write_text(content)
            print("✅ Added logging configuration to .env.example")
    
    # Create logging configuration module
    logging_module = Path("src/telemetry/centralized_logging.py")
    logging_module.parent.mkdir(parents=True, exist_ok=True)
    
    logging_code = '''"""
Centralized Logging Configuration

Provides centralized logging with support for multiple backends.
"""

import os
import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger


class CentralizedLogger:
    """Centralized logger with multiple backend support"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger configuration"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_format = os.getenv("LOG_FORMAT", "text")
        log_output = os.getenv("LOG_OUTPUT", "console")
        
        # Set log level
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        if log_format == "json":
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        # Console handler
        if "console" in log_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if "file" in log_output:
            log_file = os.getenv("LOG_FILE_PATH", "/var/log/app.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Syslog handler
        if "syslog" in log_output:
            try:
                import logging.handlers
                syslog_host = os.getenv("SYSLOG_HOST", "localhost")
                syslog_port = int(os.getenv("SYSLOG_PORT", "514"))
                syslog_handler = logging.handlers.SysLogHandler(
                    address=(syslog_host, syslog_port)
                )
                syslog_handler.setFormatter(formatter)
                self.logger.addHandler(syslog_handler)
            except Exception as e:
                self.logger.warning(f"Failed to setup syslog: {e}")
        
        # Log aggregation service
        self._setup_log_aggregation()
    
    def _setup_log_aggregation(self):
        """Setup log aggregation service"""
        service = os.getenv("LOG_AGGREGATION_SERVICE", "").lower()
        
        if service == "loki":
            self._setup_loki()
        elif service == "datadog":
            self._setup_datadog()
        elif service == "cloudwatch":
            self._setup_cloudwatch()
        elif service == "elasticsearch":
            self._setup_elasticsearch()
    
    def _setup_loki(self):
        """Setup Loki integration"""
        try:
            from promtail import PromtailHandler
            loki_url = os.getenv("LOKI_URL", "http://localhost:3100")
            handler = PromtailHandler(
                url=f"{loki_url}/loki/api/v1/push",
                labels={"job": "podcast-analytics"}
            )
            self.logger.addHandler(handler)
        except ImportError:
            self.logger.warning("promtail not installed. Install with: pip install promtail")
    
    def _setup_datadog(self):
        """Setup Datadog integration"""
        try:
            from ddtrace import patch_logging
            patch_logging()
        except ImportError:
            self.logger.warning("ddtrace not installed. Install with: pip install ddtrace")
    
    def _setup_cloudwatch(self):
        """Setup CloudWatch integration"""
        try:
            import watchtower
            log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "podcast-analytics")
            handler = watchtower.CloudWatchLogHandler(log_group=log_group)
            self.logger.addHandler(handler)
        except ImportError:
            self.logger.warning("watchtower not installed. Install with: pip install watchtower")
    
    def _setup_elasticsearch(self):
        """Setup Elasticsearch integration"""
        try:
            from pythonjsonlogger import jsonlogger
            # Elasticsearch integration would go here
            # Requires elasticsearch library
            self.logger.warning("Elasticsearch integration not yet implemented")
        except Exception:
            pass
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)


def get_logger(name: str) -> CentralizedLogger:
    """Get centralized logger instance"""
    return CentralizedLogger(name)
'''
    
    logging_module.write_text(logging_code)
    print("✅ Created src/telemetry/centralized_logging.py")
    
    # Update requirements.txt
    requirements = Path("requirements.txt")
    if requirements.exists():
        content = requirements.read_text()
        if "python-json-logger" not in content:
            content += "\n# Centralized Logging\npython-json-logger==2.0.7\n"
            requirements.write_text(content)
            print("✅ Added python-json-logger to requirements.txt")


def setup_apm():
    """Set up APM configuration"""
    
    apm_config = """# APM Configuration
# Add to your .env file

# APM Service Name
APM_SERVICE_NAME=podcast-analytics-api

# APM Provider (datadog, newrelic, elastic, none)
APM_PROVIDER=none

# Datadog APM
DD_AGENT_HOST=localhost
DD_AGENT_PORT=8126
DD_ENV=production
DD_SERVICE=podcast-analytics-api
DD_VERSION=1.0.0

# New Relic APM
NEW_RELIC_LICENSE_KEY=
NEW_RELIC_APP_NAME=Podcast Analytics

# Elastic APM
ELASTIC_APM_SERVER_URL=http://localhost:8200
ELASTIC_APM_SERVICE_NAME=podcast-analytics-api
ELASTIC_APM_ENVIRONMENT=production
"""
    
    env_example = Path(".env.example")
    if env_example.exists():
        content = env_example.read_text()
        if "APM_SERVICE_NAME" not in content:
            content += "\n# APM Configuration\n" + apm_config
            env_example.write_text(content)
            print("✅ Added APM configuration to .env.example")
    
    # Create APM module
    apm_module = Path("src/telemetry/apm_setup.py")
    apm_module.parent.mkdir(parents=True, exist_ok=True)
    
    apm_code = '''"""
APM (Application Performance Monitoring) Setup

Configures APM for performance monitoring and distributed tracing.
"""

import os
import logging

logger = logging.getLogger(__name__)

_apm_enabled = False


def init_apm():
    """Initialize APM based on provider"""
    global _apm_enabled
    
    provider = os.getenv("APM_PROVIDER", "none").lower()
    
    if provider == "none":
        logger.info("APM not configured")
        return None
    
    try:
        if provider == "datadog":
            return _init_datadog_apm()
        elif provider == "newrelic":
            return _init_newrelic_apm()
        elif provider == "elastic":
            return _init_elastic_apm()
        else:
            logger.warning(f"Unknown APM provider: {provider}")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize APM: {e}")
        return None


def _init_datadog_apm():
    """Initialize Datadog APM"""
    try:
        import ddtrace
        from ddtrace import patch_all
        
        ddtrace.config.service = os.getenv("DD_SERVICE", "podcast-analytics-api")
        ddtrace.config.env = os.getenv("DD_ENV", "production")
        ddtrace.config.version = os.getenv("DD_VERSION", "1.0.0")
        
        # Patch common libraries
        patch_all()
        
        _apm_enabled = True
        logger.info("Datadog APM initialized")
        return ddtrace
    except ImportError:
        logger.warning("ddtrace not installed. Install with: pip install ddtrace")
        return None


def _init_newrelic_apm():
    """Initialize New Relic APM"""
    try:
        import newrelic.agent
        
        license_key = os.getenv("NEW_RELIC_LICENSE_KEY")
        app_name = os.getenv("NEW_RELIC_APP_NAME", "Podcast Analytics")
        
        if not license_key:
            logger.warning("NEW_RELIC_LICENSE_KEY not set")
            return None
        
        newrelic.agent.initialize()
        
        _apm_enabled = True
        logger.info("New Relic APM initialized")
        return newrelic.agent
    except ImportError:
        logger.warning("newrelic not installed. Install with: pip install newrelic")
        return None


def _init_elastic_apm():
    """Initialize Elastic APM"""
    try:
        from elasticapm import Client
        
        server_url = os.getenv("ELASTIC_APM_SERVER_URL", "http://localhost:8200")
        service_name = os.getenv("ELASTIC_APM_SERVICE_NAME", "podcast-analytics-api")
        environment = os.getenv("ELASTIC_APM_ENVIRONMENT", "production")
        
        client = Client(
            service_name=service_name,
            server_url=server_url,
            environment=environment
        )
        
        _apm_enabled = True
        logger.info("Elastic APM initialized")
        return client
    except ImportError:
        logger.warning("elasticapm not installed. Install with: pip install elasticapm")
        return None


def is_apm_enabled() -> bool:
    """Check if APM is enabled"""
    return _apm_enabled
'''
    
    apm_module.write_text(apm_code)
    print("✅ Created src/telemetry/apm_setup.py")
    
    print("\n📋 Next Steps:")
    print("1. Choose an APM provider (Datadog, New Relic, or Elastic)")
    print("2. Install the corresponding package:")
    print("   - Datadog: pip install ddtrace")
    print("   - New Relic: pip install newrelic")
    print("   - Elastic: pip install elasticapm")
    print("3. Configure APM_PROVIDER and related env vars in .env")
    print("4. Restart your application")


if __name__ == "__main__":
    print("🔍 Setting up Observability...\n")
    setup_centralized_logging()
    setup_apm()
    print("\n✅ Observability setup complete!")
