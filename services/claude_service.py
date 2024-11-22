import anthropic
from typing import Dict, List, Union, Any, Optional
import logging
import json
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from services.dependency_service import DependencyService
from services.code_structure_service import CodeStructureService
from services.language_detection_service import LanguageDetectionService
from plugins.documentation_parser import DocumentationParser

class ClaudeService:
    def __init__(self, api_key: str):
        """Initialize Claude service with proper error handling"""
        self.use_mock = True
        self.init_error = None
        self.client = None
        self.dependency_service = None
        self.code_structure_service = None
        self.language_detection_service = None
        self.doc_parser = None

        if not api_key:
            logger.warning("No Claude API key provided, falling back to mock service")
            self.init_error = "No API key provided"
            return
            
        try:
            # Initialize Claude client
            self.client = anthropic.Anthropic(
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com",
                    "X-API-Lang": "python",
                    "X-Client-Version": "1.0.0"
                }
            )
            
            # Initialize services
            self.dependency_service = DependencyService()
            self.code_structure_service = CodeStructureService()
            self.language_detection_service = LanguageDetectionService()
            
            # Initialize documentation parser
            self.doc_parser = DocumentationParser()
            self.doc_parser.initialize()
            
            self.use_mock = False
            logger.info("Claude API client and services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            self.use_mock = True
            self.init_error = str(e)
    
    def analyze_pr_sync(self, context: Dict) -> Dict:
        """Synchronous version of analyze_pr that handles documentation parsing"""
        if self.use_mock:
            logger.info("Using mock review service")
            mock_reason = getattr(self, 'init_error', 'APIUnavailable')
            return self.mock_review(context, mock_reason)
            
        try:
            # Add dependency, code structure, and documentation analysis
            if 'files' in context:
                # Parse documentation
                logger.info("Running documentation analysis")
                try:
                    doc_analysis = self.doc_parser.execute_sync({
                        'files': [{'filename': f['filename'], 'content': f.get('content', '')} for f in context['files']]
                    })
                    context['documentation_analysis'] = doc_analysis
                    logger.info("Documentation analysis completed successfully")
                except Exception as e:
                    logger.error(f"Documentation analysis failed: {str(e)}")
                    context['documentation_analysis'] = None

                # Perform language detection
                logger.info("Running language detection")
                try:
                    language_detection = self.language_detection_service.detect_from_files(context['files'])
                    context['language_detection'] = language_detection
                    logger.info(f"Language Determination: Primary language detected: {language_detection['primary']['name']}")
                except Exception as e:
                    logger.error(f"Language Determination: Failed to detect languages: {str(e)}")
                    context['language_detection'] = None
                
                logger.info("Running dependency analysis")
                if self.dependency_service:
                    dependency_analysis = self.dependency_service.analyze_dependencies(context['files'])
                    context['dependency_analysis'] = dependency_analysis
                
                logger.info("Running code structure analysis")
                structure_analysis = {}
                if self.code_structure_service:
                    for file in context['files']:
                        try:
                            analysis = self.code_structure_service.analyze_code(
                                file.get('content', ''),
                                file['filename']
                            )
                            if isinstance(analysis, dict):
                                structure_analysis[file['filename']] = analysis
                            else:
                                structure_analysis[file['filename']] = {
                                    'structures': getattr(analysis, 'structures', []),
                                    'imports': getattr(analysis, 'imports', []),
                                    'total_complexity': getattr(analysis, 'total_complexity', {})
                                }
                        except Exception as e:
                            logger.error(f"Error analyzing {file['filename']}: {str(e)}")
                context['structure_analysis'] = structure_analysis
            
            logger.info("Building analysis prompt")
            prompt = self._build_analysis_prompt(context)
            
            logger.info("Sending request to Claude API")
            if not self.client:
                raise ValueError("Claude API client not initialized")
                
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                system="You are a code review expert. Analyze pull requests thoroughly and provide constructive feedback focusing on code quality, security, and best practices."
            )
            
            logger.info("Successfully received response from Claude API")
            return self._parse_claude_response(response)
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {str(e)}")
            error_msg = f"API Error: {str(e)}"
            return self.mock_review(context, error_msg)
        except Exception as e:
            logger.error(f"Unexpected error during PR analysis: {str(e)}")
            error_msg = f"Unexpected error: {str(e)}"
            return self.mock_review(context, error_msg)
    
    def mock_review(self, context: Dict, mock_reason: str = "APIUnavailable") -> Dict:
        """Generate a detailed mock review response with error context"""
        logger.info(f"Generating mock review. Reason: {mock_reason}")
        
        files_count = context['pr_data']['changed_files']
        additions = context['pr_data']['additions']
        deletions = context['pr_data']['deletions']
        
        # Get code structure analysis metrics if available
        structure_analysis = context.get('structure_analysis', {})
        has_metrics = bool(structure_analysis)
        
        # Get language information from detection results
        language_detection = context.get('language_detection', {})
        primary_language = "Unknown"
        secondary_languages = []
        file_extensions = set()
        
        if language_detection and 'primary' in language_detection:
            primary_language = language_detection['primary']['name']
            secondary_languages = [lang['name'] for lang in language_detection.get('secondary', [])]
        elif 'files' in context:
            # Fallback to extension-based detection
            for file in context['files']:
                ext = file['filename'].split('.')[-1] if '.' in file['filename'] else ''
                if ext:
                    file_extensions.add(ext)
            if file_extensions:
                primary_language = max(file_extensions, key=list(file_extensions).count)

        mock_response = f"""<div class="review-section">
    <h3>Summary of Changes</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-file-earmark-text"></i> Files Modified: {files_count}</li>
                <li><i class="bi bi-plus-circle"></i> Lines Added: {additions}</li>
                <li><i class="bi bi-dash-circle"></i> Lines Removed: {deletions}</li>
                <li><i class="bi bi-code-square"></i> Primary Language: {primary_language}</li>
                {'<li><i class="bi bi-collection"></i> Other Languages: ' + ', '.join(secondary_languages) + '</li>' if secondary_languages else ''}
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Code Quality Analysis</h3>
    <div class="card mb-3">
        <div class="card-body">
            <h4>Best Practices</h4>
            <ul class="list-unstyled mb-3">
                <li><i class="bi bi-check-circle text-success"></i> Code follows standard formatting conventions</li>
                <li><i class="bi bi-exclamation-triangle text-warning"></i> Consider adding more documentation for complex logic</li>
                <li><i class="bi bi-check-circle text-success"></i> Variable naming is consistent</li>
                <li><i class="bi bi-exclamation-triangle text-warning"></i> File organization could be improved</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Dependencies and Architecture</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-diagram-2"></i> Module dependencies are well-structured</li>
                <li><i class="bi bi-exclamation-triangle text-warning"></i> Consider refactoring circular dependencies</li>
                <li><i class="bi bi-box-seam"></i> External dependencies are properly managed</li>
                <li><i class="bi bi-arrows-angle-contract"></i> Module coupling is reasonable</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Potential Issues</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-info-circle text-info"></i> No major issues identified</li>
                <li><i class="bi bi-exclamation-circle text-warning"></i> Consider adding error handling for edge cases</li>
                <li><i class="bi bi-exclamation-circle text-warning"></i> Unit tests could be expanded</li>
                <li><i class="bi bi-exclamation-circle text-warning"></i> Review error handling patterns</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Security Considerations</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-check-circle text-success"></i> No obvious security vulnerabilities</li>
                <li><i class="bi bi-shield-exclamation text-warning"></i> Consider adding input validation where applicable</li>
                <li><i class="bi bi-shield-exclamation text-warning"></i> Review authentication handling if present</li>
                <li><i class="bi bi-shield-exclamation text-warning"></i> Verify data sanitization practices</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Code Structure Analysis</h3>
    <div class="card mb-3">
        <div class="card-body">
            <h4>Complexity Metrics</h4>
            <ul class="list-unstyled mb-0">"""
        
        if has_metrics:
            for filename, analysis in structure_analysis.items():
                total = analysis.get('total_complexity', ComplexityMetrics())
                total_dict = {
                    'cyclomatic_complexity': total.cyclomatic_complexity,
                    'cognitive_complexity': total.cognitive_complexity,
                    'nesting_depth': total.nesting_depth,
                    'maintainability_index': total.maintainability_index
                }
                mock_response += f"""
                <li class="mb-3">
                    <strong>{filename}</strong>
                    <ul class="list-unstyled ps-3">
                        <li><i class="bi bi-graph-up"></i> Cyclomatic Complexity: {total_dict['cyclomatic_complexity']}</li>
                        <li><i class="bi bi-brain"></i> Cognitive Complexity: {total_dict['cognitive_complexity']}</li>
                        <li><i class="bi bi-diagram-2"></i> Nesting Depth: {total_dict['nesting_depth']}</li>
                        <li><i class="bi bi-speedometer2"></i> Maintainability Index: {total_dict['maintainability_index']:.1f}</li>
                    </ul>
                </li>"""
        else:
            mock_response += """
                <li><i class="bi bi-exclamation-circle text-warning"></i> Code structure analysis not available</li>"""
            
        mock_response += """
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Performance Implications</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-speedometer2"></i> Changes appear to have minimal performance impact</li>
                <li><i class="bi bi-lightning-charge"></i> Consider caching for repeated operations</li>
                <li><i class="bi bi-graph-up"></i> Monitor resource usage in production</li>
                <li><i class="bi bi-database-check"></i> Review database query optimization</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Suggested Improvements</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-pencil"></i> Add more inline documentation</li>
                <li><i class="bi bi-diagram-2"></i> Consider breaking down complex functions</li>
                <li><i class="bi bi-exclamation-diamond"></i> Add comprehensive error handling</li>
                <li><i class="bi bi-journal-text"></i> Implement logging for better debugging</li>
            </ul>
        </div>
    </div>
</div>

<div class="alert alert-warning mt-3">
    <i class="bi bi-info-circle me-2"></i> Note: This is a mock review generated for testing purposes. 
    <br>Reason: {mock_reason}
</div>"""

        return {
            'summary': mock_response,
            'structured': True,
            'is_mock': True,
            'mock_reason': mock_reason
        }
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Builds a comprehensive analysis prompt for Claude"""
        pr_data = context['pr_data']
        files = context.get('files', [])
        comments = context.get('comments', [])
        dependency_analysis = context.get('dependency_analysis', {})
        documentation_analysis = context.get('documentation_analysis', {})

        prompt = f"""PR Details:
Title: {pr_data['title']}
Description: {pr_data['body'] or 'No description provided'}

Changes Overview:
- Files changed: {pr_data['changed_files']}
- Additions: {pr_data['additions']}
- Deletions: {pr_data['deletions']}

Modified Files:
{self._format_files(files)}

Discussion Context:
{self._format_comments(comments)}

Dependency Analysis:
Documentation Analysis:
{self._format_documentation_analysis(documentation_analysis)}

{self._format_dependency_analysis(dependency_analysis)}

Structure your response using HTML with Bootstrap classes:
1. Use .review-section for main sections
2. Wrap content in .card and .card-body
3. Use <ul class="list-unstyled mb-0"> for lists
4. Place icons before text content in list items:
   <li><i class="bi bi-[icon-name] [text-color]"></i> Content</li>
5. Use these icons consistently:
   - bi-check-circle text-success (for good practices)
   - bi-exclamation-triangle text-warning (for warnings)
   - bi-exclamation-circle (for issues)
   - bi-shield-exclamation (for security warnings)
   - bi-speedometer2 (for performance metrics)
6. Organize content into sections:
   - Code Quality and Best Practices
   - Dependencies and Architecture
   - Potential Issues
    - Security Considerations
   - Performance Implications
   - Suggested Improvements"""

    def _build_analysis_prompt(self, context: Dict) -> str:
        """Build analysis prompt with PR context"""
        prompt = """Please provide a thorough code review for this pull request. Focus on:
