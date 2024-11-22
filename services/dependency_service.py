import subprocess
import json
import os
import logging
from typing import Dict, List, Optional
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyService:
    def __init__(self):
        """Initialize dependency analysis service"""
        self.temp_dir: str = ""
        
    def analyze_dependencies(self, files: List[Dict]) -> Dict:
        """Analyze dependencies in the provided files"""
        try:
            logger.info("Code Structure Analysis: Starting dependency analysis")
            total_files = len(files)
            logger.info(f"Code Structure Analysis: Found {total_files} files to analyze")
            
            # Create temporary directory for analysis
            self.temp_dir = tempfile.mkdtemp()
            logger.info("Code Structure Analysis: Created temporary directory for analysis")
            
            try:
                # Write files to temporary directory with progress tracking
                processed_files = 0
                for file in files:
                    try:
                        current_filename = file.get('filename', '')
                        if not current_filename:
                            continue
                            
                        processed_files += 1
                        progress = (processed_files / total_files) * 100
                        logger.info(f"Code Structure Analysis: Processing file {processed_files}/{total_files} ({progress:.1f}%): {current_filename}")
                        
                        self._write_files_to_temp([file])
                    except Exception as e:
                        logger.error(f"Code Structure Analysis: Error processing file: {str(e)}")
                
                # Run dependency analysis
                logger.info("Code Structure Analysis: Running dependency-cruiser analysis")
                dep_cruiser_result = self._run_dependency_cruiser()
                
                logger.info("Code Structure Analysis: Running madge analysis")
                madge_result = self._run_madge()
                
                # Process and combine results
                logger.info("Code Structure Analysis: Processing analysis results")
                analysis_result = self._process_results(dep_cruiser_result, madge_result)
                
                logger.info("Code Structure Analysis: Analysis completed successfully")
                return analysis_result
                
            except Exception as e:
                logger.error(f"Code Structure Analysis: Failed to analyze dependencies: {str(e)}")
                return {
                    'error': str(e),
                    'dependency_graph': None,
                    'circular_dependencies': [],
                    'external_dependencies': []
                }
            
        finally:
            # Cleanup temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    import shutil
                    shutil.rmtree(self.temp_dir)
                    logger.info("Code Structure Analysis: Cleaned up temporary directory")
                except Exception as e:
                    logger.error(f"Code Structure Analysis: Failed to cleanup temp directory: {str(e)}")
    
    def _write_files_to_temp(self, files: List[Dict]) -> None:
        """Write PR files to temporary directory with filtering"""
        # File extensions to analyze
        CODE_EXTENSIONS = {
            # JavaScript/TypeScript
            '.js': 'JavaScript',
            '.jsx': 'JavaScript React',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript React',
            # Python
            '.py': 'Python',
            # Other languages
            '.java': 'Java',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        
        # Skip patterns for configuration and test files
        SKIP_PATTERNS = [
            '.test.', '.spec.', '.config.',  # Test and config files
            'package.json', 'package-lock.json',  # Package files
            '.replit', 'poetry.lock', 'pyproject.toml',  # Project config
            '.git', '.env', '.vscode',  # Hidden/IDE files
            'README', 'LICENSE', '.md', '.txt'  # Documentation
        ]
        
        for file in files:
            filename = file.get('filename', '')
            if not filename or not file.get('patch'):
                continue
                
            # Get file extension and validate
            ext = os.path.splitext(filename)[1].lower()
            if ext not in CODE_EXTENSIONS:
                logger.debug(f"Skipping non-code file: {filename} (unsupported extension)")
                continue
                
            # Skip files matching skip patterns
            if any(pattern in filename.lower() for pattern in SKIP_PATTERNS):
                logger.debug(f"Skipping file: {filename} (matches skip pattern)")
                continue
                
            logger.info(f"Processing {CODE_EXTENSIONS[ext]} file: {filename}")
            
            file_path = os.path.join(str(self.temp_dir), filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            try:
                logger.info(f"Processing file for analysis: {filename}")
                with open(file_path, 'w') as f:
                    f.write(file['patch'])
            except Exception as e:
                logger.error(f"Failed to write file {filename}: {str(e)}")
                continue
            
            logger.debug(f"Successfully wrote {filename} to temp directory")
    
    def _run_dependency_cruiser(self) -> Optional[Dict]:
        """Run dependency-cruiser analysis with improved error handling"""
        try:
            logger.info("Configuring dependency-cruiser analysis")
            # Custom dependency-cruiser configuration
            config = {
                "forbidden": [
                    {
                        "name": "no-circular",
                        "severity": "error",
                        "from": {},
                        "to": {
                            "circular": True
                        }
                    }
                ],
                "options": {
                    "doNotFollow": {
                        "path": "node_modules",
                        "dependencyTypes": [
                            "npm",
                            "npm-dev",
                            "npm-optional",
                            "npm-peer",
                            "npm-bundled"
                        ]
                    },
                    "exclude": "\\.(spec|test|config)\\.(js|ts|jsx|tsx)$|\\.(replit|json|md|txt|svg)$",
                    "maxDepth": 6,
                    "includeOnly": "\\.(js|jsx|ts|tsx|py)$",
                    "moduleSystems": ["amd", "cjs", "es6", "tsd"],
                    "tsConfig": None,
                    "tsPreCompilationDeps": "true",
                    "preserveSymlinks": "false",
                    "webpackConfig": None,
                    "enhancedResolveOptions": {
                        "exportsFields": ["exports"],
                        "conditionNames": ["import", "require", "node", "default"],
                        "extensions": [".js", ".jsx", ".ts", ".tsx", ".py"]
                    },
                    "cache": {
                        "enabled": "true",
                        "strategy": "metadata"
                    }
                }
            }
            
            config_path = os.path.join(str(self.temp_dir), '.dependency-cruiser.json')
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info("Successfully wrote dependency-cruiser configuration")
            except Exception as e:
                logger.error(f"Failed to write dependency-cruiser configuration: {str(e)}")
                return None
                
            # Run dependency-cruiser with JSON output and handle errors
            try:
                result = subprocess.run(
                    ['npx', 'depcruise', '--config', '.dependency-cruiser.json', '--output-type', 'json', '.'],
                    cwd=self.temp_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return json.loads(result.stdout)
                else:
                    logger.error(f"dependency-cruiser failed: {result.stderr}")
                    return None
                    
            except Exception as e:
                logger.error(f"Failed to run dependency-cruiser: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to run dependency-cruiser: {str(e)}")
            return None
    
    def _run_madge(self) -> Optional[Dict]:
        """Run madge analysis"""
        try:
            # Run madge with JSON output
            result = subprocess.run(
                ['npx', 'madge', '--json', '.'],
                cwd=self.temp_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"madge failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to run madge: {str(e)}")
            return None
    
    def _process_results(self, dep_cruiser_result: Optional[Dict], madge_result: Optional[Dict]) -> Dict:
        """Process and combine results from both tools"""
        result = {
            'dependency_graph': {},
            'circular_dependencies': [],
            'external_dependencies': [],
            'structure_analysis': {},
            'error': None
        }
        
        if not dep_cruiser_result and not madge_result:
            result['error'] = "No analysis results available from either tool"
            return result
            
        dependency_graph = {}
        circular_dependencies = []
        external_dependencies = []
        structure_analysis = {}
        
        # Process dependency-cruiser results
        if dep_cruiser_result:
            modules = dep_cruiser_result.get('modules', [])
            for module in modules:
                source = module.get('source', '')
                dependencies = [dep.get('resolved', '') for dep in module.get('dependencies', [])]
                
                if source:
                    dependency_graph[source] = dependencies
                    
                    # Collect external dependencies
                    for dep in module.get('dependencies', []):
                        if dep.get('dependencyTypes', []):
                            if 'npm' in dep['dependencyTypes'] or 'core' in dep['dependencyTypes']:
                                external_dependencies.append({
                                    'module': source,
                                    'depends_on': dep['resolved']
                                })
                    
                    # Perform code structure analysis
                    structure_analysis[source] = {
                        'exports': self._analyze_exports(module),
                        'functions': self._analyze_function_length(module),
                        'duplication': self._find_code_duplication(module),
                        'comment_ratio': self._calculate_comment_ratio(module)
                    }
        
        # Process madge results for circular dependencies
        if madge_result:
            for source, deps in madge_result.items():
                if source in deps:  # Self-dependency
                    circular_dependencies.append([source])
                for dep in deps:
                    if dep in madge_result and source in madge_result[dep]:
                        # Found circular dependency
                        if [source, dep] not in circular_dependencies and [dep, source] not in circular_dependencies:
                            circular_dependencies.append([source, dep])
        
        # Combine results
        result.update({
            'dependency_graph': dependency_graph,
            'circular_dependencies': circular_dependencies,
            'external_dependencies': external_dependencies,
            'structure_analysis': structure_analysis
        })
        
        return result

    def _analyze_exports(self, module: Dict) -> List[str]:
        """Analyze module exports"""
        exports = []
        if not module.get('source'):
            return exports
            
        content = module.get('source', '')
        
        # Find exports through __all__
        for line in content.splitlines():
            if '__all__' in line and '=' in line:
                try:
                    # Extract list items from __all__ definition
                    items = line.split('=')[1].strip()
                    if items.startswith('[') and items.endswith(']'):
                        items = items[1:-1]  # Remove brackets
                        exports.extend([item.strip().strip("'").strip('"') 
                                     for item in items.split(',') if item.strip()])
                except Exception as e:
                    logger.error(f"Error parsing __all__ in {module.get('source', '')}: {str(e)}")
        
        # Find other exports (public functions and classes)
        for line in content.splitlines():
            if line.strip().startswith(('def ', 'class ')) and not line.strip().startswith('_'):
                name = line.split()[1].split('(')[0]
                if name not in exports:
                    exports.append(name)
        
        return exports

    def _analyze_function_length(self, module: Dict) -> Dict[str, int]:
        """Analyze function lengths in the module"""
        functions = {}
        if not module.get('source'):
            return functions

        current_function = None
        current_length = 0
        
        for line in module.get('source', '').splitlines():
            if line.strip().startswith('def '):
                if current_function:
                    functions[current_function] = current_length
                current_function = line.split('def ')[1].split('(')[0]
                current_length = 1
            elif current_function and line.strip():
                current_length += 1
            elif current_function and not line.strip():
                functions[current_function] = current_length
                current_function = None
                current_length = 0
        
        if current_function:
            functions[current_function] = current_length
            
        return functions

    def _find_code_duplication(self, module: Dict) -> Dict:
        """Find potential code duplication"""
        duplication = {
            'duplicate_blocks': [],
            'similarity_score': 0.0
        }
        
        if not module.get('source'):
            return duplication
        
        content = module.get('source', '')
        lines = content.splitlines()
        block_size = 6  # Minimum block size to consider
        
        for i in range(len(lines) - block_size):
            block1 = '\n'.join(lines[i:i + block_size])
            for j in range(i + block_size, len(lines) - block_size):
                block2 = '\n'.join(lines[j:j + block_size])
                if block1 == block2:
                    duplication['duplicate_blocks'].append({
                        'start_line1': i + 1,
                        'end_line1': i + block_size,
                        'start_line2': j + 1,
                        'end_line2': j + block_size
                    })
        
        if duplication['duplicate_blocks']:
            total_duplicated = sum(block_size for _ in duplication['duplicate_blocks'])
            duplication['similarity_score'] = total_duplicated / len(lines)
        
    def _calculate_comment_ratio(self, module: Dict) -> float:
        """Calculate the ratio of comments to code"""
        if not module.get('source'):
            return 0.0
        
        content = module.get('source', '')
        lines = content.splitlines()
        
        comment_lines = 0
        code_lines = 0
        in_multiline = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
                
            # Handle multiline comments
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_multiline:
                    in_multiline = False
                else:
                    in_multiline = True
                comment_lines += 1
                continue
                
            # Count comment and code lines
            if in_multiline:
                comment_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        total_lines = comment_lines + code_lines
        return round(comment_lines / total_lines, 2) if total_lines > 0 else 0.0
        return duplication

    def _calculate_comment_ratio(self, module: Dict) -> float:
        """Calculate the ratio of comments to code"""
        if not module.get('source'):
            return 0.0
        
        content = module.get('source', '')
        lines = content.splitlines()
        
        comment_lines = len([line for line in lines 
                           if line.strip().startswith('#') or 
                           line.strip().startswith('"""') or 
                           line.strip().startswith("'''")]) 
        
        code_lines = len([line for line in lines 
                         if line.strip() and 
                         not line.strip().startswith('#') and 
                         not line.strip().startswith('"""') and 
                         not line.strip().startswith("'''")])
        
        return comment_lines / max(1, code_lines)
