"""
Privacy, Compliance, and Security Validation Framework

Validates compliance for each new segment and operational pattern.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    NOT_APPLICABLE = "not_applicable"


class SecurityLevel(Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceCheck:
    """Compliance check result"""
    check_id: str
    standard: ComplianceStandard
    status: ComplianceStatus
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    checked_by: Optional[str] = None


@dataclass
class SecurityAssessment:
    """Security assessment result"""
    assessment_id: str
    security_level: SecurityLevel
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assessed_by: Optional[str] = None


@dataclass
class PrivacyImpactAssessment:
    """Privacy Impact Assessment (PIA)"""
    pia_id: str
    feature_name: str
    data_types_collected: List[str]
    data_retention_period: Optional[int] = None
    data_sharing: List[str] = field(default_factory=list)
    user_consent_required: bool = False
    data_subject_rights: List[str] = field(default_factory=list)
    compliance_status: ComplianceStatus = ComplianceStatus.REQUIRES_REVIEW
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ComplianceValidator:
    """
    Compliance Validator
    
    Validates privacy, compliance, and security for new segments and operational patterns.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._checks: Dict[str, ComplianceCheck] = {}
        self._assessments: Dict[str, SecurityAssessment] = {}
        self._pias: Dict[str, PrivacyImpactAssessment] = {}
        
        # Compliance requirements by standard
        self.compliance_requirements = {
            ComplianceStandard.GDPR: [
                "data_minimization",
                "purpose_limitation",
                "storage_limitation",
                "data_subject_rights",
                "consent_management",
                "data_breach_notification",
                "privacy_by_design"
            ],
            ComplianceStandard.CCPA: [
                "right_to_know",
                "right_to_delete",
                "right_to_opt_out",
                "non_discrimination",
                "data_transparency"
            ],
            ComplianceStandard.SOC2: [
                "access_controls",
                "encryption",
                "monitoring",
                "incident_response",
                "change_management"
            ]
        }
        
    async def validate_segment_compliance(
        self,
        segment_name: str,
        segment_metadata: Dict[str, Any],
        applicable_standards: List[ComplianceStandard]
    ) -> Dict[str, ComplianceCheck]:
        """
        Validate compliance for a new user segment
        
        Args:
            segment_name: Name of the segment
            segment_metadata: Segment metadata (data collected, processing, etc.)
            applicable_standards: List of compliance standards to check
            
        Returns:
            Dictionary of compliance checks by standard
        """
        checks = {}
        
        for standard in applicable_standards:
            check = await self._check_compliance_standard(
                segment_name,
                segment_metadata,
                standard
            )
            checks[standard.value] = check
            self._checks[check.check_id] = check
        
        # Record metrics
        compliant_count = sum(
            1 for c in checks.values()
            if c.status == ComplianceStatus.COMPLIANT
        )
        
        self.metrics.record_gauge(
            "compliance_check_compliant_count",
            compliant_count,
            tags={"segment": segment_name, "total_standards": len(applicable_standards)}
        )
        
        await self.events.log_event(
            event_type="segment_compliance_validated",
            user_id=None,
            properties={
                "segment_name": segment_name,
                "compliant_standards": compliant_count,
                "total_standards": len(applicable_standards),
                "checks": {k: v.status.value for k, v in checks.items()}
            }
        )
        
        return checks
    
    async def _check_compliance_standard(
        self,
        segment_name: str,
        metadata: Dict[str, Any],
        standard: ComplianceStandard
    ) -> ComplianceCheck:
        """Check compliance against a specific standard"""
        check_id = str(uuid4())
        findings = []
        recommendations = []
        
        requirements = self.compliance_requirements.get(standard, [])
        
        # Check each requirement
        for requirement in requirements:
            if requirement == "data_minimization":
                if metadata.get("data_collected", {}).get("excessive", False):
                    findings.append("Data minimization: Collecting more data than necessary")
                    recommendations.append("Review data collection and minimize to essential fields only")
            
            elif requirement == "consent_management":
                if not metadata.get("consent_obtained", False):
                    findings.append("Consent management: User consent not obtained")
                    recommendations.append("Implement consent management system")
            
            elif requirement == "data_subject_rights":
                rights_supported = metadata.get("data_subject_rights_supported", [])
                required_rights = ["access", "rectification", "erasure", "portability"]
                missing_rights = [r for r in required_rights if r not in rights_supported]
                if missing_rights:
                    findings.append(f"Data subject rights: Missing support for {', '.join(missing_rights)}")
                    recommendations.append(f"Implement support for: {', '.join(missing_rights)}")
            
            elif requirement == "encryption":
                if not metadata.get("encryption_at_rest", False) or not metadata.get("encryption_in_transit", False):
                    findings.append("Encryption: Missing encryption for data at rest or in transit")
                    recommendations.append("Implement encryption for data at rest and in transit")
            
            elif requirement == "access_controls":
                if not metadata.get("access_controls_implemented", False):
                    findings.append("Access controls: Access controls not properly implemented")
                    recommendations.append("Implement role-based access controls")
        
        # Determine status
        if not findings:
            status = ComplianceStatus.COMPLIANT
        elif len(findings) <= 2:
            status = ComplianceStatus.REQUIRES_REVIEW
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        check = ComplianceCheck(
            check_id=check_id,
            standard=standard,
            status=status,
            findings=findings,
            recommendations=recommendations
        )
        
        return check
    
    async def assess_security(
        self,
        feature_name: str,
        feature_metadata: Dict[str, Any]
    ) -> SecurityAssessment:
        """
        Assess security for a feature or operational pattern
        
        Args:
            feature_name: Name of feature/pattern
            feature_metadata: Metadata including security considerations
            
        Returns:
            SecurityAssessment
        """
        assessment_id = str(uuid4())
        vulnerabilities = []
        mitigations = []
        
        # Check for common vulnerabilities
        if not feature_metadata.get("authentication_required", True):
            vulnerabilities.append({
                "type": "authentication",
                "severity": "high",
                "description": "Feature may not require authentication"
            })
            mitigations.append("Require authentication for all user-facing features")
        
        if feature_metadata.get("sensitive_data_handled", False):
            if not feature_metadata.get("encryption_implemented", False):
                vulnerabilities.append({
                    "type": "encryption",
                    "severity": "critical",
                    "description": "Sensitive data handled without encryption"
                })
                mitigations.append("Implement encryption for sensitive data")
        
        if feature_metadata.get("sql_queries", False):
            if not feature_metadata.get("parameterized_queries", True):
                vulnerabilities.append({
                    "type": "sql_injection",
                    "severity": "critical",
                    "description": "SQL queries may be vulnerable to injection"
                })
                mitigations.append("Use parameterized queries to prevent SQL injection")
        
        if feature_metadata.get("user_input_accepted", False):
            if not feature_metadata.get("input_validation", False):
                vulnerabilities.append({
                    "type": "input_validation",
                    "severity": "medium",
                    "description": "User input not validated"
                })
                mitigations.append("Implement input validation and sanitization")
        
        # Determine security level
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        high_vulns = [v for v in vulnerabilities if v.get("severity") == "high"]
        
        if critical_vulns:
            security_level = SecurityLevel.CRITICAL
        elif high_vulns:
            security_level = SecurityLevel.HIGH
        elif vulnerabilities:
            security_level = SecurityLevel.MEDIUM
        else:
            security_level = SecurityLevel.LOW
        
        assessment = SecurityAssessment(
            assessment_id=assessment_id,
            security_level=security_level,
            vulnerabilities=vulnerabilities,
            mitigations=mitigations
        )
        
        self._assessments[assessment_id] = assessment
        
        # Record metrics
        self.metrics.record_gauge(
            "security_assessment_level",
            {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(security_level.value, 0),
            tags={"feature": feature_name}
        )
        
        await self.events.log_event(
            event_type="security_assessed",
            user_id=None,
            properties={
                "assessment_id": assessment_id,
                "feature_name": feature_name,
                "security_level": security_level.value,
                "vulnerability_count": len(vulnerabilities)
            }
        )
        
        return assessment
    
    async def conduct_privacy_impact_assessment(
        self,
        feature_name: str,
        data_types_collected: List[str],
        data_retention_period: Optional[int] = None,
        data_sharing: Optional[List[str]] = None,
        user_consent_required: bool = False
    ) -> PrivacyImpactAssessment:
        """
        Conduct Privacy Impact Assessment (PIA)
        
        Args:
            feature_name: Name of feature
            data_types_collected: Types of data collected
            data_retention_period: Data retention period in days
            data_sharing: List of third parties data is shared with
            user_consent_required: Whether user consent is required
            
        Returns:
            PrivacyImpactAssessment
        """
        pia_id = str(uuid4())
        
        # Determine data subject rights based on data types
        data_subject_rights = []
        if any("personal" in dt.lower() for dt in data_types_collected):
            data_subject_rights.extend(["access", "rectification", "erasure"])
        
        if any("email" in dt.lower() or "contact" in dt.lower() for dt in data_types_collected):
            data_subject_rights.append("portability")
        
        # Check compliance status
        compliance_status = ComplianceStatus.COMPLIANT
        if not user_consent_required and any("personal" in dt.lower() for dt in data_types_collected):
            compliance_status = ComplianceStatus.REQUIRES_REVIEW
        
        if data_retention_period and data_retention_period > 365:
            compliance_status = ComplianceStatus.REQUIRES_REVIEW
        
        pia = PrivacyImpactAssessment(
            pia_id=pia_id,
            feature_name=feature_name,
            data_types_collected=data_types_collected,
            data_retention_period=data_retention_period,
            data_sharing=data_sharing or [],
            user_consent_required=user_consent_required,
            data_subject_rights=data_subject_rights,
            compliance_status=compliance_status
        )
        
        self._pias[pia_id] = pia
        
        await self.events.log_event(
            event_type="privacy_impact_assessment_conducted",
            user_id=None,
            properties={
                "pia_id": pia_id,
                "feature_name": feature_name,
                "data_types": data_types_collected,
                "compliance_status": compliance_status.value
            }
        )
        
        return pia
    
    async def validate_operational_pattern(
        self,
        pattern_name: str,
        pattern_metadata: Dict[str, Any],
        applicable_standards: List[ComplianceStandard]
    ) -> Dict[str, Any]:
        """
        Validate compliance and security for an operational pattern
        
        Args:
            pattern_name: Name of operational pattern
            pattern_metadata: Pattern metadata
            applicable_standards: Compliance standards to check
            
        Returns:
            Validation results
        """
        # Conduct compliance checks
        compliance_checks = await self.validate_segment_compliance(
            pattern_name,
            pattern_metadata,
            applicable_standards
        )
        
        # Conduct security assessment
        security_assessment = await self.assess_security(
            pattern_name,
            pattern_metadata
        )
        
        # Conduct PIA if personal data is involved
        pia = None
        if pattern_metadata.get("personal_data_involved", False):
            pia = await self.conduct_privacy_impact_assessment(
                pattern_name,
                pattern_metadata.get("data_types_collected", []),
                pattern_metadata.get("data_retention_period"),
                pattern_metadata.get("data_sharing"),
                pattern_metadata.get("user_consent_required", False)
            )
        
        # Overall validation status
        all_compliant = all(
            c.status == ComplianceStatus.COMPLIANT
            for c in compliance_checks.values()
        )
        
        security_ok = security_assessment.security_level in [SecurityLevel.LOW, SecurityLevel.MEDIUM]
        
        validation_passed = all_compliant and security_ok and (
            pia is None or pia.compliance_status == ComplianceStatus.COMPLIANT
        )
        
        return {
            "pattern_name": pattern_name,
            "validation_passed": validation_passed,
            "compliance_checks": {
                k: {
                    "status": v.status.value,
                    "findings": v.findings,
                    "recommendations": v.recommendations
                }
                for k, v in compliance_checks.items()
            },
            "security_assessment": {
                "security_level": security_assessment.security_level.value,
                "vulnerabilities": security_assessment.vulnerabilities,
                "mitigations": security_assessment.mitigations
            },
            "privacy_impact_assessment": {
                "pia_id": pia.pia_id,
                "compliance_status": pia.compliance_status.value,
                "data_subject_rights": pia.data_subject_rights
            } if pia else None,
            "recommendations": self._generate_validation_recommendations(
                compliance_checks,
                security_assessment,
                pia
            )
        }
    
    def _generate_validation_recommendations(
        self,
        compliance_checks: Dict[str, ComplianceCheck],
        security_assessment: SecurityAssessment,
        pia: Optional[PrivacyImpactAssessment]
    ) -> List[str]:
        """Generate overall validation recommendations"""
        recommendations = []
        
        # Compliance recommendations
        non_compliant = [
            k for k, v in compliance_checks.items()
            if v.status == ComplianceStatus.NON_COMPLIANT
        ]
        if non_compliant:
            recommendations.append(
                f"Address non-compliance with standards: {', '.join(non_compliant)}"
            )
        
        # Security recommendations
        if security_assessment.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            recommendations.append(
                f"Address security vulnerabilities: {len(security_assessment.vulnerabilities)} found"
            )
        
        # Privacy recommendations
        if pia and pia.compliance_status != ComplianceStatus.COMPLIANT:
            recommendations.append("Address privacy compliance concerns")
        
        return recommendations
    
    async def get_compliance_check(self, check_id: str) -> Optional[ComplianceCheck]:
        """Get compliance check by ID"""
        return self._checks.get(check_id)
    
    async def get_security_assessment(self, assessment_id: str) -> Optional[SecurityAssessment]:
        """Get security assessment by ID"""
        return self._assessments.get(assessment_id)
    
    async def get_pia(self, pia_id: str) -> Optional[PrivacyImpactAssessment]:
        """Get Privacy Impact Assessment by ID"""
        return self._pias.get(pia_id)
