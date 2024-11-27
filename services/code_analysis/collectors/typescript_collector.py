from typing import Dict, Any, List, Optional
from .base_collector import BaseCollector, CollectorConfig, CollectorContext
from ..analyzers.typescript_analyzer import TypeScriptAnalyzer
from ...reporting.report_generator import TypeScriptReportGenerator, ReportConfig
import asyncio
import os
from dataclasses import dataclass
from enum import Enum
import tempfile
import shutil
from pathlib import Path

class MetricWeight(Enum):
    """Weights for different metrics in quality score calculation."""
    TYPE_COVERAGE = 0.3
    DOCUMENTATION = 0.2
    COMPLEXITY = 0.15
    BEST_PRACTICES = 0.15
    FRAMEWORK_USAGE = 0.1
    ERROR_HANDLING = 0.1

@dataclass
class TypeScriptCollectorConfig(CollectorConfig):
    """Configuration specific to TypeScript collection."""
    min_type_coverage: float = 0.8
    min_doc_coverage: float = 0.7
    max_complexity: int = 15
    framework_check: bool = True
    error_check: bool = True
    generate_examples: bool = True
    temp_dir: Optional[str] = None  # Directory to store downloaded files

class TypeScriptCollector(BaseCollector):
    """Collector for TypeScript code analysis."""
    
    def __init__(self, config: TypeScriptCollectorConfig = TypeScriptCollectorConfig()):
        super().__init__(config)
        self.analyzer = TypeScriptAnalyzer()
        self.report_generator = TypeScriptReportGenerator()
        self.last_analysis = None
        self.diff_analysis = None
        self._temp_dir = None
    
    async def collect(self, context: CollectorContext) -> Dict[str, Any]:
        """Collect TypeScript analysis data."""
        try:
            # Create temp directory if not specified
            if not self.config.temp_dir:
                self._temp_dir = tempfile.mkdtemp(prefix='ts_analysis_')
            else:
                self._temp_dir = self.config.temp_dir
                os.makedirs(self._temp_dir, exist_ok=True)
            
            # Download repository files
            repo_dir = await self._download_repository(
                context.repository_url,
                context.base_branch,
                self._temp_dir
            )
            
            # Analyze repository
            analysis_results = await asyncio.to_thread(
                self.analyzer.analyze_directory,
                repo_dir
            )
            
            self.last_analysis = analysis_results
            
            # Generate report
            if context.diff_only and context.pr_number:
                return await self.collect_diff(context)
            
            result = {
                'analysis': analysis_results,
                'metrics': self.get_metrics(),
                'recommendations': self.get_recommendations(),
                'quality_score': self.get_quality_score(),
                'report': self.report_generator.generate_project_report(analysis_results)
            }
            
            # Clean up if using temp directory
            if not self.config.temp_dir and self._temp_dir:
                shutil.rmtree(self._temp_dir)
            
            return result
            
        except Exception as e:
            # Clean up on error if using temp directory
            if not self.config.temp_dir and self._temp_dir:
                shutil.rmtree(self._temp_dir)
            raise Exception(f"Error collecting TypeScript data: {str(e)}")
    
    async def collect_diff(self, context: CollectorContext) -> Dict[str, Any]:
        """Collect analysis data for changes only."""
        try:
            if not self.last_analysis:
                await self.collect(context)
            
            # Create PR branch directory
            pr_dir = os.path.join(self._temp_dir, f'pr_{context.pr_number}')
            os.makedirs(pr_dir, exist_ok=True)
            
            # Download PR files
            pr_repo_dir = await self._download_repository(
                context.repository_url,
                f"pull/{context.pr_number}/head",
                pr_dir
            )
            
            # Analyze PR branch
            pr_analysis = await asyncio.to_thread(
                self.analyzer.analyze_directory,
                pr_repo_dir
            )
            
            self.diff_analysis = pr_analysis
            
            result = {
                'analysis': pr_analysis,
                'base_analysis': self.last_analysis,
                'metrics': self.get_metrics(),
                'recommendations': self.get_recommendations(),
                'quality_score': self.get_quality_score(),
                'report': self.report_generator.generate_pr_report(pr_analysis, self.last_analysis)
            }
            
            # Clean up if using temp directory
            if not self.config.temp_dir and self._temp_dir:
                shutil.rmtree(self._temp_dir)
            
            return result
            
        except Exception as e:
            # Clean up on error if using temp directory
            if not self.config.temp_dir and self._temp_dir:
                shutil.rmtree(self._temp_dir)
            raise Exception(f"Error collecting PR diff data: {str(e)}")
    
    async def _download_repository(self, repo_url: str, branch: str, target_dir: str) -> str:
        """Download repository files to local directory."""
        try:
            # Create unique subdirectory for this branch
            branch_dir = os.path.join(target_dir, branch.replace('/', '_'))
            os.makedirs(branch_dir, exist_ok=True)
            
            # Download files using GitHub API
            # TODO: Implement actual file download logic here
            # For now, just return the directory
            return branch_dir
            
        except Exception as e:
            raise Exception(f"Error downloading repository: {str(e)}")
    
    def get_metrics(self) -> Dict[str, float]:
        """Get numerical metrics from the analysis."""
        if not self.last_analysis:
            return {}
        
        analysis = self.diff_analysis if self.diff_analysis else self.last_analysis
        
        return {
            'type_coverage': analysis['type_analysis']['coverage'],
            'documentation_coverage': analysis['documentation_analysis']['metrics']['coverage'],
            'complexity_score': analysis['summary']['complexity_score'],
            'framework_score': analysis['framework_analysis']['metrics']['framework_score'],
            'error_handling_score': analysis['summary']['error_handling_score'],
            'best_practices_score': analysis['summary']['best_practices_score']
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations based on the analysis."""
        if not self.last_analysis:
            return []
        
        analysis = self.diff_analysis if self.diff_analysis else self.last_analysis
        recommendations = []
        
        # Add type-related recommendations
        if analysis['type_analysis']['coverage'] < self.config.min_type_coverage:
            recommendations.append({
                'category': 'type_safety',
                'priority': 'high',
                'title': 'Improve Type Coverage',
                'description': f"Current type coverage ({analysis['type_analysis']['coverage']*100:.1f}%) is below the minimum threshold ({self.config.min_type_coverage*100}%)",
                'suggestions': analysis['type_analysis']['suggestions']
            })
        
        # Add documentation recommendations
        if analysis['documentation_analysis']['metrics']['coverage'] < self.config.min_doc_coverage:
            recommendations.append({
                'category': 'documentation',
                'priority': 'medium',
                'title': 'Improve Documentation Coverage',
                'description': f"Current documentation coverage ({analysis['documentation_analysis']['metrics']['coverage']*100:.1f}%) is below the minimum threshold ({self.config.min_doc_coverage*100}%)",
                'suggestions': analysis['documentation_analysis']['suggestions']
            })
        
        # Add framework-specific recommendations
        if self.config.framework_check and analysis['framework_analysis']['suggestions']:
            recommendations.append({
                'category': 'framework',
                'priority': 'medium',
                'title': 'Framework Best Practices',
                'description': 'Consider implementing these framework-specific improvements',
                'suggestions': analysis['framework_analysis']['suggestions']
            })
        
        return recommendations
    
    def get_quality_score(self) -> float:
        """Calculate overall quality score."""
        if not self.last_analysis:
            return 0.0
        
        analysis = self.diff_analysis if self.diff_analysis else self.last_analysis
        metrics = self.get_metrics()
        
        score = 0.0
        score += metrics['type_coverage'] * MetricWeight.TYPE_COVERAGE.value
        score += metrics['documentation_coverage'] * MetricWeight.DOCUMENTATION.value
        score += metrics['complexity_score'] * MetricWeight.COMPLEXITY.value
        score += metrics['best_practices_score'] * MetricWeight.BEST_PRACTICES.value
        score += metrics['framework_score'] * MetricWeight.FRAMEWORK_USAGE.value
        score += metrics['error_handling_score'] * MetricWeight.ERROR_HANDLING.value
        
        return min(max(score, 0.0), 1.0) * 100  # Convert to percentage
