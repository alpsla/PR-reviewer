"""Security metrics for code analysis."""
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class SecurityMetrics:
    """Security-related metrics"""
    vulnerabilities: List[Dict] = field(default_factory=list)
    unsafe_patterns: List[Dict] = field(default_factory=list)
    security_score: float = 100.0
    authentication_checks: bool = False
    input_validation: bool = False
    data_encryption: bool = False
