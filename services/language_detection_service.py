from typing import Dict, List, Optional, TypedDict
import logging
import re
from urllib.parse import urlparse
import requests
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LanguageInfo(TypedDict):
    """Language information with confidence scoring"""
    name: str
    confidence: float
    bytes: int
    type: str  # 'programming', 'markup', 'data', etc.

class RepositoryLanguages(TypedDict):
    """Repository language information"""
    primary: LanguageInfo
    secondary: List[LanguageInfo]
    total_bytes: int
    detection_source: str  # 'github' or 'content'

class FileContent(TypedDict):
    """File content information"""
    filename: str
    content: str
    size: int

class LanguageTools:
    """Common language detection tools and utilities"""
    
    # Language extension mappings based on GitHub's linguist
    EXTENSION_MAP = {
        'py': {'name': 'Python', 'type': 'programming'},
        'js': {'name': 'JavaScript', 'type': 'programming'},
        'ts': {'name': 'TypeScript', 'type': 'programming'},
        'jsx': {'name': 'JavaScript', 'type': 'programming'},
        'tsx': {'name': 'TypeScript', 'type': 'programming'},
        'java': {'name': 'Java', 'type': 'programming'},
        'rb': {'name': 'Ruby', 'type': 'programming'},
        'go': {'name': 'Go', 'type': 'programming'},
        'rs': {'name': 'Rust', 'type': 'programming'},
        'php': {'name': 'PHP', 'type': 'programming'},
        'cs': {'name': 'C#', 'type': 'programming'},
        'cpp': {'name': 'C++', 'type': 'programming'},
        'c': {'name': 'C', 'type': 'programming'},
        'html': {'name': 'HTML', 'type': 'markup'},
        'css': {'name': 'CSS', 'type': 'markup'},
        'md': {'name': 'Markdown', 'type': 'markup'},
        'json': {'name': 'JSON', 'type': 'data'},
        'yml': {'name': 'YAML', 'type': 'data'},
        'yaml': {'name': 'YAML', 'type': 'data'},
        'xml': {'name': 'XML', 'type': 'markup'},
    }

    @staticmethod
    def get_language_from_extension(extension: str) -> Optional[Dict[str, str]]:
        """Get language information from file extension"""
        return LanguageTools.EXTENSION_MAP.get(extension.lower().lstrip('.'))

    @staticmethod
    def calculate_confidence(content: str, language_info: Dict[str, str]) -> float:
        """Calculate confidence score based on file content and language"""
        logger.debug(f"Calculating confidence score for {language_info['name']}")
        confidence = 0.7  # Base confidence from extension
        logger.debug(f"Base confidence from extension: {confidence}")

        # Language-specific patterns
        patterns = {
            'Python': (r'import\s+|from\s+\w+\s+import|def\s+\w+\s*\(|class\s+\w+:', 0.2),
            'JavaScript': (r'const\s+|let\s+|function\s+\w+\s*\(|import\s+.*from|export\s+', 0.2),
            'TypeScript': (r'interface\s+|type\s+|class\s+\w+\s*{|implements\s+|extends\s+', 0.2),
            'Java': (r'public\s+class|private\s+|protected\s+|package\s+|import\s+java\.', 0.2),
            'HTML': (r'<!DOCTYPE\s+html|<html|<head|<body|<div|<span|<p>', 0.2),
            'CSS': (r'@media|{[\s\w\-:;]+}|\s*[\w\-]+\s*:{1}|@import\s+', 0.2),
        }

        if language_info['name'] in patterns:
            pattern, boost = patterns[language_info['name']]
            if re.search(pattern, content, re.IGNORECASE):
                confidence += boost
                logger.debug(f"Found {language_info['name']} patterns in content, boosting confidence by {boost}")

        return min(confidence, 1.0)

