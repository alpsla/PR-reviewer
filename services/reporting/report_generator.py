from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass
import json
import markdown
from jinja2 import Environment, FileSystemLoader
import os

@dataclass
class ReportConfig:
    """Configuration for report generation."""
    include_charts: bool = True
    include_code_examples: bool = True
    theme: str = "light"
    max_code_examples: int = 5
    chart_style: str = "modern"

class TypeScriptReportGenerator:
    """Generates comprehensive TypeScript analysis reports."""
    
    def __init__(self, config: ReportConfig = ReportConfig()):
        self.config = config
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate_project_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a full project analysis report."""
        template = self.env.get_template('project_report.html.j2')
        
        # Generate charts
        charts = self._generate_charts(analysis_results) if self.config.include_charts else {}
        
        # Generate code examples
        code_examples = self._generate_code_examples(analysis_results) if self.config.include_code_examples else []
        
        # Prepare report data
        report_data = {
            'summary': analysis_results.get('summary', {}),
            'type_analysis': analysis_results.get('type_analysis', {}),
            'documentation_analysis': analysis_results.get('documentation_analysis', {}),
            'framework_analysis': analysis_results.get('framework_analysis', {}),
            'charts': charts,
            'code_examples': code_examples,
            'theme': self.config.theme
        }
        
        return template.render(**report_data)

    def generate_pr_report(self, pr_analysis: Dict[str, Any], base_analysis: Dict[str, Any]) -> str:
        """Generate a pull request analysis report comparing against base branch."""
        template = self.env.get_template('pr_report.html.j2')
        
        # Generate differential analysis
        diff_analysis = self._generate_diff_analysis(pr_analysis, base_analysis)
        
        # Generate comparison charts
        charts = self._generate_comparison_charts(pr_analysis, base_analysis) if self.config.include_charts else {}
        
        # Generate code examples focusing on changes
        code_examples = self._generate_pr_code_examples(pr_analysis) if self.config.include_code_examples else []
        
        report_data = {
            'diff_analysis': diff_analysis,
            'charts': charts,
            'code_examples': code_examples,
            'summary': pr_analysis.get('summary', {}),
            'theme': self.config.theme
        }
        
        return template.render(**report_data)

    def _generate_charts(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts for the analysis results."""
        charts = {}
        
        # Type Coverage Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=analysis_results.get('type_analysis', {}).get('coverage', 0) * 100,
            title={'text': "Type Coverage"},
            gauge={'axis': {'range': [0, 100]}}
        ))
        charts['type_coverage'] = fig.to_html(full_html=False)
        
        # Documentation Coverage
        doc_metrics = analysis_results.get('documentation_analysis', {}).get('metrics', {})
        fig = px.bar(
            x=['Functions', 'Classes', 'Interfaces'],
            y=[
                doc_metrics.get('documented_functions', 0) / max(doc_metrics.get('total_functions', 1), 1) * 100,
                doc_metrics.get('documented_classes', 0) / max(doc_metrics.get('total_classes', 1), 1) * 100,
                doc_metrics.get('documented_interfaces', 0) / max(doc_metrics.get('total_interfaces', 1), 1) * 100
            ],
            title="Documentation Coverage"
        )
        charts['doc_coverage'] = fig.to_html(full_html=False)
        
        # Type Usage Distribution
        type_metrics = analysis_results.get('type_analysis', {}).get('metrics', {})
        fig = px.pie(
            values=[
                type_metrics.get('interfaces', 0),
                type_metrics.get('type_aliases', 0),
                type_metrics.get('generics', 0),
                type_metrics.get('utility_types', 0)
            ],
            names=['Interfaces', 'Type Aliases', 'Generics', 'Utility Types'],
            title="Type Usage Distribution"
        )
        charts['type_distribution'] = fig.to_html(full_html=False)
        
        return charts

    def _generate_comparison_charts(self, pr_analysis: Dict[str, Any], base_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate comparison charts between PR and base branch."""
        charts = {}
        
        # Type Coverage Comparison
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Base Branch",
            x=["Type Coverage"],
            y=[base_analysis.get('type_analysis', {}).get('coverage', 0) * 100]
        ))
        fig.add_trace(go.Bar(
            name="PR Branch",
            x=["Type Coverage"],
            y=[pr_analysis.get('type_analysis', {}).get('coverage', 0) * 100]
        ))
        charts['type_coverage_comparison'] = fig.to_html(full_html=False)
        
        # Documentation Changes
        fig = go.Figure()
        base_docs = base_analysis.get('documentation_analysis', {}).get('metrics', {})
        pr_docs = pr_analysis.get('documentation_analysis', {}).get('metrics', {})
        
        categories = ['Functions', 'Classes', 'Interfaces']
        base_values = [
            base_docs.get('documented_functions', 0),
            base_docs.get('documented_classes', 0),
            base_docs.get('documented_interfaces', 0)
        ]
        pr_values = [
            pr_docs.get('documented_functions', 0),
            pr_docs.get('documented_classes', 0),
            pr_docs.get('documented_interfaces', 0)
        ]
        
        fig.add_trace(go.Bar(name="Base Branch", x=categories, y=base_values))
        fig.add_trace(go.Bar(name="PR Branch", x=categories, y=pr_values))
        charts['documentation_changes'] = fig.to_html(full_html=False)
        
        return charts

    def _generate_code_examples(self, analysis_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate code examples from analysis results."""
        examples = []
        
        # Get type-related examples
        type_examples = analysis_results.get('type_analysis', {}).get('examples', [])
        for example in type_examples[:self.config.max_code_examples]:
            examples.append({
                'title': 'Type Usage Example',
                'code': example.get('code', ''),
                'explanation': example.get('explanation', '')
            })
        
        # Get documentation examples
        doc_examples = analysis_results.get('documentation_analysis', {}).get('examples', [])
        for example in doc_examples[:self.config.max_code_examples]:
            examples.append({
                'title': 'Documentation Example',
                'code': example.get('code', ''),
                'explanation': example.get('explanation', '')
            })
        
        return examples

    def _generate_pr_code_examples(self, pr_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate code examples specific to PR changes."""
        examples = []
        
        # Focus on changed files and their analysis
        file_analysis = pr_analysis.get('file_analysis', {})
        for file_path, analysis in file_analysis.items():
            if analysis.get('changes', []):
                examples.append({
                    'title': f'Changes in {file_path}',
                    'code': analysis.get('changes', [])[0].get('code', ''),
                    'explanation': analysis.get('changes', [])[0].get('explanation', '')
                })
                
                if len(examples) >= self.config.max_code_examples:
                    break
        
        return examples

    def _generate_diff_analysis(self, pr_analysis: Dict[str, Any], base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate differential analysis between PR and base branch."""
        return {
            'type_coverage_change': (
                pr_analysis.get('type_analysis', {}).get('coverage', 0) -
                base_analysis.get('type_analysis', {}).get('coverage', 0)
            ) * 100,
            'doc_coverage_change': (
                pr_analysis.get('documentation_analysis', {}).get('metrics', {}).get('coverage', 0) -
                base_analysis.get('documentation_analysis', {}).get('metrics', {}).get('coverage', 0)
            ) * 100,
            'quality_score_change': (
                pr_analysis.get('summary', {}).get('quality_score', 0) -
                base_analysis.get('summary', {}).get('quality_score', 0)
            ),
            'new_issues': len(pr_analysis.get('summary', {}).get('action_items', [])),
            'resolved_issues': self._count_resolved_issues(pr_analysis, base_analysis)
        }

    def _count_resolved_issues(self, pr_analysis: Dict[str, Any], base_analysis: Dict[str, Any]) -> int:
        """Count number of issues resolved in PR compared to base branch."""
        base_issues = set(
            issue['id'] 
            for issue in base_analysis.get('summary', {}).get('action_items', [])
        )
        pr_issues = set(
            issue['id'] 
            for issue in pr_analysis.get('summary', {}).get('action_items', [])
        )
        return len(base_issues - pr_issues)
