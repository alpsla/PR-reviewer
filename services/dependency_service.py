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
        self.temp_dir = None
        
    def analyze_dependencies(self, files: List[Dict]) -> Dict:
        """Analyze dependencies in the provided files"""
        try:
            # Create temporary directory for analysis
            self.temp_dir = tempfile.mkdtemp()
            
            # Write files to temporary directory
            self._write_files_to_temp(files)
            
            # Run dependency analysis
            dep_cruiser_result = self._run_dependency_cruiser()
            madge_result = self._run_madge()
            
            # Process and combine results
            analysis_result = self._process_results(dep_cruiser_result, madge_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to analyze dependencies: {str(e)}")
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
                except Exception as e:
                    logger.error(f"Failed to cleanup temp directory: {str(e)}")
    
    def _write_files_to_temp(self, files: List[Dict]) -> None:
        """Write PR files to temporary directory"""
        for file in files:
            if not file.get('patch'):
                continue
                
            file_path = os.path.join(self.temp_dir, file['filename'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            try:
                with open(file_path, 'w') as f:
                    f.write(file['patch'])
            except Exception as e:
                logger.error(f"Failed to write file {file['filename']}: {str(e)}")
    
    def _run_dependency_cruiser(self) -> Optional[Dict]:
        """Run dependency-cruiser analysis"""
        try:
            # Initialize depcruise config
            config = {
                "extends": "dependency-cruiser/configs/recommended-strict",
                "options": {
                    "doNotFollow": {
                        "path": "node_modules"
                    },
                    "exclude": "(\\.spec\\.js$|\\.test\\.js$)",
                    "maxDepth": 6
                }
            }
            
            config_path = os.path.join(self.temp_dir, '.dependency-cruiser.json')
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            # Run dependency-cruiser with JSON output
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