- Code Quality and Best Practices
- Dependencies and Architecture
- Potential Issues
- Security Considerations
- Performance Implications
- Suggested Improvements"""

        # Add PR data section
        if 'pr_data' in context:
            prompt += "\n\nPR Details:\n" + str(context['pr_data'])

        # Add files section
        if 'files' in context:
            prompt += "\n\n" + self._format_files(context['files'])

        # Add comments section
        if 'comments' in context:
            prompt += "\n\n" + self._format_comments(context['comments'])

        # Add language detection results
        if context.get('language_detection'):
            prompt += "\n\nLanguage Detection:\n"
            prompt += f"Primary: {context['language_detection']['primary']['name']}\n"
            if context['language_detection'].get('secondary'):
                prompt += "Secondary Languages:\n"
                for lang in context['language_detection']['secondary']:
                    prompt += f"- {lang['name']} ({lang['percentage']}%)\n"

        # Add dependency analysis
        if context.get('dependency_analysis'):
            prompt += "\n\n" + self._format_dependency_analysis(context['dependency_analysis'])

        # Add documentation analysis
        if context.get('documentation_analysis'):
            prompt += "\n\n" + self._format_documentation_analysis(context['documentation_analysis'])

        return prompt
    def _format_files(self, files: List[Dict]) -> str:
        """Format files list for prompt"""
        if not files:
            return "No files were modified"
            
        formatted = "Modified Files:\n"
        for file in files:
            formatted += f"\n{file['filename']}:\n"
            formatted += f"- Status: {file['status']}\n"
            formatted += f"- Changes: +{file['additions']}, -{file['deletions']}\n"
            if file.get('patch'):
                formatted += f"- Diff:\n```\n{file['patch']}\n```\n"
        return formatted

    def _format_comments(self, comments: List[Dict]) -> str:
        """Format PR comments for prompt"""
        if not comments:
            return "No comments found"
            
        formatted = "Discussion Context:\n"
        for comment in comments[:5]:  # Limit to 5 most recent comments
            formatted += f"\n{comment['user']} wrote:\n{comment['body']}\n"
        return formatted

    def _format_dependency_analysis(self, analysis: Dict) -> str:
        """Format dependency analysis results"""
        if not analysis or analysis.get('error'):
            return "Dependency analysis not available"
            
        circular_deps = analysis.get('circular_dependencies', [])
        external_deps = analysis.get('external_dependencies', [])
        
        formatted = "Dependency Analysis Results:\n"
        
        if circular_deps:
            formatted += "\nCircular Dependencies Found:\n"
            for cycle in circular_deps:
                formatted += f"- {' -> '.join(cycle)}\n"
        else:
            formatted += "\nNo circular dependencies found.\n"
        
        if external_deps:
            formatted += "\nExternal Dependencies:\n"
            for dep in external_deps:
                formatted += f"- {dep}\n"
        else:
            formatted += "\nNo external dependencies found.\n"
        return formatted

    def _format_documentation_analysis(self, analysis: Dict) -> str:
        """Format documentation analysis results"""
        if not analysis or not isinstance(analysis, dict):
            return "Documentation analysis not available"
            
        documentation = analysis.get('documentation', {})
        stats = analysis.get('stats', {})
        
        formatted = "Documentation Analysis Results:\n"
        
        if stats:
            formatted += f"\nOverall Statistics:\n"
            formatted += f"- Total Files: {stats.get('total_files_analyzed', 0)}\n"
            formatted += f"- Average Coverage: {stats.get('average_coverage', 0)}%\n"
            formatted += f"- Average Quality: {stats.get('average_quality', 0)}%\n"
            formatted += f"- Well Documented Files: {stats.get('well_documented_files', 0)}\n"
            formatted += f"- Need Improvement: {stats.get('needs_improvement', 0)}\n"
            
        if documentation:
            formatted += "\nPer-file Documentation:\n"
            for filename, doc_info in documentation.items():
                if isinstance(doc_info, dict) and 'error' not in doc_info:
                    formatted += f"\n{filename}:\n"
                    formatted += f"- Coverage: {doc_info.get('coverage', 0)}%\n"
                    formatted += f"- Quality Score: {doc_info.get('quality_score', 0)}%\n"
                    
                    # Add class documentation info
                    if doc_info.get('classes'):
                        formatted += "- Documented Classes:\n"
                        for class_name, class_info in doc_info['classes'].items():
                            formatted += f"  • {class_name}: {'Documented' if class_info.get('docstring') else 'Undocumented'}\n"
                    
                    # Add function documentation info
                    if doc_info.get('functions'):
                        formatted += "- Documented Functions:\n"
                        for func_name, func_info in doc_info['functions'].items():
                            formatted += f"  • {func_name}: {'Documented' if func_info.get('docstring') else 'Undocumented'}\n"
                            
        return formatted
        
    def analyze_pr_sync(self, context: Dict) -> Dict:
        """Synchronous version of analyze_pr method.
        
        Args:
            context: Dictionary containing PR analysis context
            
        Returns:
            Dictionary containing the analysis results
            
        Raises:
            Exception: If analysis fails
        """
        if self.use_mock:
            logger.info("Using mock review service")
            mock_reason = getattr(self, 'init_error', 'APIUnavailable')
            return self.mock_review(context, mock_reason)
            
        try:
            # Add dependency, code structure, and documentation analysis
            if 'files' in context:
                # Parse documentation
                logger.info("Running documentation analysis")
                try:
                    doc_analysis = self.doc_parser.execute_sync({
                        'files': [{'filename': f['filename'], 'content': f.get('content', '')} for f in context['files']]
                    })
                    context['documentation_analysis'] = doc_analysis
                    logger.info("Documentation analysis completed successfully")
                except Exception as e:
                    logger.error(f"Documentation analysis failed: {str(e)}")
                    context['documentation_analysis'] = None

                # Perform language detection
                logger.info("Running language detection")
                try:
                    language_detection = self.language_detection_service.detect_from_files(context['files'])
                    context['language_detection'] = language_detection
                    logger.info(f"Language Determination: Primary language detected: {language_detection['primary']['name']}")
                except Exception as e:
                    logger.error(f"Language Determination: Failed to detect languages: {str(e)}")
                    context['language_detection'] = None
                
                # Run dependency analysis if available
                if self.dependency_service:
                    logger.info("Running dependency analysis")
                    dependency_analysis = self.dependency_service.analyze_dependencies(context['files'])
                    context['dependency_analysis'] = dependency_analysis
                
                # Run code structure analysis if available
                if self.code_structure_service:
                    logger.info("Running code structure analysis")
                    structure_analysis = {}
                    for file in context['files']:
                        try:
                            analysis = self.code_structure_service.analyze_code(
                                file.get('content', ''),
                                file['filename']
                            )
                            if isinstance(analysis, dict):
                                structure_analysis[file['filename']] = analysis
                            else:
                                structure_analysis[file['filename']] = {
                                    'structures': getattr(analysis, 'structures', []),
                                    'imports': getattr(analysis, 'imports', []),
                                    'total_complexity': getattr(analysis, 'total_complexity', {})
                                }
                        except Exception as e:
                            logger.error(f"Error analyzing {file['filename']}: {str(e)}")
                    context['structure_analysis'] = structure_analysis
            
            logger.info("Building analysis prompt")
            prompt = self._build_analysis_prompt(context)
            
            logger.info("Sending request to Claude API")
            if not self.client:
                raise ValueError("Claude API client not initialized")
                
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                system="You are a code review expert. Analyze pull requests thoroughly and provide constructive feedback focusing on code quality, security, and best practices."
            )
            
            logger.info("Successfully received response from Claude API")
            return self._parse_claude_response(response)
            
        except Exception as e:
            logger.error(f"Error during PR analysis: {str(e)}")
            error_msg = f"Analysis error: {str(e)}"
            return self.mock_review(context, error_msg)
                    
    
    def _parse_claude_response(self, response: Any) -> Dict:
        """Parses Claude's response with enhanced validation and error handling"""
        try:
            if not response:
                logger.error("Empty response received from Claude")
                raise ValueError("Empty response from Claude")
            
            # Extract content from response based on Anthropic SDK v0.3+
            if hasattr(response, 'content') and isinstance(response.content, (list, str)):
                if isinstance(response.content, list) and len(response.content) > 0:
                    content = response.content[0].text
                else:
                    content = str(response.content)
            else:
                # Fallback for other response structures
                content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            # Clean up response content
            content = re.sub(r"^Here's the code review feedback.*?:\s*", "", content, flags=re.IGNORECASE).strip()
            content = re.sub(r'```html\s*|\s*```$', '', content, flags=re.IGNORECASE).strip()
            
            # Ensure proper HTML structure
            if not ('<div' in content and '</div>' in content):
                logger.warning("Adding HTML structure to response")
                content = f'''
                <div class="code-review">
                    <div class="review-section">
                        {content}
                    </div>
                </div>
                '''
            
            # Basic HTML validation
            if not content.strip():
                raise ValueError("Empty content after parsing")
                
            # Log successful parsing
            logger.info("Successfully parsed Claude response")
            
            return {
                'summary': content,
                'structured': True,
                'is_mock': False,
                'format': 'html'
            }
            
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to parse Claude response structure: {str(e)}")
            # Return unstructured text as fallback
            return {
                'summary': str(response),
                'structured': False,
                'is_mock': False,
                'format': 'text',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing Claude response: {str(e)}")
            return {
                'summary': "Failed to parse review response. Please try again.",
                'structured': False,
                'is_mock': True,
                'format': 'text',
                'error': str(e)
            }