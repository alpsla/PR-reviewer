"""Complexity metrics for code analysis."""
from dataclasses import dataclass

@dataclass
class ComplexityMetrics:
    """Complexity metrics for code analysis"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    maintainability_index: float = 100.0

    def update(self, other: 'ComplexityMetrics') -> None:
        """Update metrics from another ComplexityMetrics object"""
        self.cyclomatic_complexity += other.cyclomatic_complexity
        self.cognitive_complexity += other.cognitive_complexity
        self.nesting_depth = max(self.nesting_depth, other.nesting_depth)
        self.maintainability_index = (self.maintainability_index + other.maintainability_index) / 2
