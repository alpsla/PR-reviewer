"""Performance metrics for code analysis."""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PerformanceMetrics:
    """Performance-related metrics"""
    memory_usage: Optional[float] = None
    time_complexity: str = "O(1)"
    space_complexity: str = "O(1)"
    async_operations: bool = False
    caching_used: bool = False
    resource_leaks: List[str] = field(default_factory=list)