class LanguageDetectionService:
    """Service for detecting programming languages in repositories and files"""

    def __init__(self, github_token: Optional[str] = None):
        """Initialize the language detection service"""
        self.github_token = github_token
        self._cache = {}
        self.current_detection: Optional[RepositoryLanguages] = None

    @lru_cache(maxsize=100)
    async def detectFromGitHub(self, pr_url: str) -> RepositoryLanguages:
        """Detect languages from a GitHub PR URL"""
        try:
            logger.info(f"Starting GitHub language detection for PR: {pr_url}")
            
            # Parse PR URL to get owner and repo
            parsed = urlparse(pr_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 4:
                raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

            owner, repo = path_parts[0:2]
            logger.info(f"Analyzing repository: {owner}/{repo}")
            
            # Call GitHub API
            headers = {'Authorization': f'token {self.github_token}'} if self.github_token else {}
            response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/languages',
                headers=headers
            )
            response.raise_for_status()
            
            # Process GitHub response
            languages_data = response.json()
            total_bytes = sum(languages_data.values())
            logger.info(f"Found {len(languages_data)} languages in repository, total size: {total_bytes} bytes")
            
            # Sort languages by bytes
            sorted_languages = sorted(
                [(name, bytes) for name, bytes in languages_data.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            for lang, bytes in sorted_languages:
                percentage = (bytes / total_bytes) * 100
                logger.info(f"Language detected: {lang} ({bytes} bytes, {percentage:.1f}% of codebase)")
            
            if not sorted_languages:
                raise ValueError("No languages detected in repository")
            
            # Create RepositoryLanguages object
            primary_lang = sorted_languages[0]
            self.current_detection = {
                'primary': {
                    'name': primary_lang[0],
                    'confidence': 0.9,  # High confidence for GitHub API data
                    'bytes': primary_lang[1],
                    'type': 'programming'  # Default to programming
                },
                'secondary': [
                    {
                        'name': lang[0],
                        'confidence': 0.9,
                        'bytes': lang[1],
                        'type': 'programming'
                    }
                    for lang in sorted_languages[1:]
                ],
                'total_bytes': total_bytes,
                'detection_source': 'github'
            }
            
            return self.current_detection
            
        except requests.RequestException as e:
            logger.error(f"GitHub API error: {str(e)}")
            raise RuntimeError(f"Failed to fetch language data from GitHub: {str(e)}")
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            raise RuntimeError(f"Language detection failed: {str(e)}")

    async def detectFromContent(self, files: List[FileContent]) -> RepositoryLanguages:
        """Detect languages from file contents"""
        try:
            logger.info(f"Starting content-based language detection for {len(files)} files")
            language_stats: Dict[str, Dict] = {}
            total_bytes = 0
            
            for file in files:
                logger.info(f"Processing file: {file['filename']}")
                # Get file extension
                extension = file['filename'].split('.')[-1] if '.' in file['filename'] else ''
                if not extension:
                    continue
                
                # Get language info from extension
                lang_info = LanguageTools.get_language_from_extension(extension)
                if not lang_info:
                    continue
                
                # Calculate confidence score
                confidence = LanguageTools.calculate_confidence(file['content'], lang_info)
                logger.info(f"Language {lang_info['name']} detected with {confidence:.2f} confidence for file {file['filename']}")
                
                # Update language statistics
                if lang_info['name'] not in language_stats:
                    language_stats[lang_info['name']] = {
                        'bytes': 0,
                        'confidence': 0,
                        'type': lang_info['type']
                    }
                
                language_stats[lang_info['name']]['bytes'] += file['size']
                language_stats[lang_info['name']]['confidence'] = max(
                    language_stats[lang_info['name']]['confidence'],
                    confidence
                )
                total_bytes += file['size']
            
            # Sort languages by bytes
            sorted_languages = sorted(
                [(name, info) for name, info in language_stats.items()],
                key=lambda x: x[1]['bytes'],
                reverse=True
            )
            
            if not sorted_languages:
                raise ValueError("No languages detected in files")
            
            # Create RepositoryLanguages object
            primary_lang = sorted_languages[0]
            self.current_detection = {
                'primary': {
                    'name': primary_lang[0],
                    'confidence': primary_lang[1]['confidence'],
                    'bytes': primary_lang[1]['bytes'],
                    'type': primary_lang[1]['type']
                },
                'secondary': [
                    {
                        'name': lang[0],
                        'confidence': info['confidence'],
                        'bytes': info['bytes'],
                        'type': info['type']
                    }
                    for lang, info in sorted_languages[1:]
                ],
                'total_bytes': total_bytes,
                'detection_source': 'content'
            }
            
            return self.current_detection
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            raise RuntimeError(f"Language detection failed: {str(e)}")

    def validateDetection(self, detection: RepositoryLanguages) -> bool:
        """Validate language detection results"""
        try:
            # Check required fields
            required_fields = {'primary', 'secondary', 'total_bytes', 'detection_source'}
            if not all(field in detection for field in required_fields):
                return False
            
            # Validate primary language
            required_lang_fields = {'name', 'confidence', 'bytes', 'type'}
            if not all(field in detection['primary'] for field in required_lang_fields):
                return False
            
            # Validate confidence scores
            if not (0 <= detection['primary']['confidence'] <= 1):
                return False
            
            # Validate secondary languages
            for lang in detection['secondary']:
                if not all(field in lang for field in required_lang_fields):
                    return False
                if not (0 <= lang['confidence'] <= 1):
                    return False
            
            # Validate total bytes
            total = detection['primary']['bytes'] + sum(lang['bytes'] for lang in detection['secondary'])
            if total != detection['total_bytes']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False

    def getPrimaryLanguage(self) -> str:
        """Get the primary language name"""
        if not self.current_detection:
            raise RuntimeError("No language detection results available")
        return self.current_detection['primary']['name']

    def getSecondaryLanguages(self) -> List[str]:
        """Get list of secondary language names"""
        if not self.current_detection:
            raise RuntimeError("No language detection results available")
        return [lang['name'] for lang in self.current_detection['secondary']]
