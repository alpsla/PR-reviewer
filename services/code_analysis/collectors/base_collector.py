from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CollectorConfig:
    """Base configuration for collectors."""
    include_patterns: list[str] = None
    exclude_patterns: list[str] = None
    max_files: int = 1000
    timeout: int = 300
    detail_level: str = "normal"  # "minimal", "normal", "detailed"

@dataclass
class CollectorContext:
    """Context information for collection process."""
    repository_url: str
    base_branch: str
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    diff_only: bool = False

class BaseCollector(ABC):
    """Base class for all data collectors."""
    
    def __init__(self, config: CollectorConfig = CollectorConfig()):
        self.config = config
    
    @abstractmethod
    async def collect(self, context: CollectorContext) -> Dict[str, Any]:
        """Collect data based on the given context."""
        pass
    
    @abstractmethod
    async def collect_diff(self, context: CollectorContext) -> Dict[str, Any]:
        """Collect data for changes only."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """Get numerical metrics from the collected data."""
        pass
    
    @abstractmethod
    def get_recommendations(self) -> list[Dict[str, Any]]:
        """Get recommendations based on the collected data."""
        pass
    
    @abstractmethod
    def get_quality_score(self) -> float:
        """Calculate overall quality score."""
        pass
