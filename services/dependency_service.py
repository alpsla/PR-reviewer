import subprocess
import json
import os
import logging
import tempfile
import shutil
import backoff
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyAnalysisError(Exception):
    """Custom exception for dependency analysis errors"""
    pass

class DependencyService:
    def __init__(self):
        """Initialize dependency analysis service"""
        self.temp_dir: Optional[Path] = None
        
    def analyze_dependencies(self, files: List[Dict]) -> Dict:
        """Analyze dependencies in the provided files"""
        if not files:
            logger.warning("No files provided for analysis")
            return self._empty_analysis_result()
            
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            self.temp_dir = Path(temp_dir)
            logger.info(f"Created temporary directory: {self.temp_dir}")
            
            # Filter JavaScript/TypeScript files
            js_files = [f for f in files if f['filename'].endswith(('.js', '.jsx', '.ts', '.tsx'))]
            if not js_files:
                logger.info("No JavaScript/TypeScript files found for analysis")
                return self._empty_analysis_result()
            
            # Create necessary configuration files
            self._create_config_files()
            
            # Write files to temporary directory
            self._write_files_to_temp(js_files)
            
            # Run dependency analysis
            dep_cruiser_result = self._run_dependency_cruiser()
            madge_result = self._run_madge()
            
            # Process results
            analysis_result = self._process_results(dep_cruiser_result, madge_result)
            logger.info("Dependency analysis completed successfully")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to analyze dependencies: {str(e)}")
            return self._empty_analysis_result(error=str(e))
        finally:
            # Cleanup temporary directory
            if self.temp_dir and self.temp_dir.exists():
                try:
                    shutil.rmtree(str(self.temp_dir))
                    logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
                except Exception as e:
                    logger.error(f"Failed to cleanup temp directory: {str(e)}")
    
    def _create_config_files(self):
        """Create necessary configuration files"""
        if not self.temp_dir:
            raise DependencyAnalysisError("Temporary directory not initialized")
            
        # Create package.json
        package_json = {
            "name": "dependency-analysis",
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "dependencies": {
                "dependency-cruiser": "*",
                "madge": "*"
            }
        }
        
        package_json_path = self.temp_dir / 'package.json'
        package_json_path.write_text(json.dumps(package_json))
        
        # Install dependencies in the temporary directory
        try:
            subprocess.run(
                ['npm', 'install'],
                cwd=str(self.temp_dir),
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            logger.info("Created package.json and installed dependencies")
        except Exception as e:
            logger.error(f"Failed to install dependencies: {str(e)}")
            raise DependencyAnalysisError(f"Failed to install dependencies: {str(e)}")
        
        # Create tsconfig.json for TypeScript support
        tsconfig_json = {
            "compilerOptions": {
                "target": "es2020",
                "module": "esnext",
                "moduleResolution": "node",
                "jsx": "react",
                "allowJs": True,
                "checkJs": False,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "resolveJsonModule": True
            },
            "include": ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"],
            "exclude": ["node_modules"]
        }
        
        tsconfig_path = self.temp_dir / 'tsconfig.json'
        tsconfig_path.write_text(json.dumps(tsconfig_json))
        
        logger.info("Created configuration files")
    
    def _empty_analysis_result(self, error: Optional[str] = None) -> Dict:
        """Return empty analysis result structure"""
        return {
            'error': error,
            'dependency_graph': {},
            'circular_dependencies': [],
            'external_dependencies': [],
            'summary': {
                'total_modules': 0,
                'circular_dependencies_count': 0,
                'external_dependencies_count': 0
            }
        }
    
    def _write_files_to_temp(self, files: List[Dict]) -> None:
        """Write PR files to temporary directory maintaining structure"""
        if not self.temp_dir:
            raise DependencyAnalysisError("Temporary directory not initialized")
            
        logger.info("Writing files to temporary directory")
        
        for file in files:
            try:
                # Use pathlib for safer path handling
                file_path = self.temp_dir / file['filename']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Get actual content instead of just patch
                content = file.get('content', '')
                if not content and 'patch' in file:
                    content = file['patch']
                
                file_path.write_text(content)
                logger.debug(f"Wrote file: {file['filename']}")
                
            except Exception as e:
                logger.error(f"Failed to write file {file['filename']}: {str(e)}")
                raise DependencyAnalysisError(f"Failed to write file {file['filename']}: {str(e)}")
    
    @backoff.on_exception(backoff.expo, subprocess.CalledProcessError, max_tries=2)
    def _run_dependency_cruiser(self) -> Optional[Dict]:
        """Run dependency-cruiser analysis with retries"""
        if not self.temp_dir:
            raise DependencyAnalysisError("Temporary directory not initialized")
            
        try:
            logger.info("Running dependency-cruiser analysis")
            
            # Create minimal config
            config = {
                "options": {
                    "doNotFollow": {
                        "path": "node_modules"
                    },
                    "exclude": "\\.spec\\.(js|jsx|ts|tsx)$",
                    "maxDepth": 10,
                    "moduleSystems": ["cjs", "es6"],
                    "tsConfig": {
                        "fileName": "./tsconfig.json"
                    },
                    "enhancedResolvers": ["node", "typescript"]
                }
            }
            
            # Write config file
            config_path = self.temp_dir / '.dependency-cruiser.json'
            config_path.write_text(json.dumps(config))
            
            # Run analysis using local node_modules
            result = subprocess.run(
                ['npx', '--no-install', 'dependency-cruiser', '--config', '.dependency-cruiser.json', '--output-type', 'json', '.'],
                cwd=str(self.temp_dir),
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            if result.stdout:
                logger.info("Successfully ran dependency-cruiser")
                return json.loads(result.stdout)
            
            logger.warning("dependency-cruiser returned empty result")
            return None
            
        except Exception as e:
            logger.error(f"Failed to run dependency-cruiser: {str(e)}")
            return None
    
    @backoff.on_exception(backoff.expo, subprocess.CalledProcessError, max_tries=2)
    def _run_madge(self) -> Optional[Dict]:
        """Run madge analysis with retries"""
        if not self.temp_dir:
            raise DependencyAnalysisError("Temporary directory not initialized")
            
        try:
            logger.info("Running madge analysis")
            
            # Run analysis using local node_modules
            result = subprocess.run(
                ['npx', '--no-install', 'madge', '--json', '--extensions', 'js,jsx,ts,tsx', '.'],
                cwd=str(self.temp_dir),
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            if result.stdout:
                logger.info("Successfully ran madge")
                return json.loads(result.stdout)
            
            logger.warning("madge returned empty result")
            return None
            
        except Exception as e:
            logger.error(f"Failed to run madge: {str(e)}")
            return None
    
    def _process_results(self, dep_cruiser_result: Optional[Dict], madge_result: Optional[Dict]) -> Dict:
        """Process and combine results from both tools"""
        logger.info("Processing dependency analysis results")
        
        if not dep_cruiser_result and not madge_result:
            logger.warning("No results from either analysis tool")
            return self._empty_analysis_result(error="No analysis results available")
        
        dependency_graph = {}
        circular_dependencies = []
        external_dependencies = []
        
        # Process dependency-cruiser results
        if dep_cruiser_result and 'modules' in dep_cruiser_result:
            for module in dep_cruiser_result['modules']:
                source = module.get('source', '')
                dependencies = [
                    dep.get('resolved', '') 
                    for dep in module.get('dependencies', [])
                    if dep.get('resolved')
                ]
                
                if source and dependencies:
                    dependency_graph[source] = dependencies
                    
                    # Collect external dependencies
                    for dep in module.get('dependencies', []):
                        if not dep.get('resolved'):
                            continue
                            
                        dep_types = dep.get('dependencyTypes', [])
                        if any(t in dep_types for t in ['npm', 'core']):
                            external_dependencies.append({
                                'module': source,
                                'depends_on': dep['resolved'],
                                'type': dep_types[0]
                            })
        
        # Process madge results for circular dependencies
        if madge_result:
            visited = set()
            for source, deps in madge_result.items():
                if source in deps:  # Self-dependency
                    circular_dependencies.append([source])
                for dep in deps:
                    if dep in madge_result and source in madge_result[dep]:
                        # Found circular dependency
                        cycle = sorted([source, dep])
                        cycle_key = '->'.join(cycle)
                        if cycle_key not in visited:
                            visited.add(cycle_key)
                            circular_dependencies.append(cycle)
        
        logger.info(f"Found {len(circular_dependencies)} circular dependencies and {len(external_dependencies)} external dependencies")
        
        return {
            'dependency_graph': dependency_graph,
            'circular_dependencies': circular_dependencies,
            'external_dependencies': external_dependencies,
            'summary': {
                'total_modules': len(dependency_graph),
                'circular_dependencies_count': len(circular_dependencies),
                'external_dependencies_count': len(external_dependencies)
            }
        }
