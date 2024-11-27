from typing import Dict, List, Optional, Any
import re
from .typescript_analyzer import TypeScriptAnalyzer

class ReactAnalyzer(TypeScriptAnalyzer):
    """Enhanced React-specific analyzer building on TypeScript capabilities"""

    def __init__(self):
        super().__init__()
        self._compile_react_patterns()

    def analyze(self, content: str, filename: str) -> Dict:
        """Main analysis entry point"""
        # Get base TypeScript analysis
        ts_analysis = super().analyze(content, filename)
        
        # Add React-specific analysis
        return {
            **ts_analysis,
            'components': self.analyze_components(content),
            'hooks': self.analyze_hooks(content),
            'patterns': self.analyze_react_patterns(content),
            'performance': self.analyze_performance(content),
            'accessibility': self.analyze_accessibility(content)
        }

    def analyze_components(self, content: str) -> Dict:
        """Analyze React component structure and patterns"""
        return {
            'functional': self._analyze_functional_components(content),
            'class': self._analyze_class_components(content),
            'hoc': self._analyze_higher_order_components(content),
            'props': self._analyze_props(content),
            'state': self._analyze_state_usage(content),
            'lifecycle': self._analyze_lifecycle_methods(content),
            'error_boundaries': self._analyze_error_boundaries(content)
        }

    def analyze_hooks(self, content: str) -> Dict:
        """Analyze React hooks usage and patterns"""
        return {
            'state_hooks': self._analyze_state_hooks(content),
            'effect_hooks': self._analyze_effect_hooks(content),
            'context_hooks': self._analyze_context_hooks(content),
            'ref_hooks': self._analyze_ref_hooks(content),
            'custom_hooks': self._analyze_custom_hooks(content),
            'memoization': self._analyze_memoization_hooks(content),
            'dependencies': self._analyze_hook_dependencies(content)
        }

    def analyze_react_patterns(self, content: str) -> Dict:
        """Analyze React design patterns and best practices"""
        return {
            'composition': self._analyze_component_composition(content),
            'render_props': self._analyze_render_props(content),
            'context_usage': self._analyze_context_usage(content),
            'code_splitting': self._analyze_code_splitting(content),
            'suspense': self._analyze_suspense_usage(content),
            'error_handling': self._analyze_error_handling(content)
        }

    def analyze_performance(self, content: str) -> Dict:
        """Analyze React performance optimizations"""
        return {
            'memo_usage': self._analyze_memo_usage(content),
            'callback_usage': self._analyze_callback_usage(content),
            'virtual_list': self._analyze_virtual_list_usage(content),
            'lazy_loading': self._analyze_lazy_loading(content),
            'render_optimization': self._analyze_render_optimization(content)
        }

    def analyze_accessibility(self, content: str) -> Dict:
        """Analyze React accessibility compliance"""
        return {
            'aria_props': self._analyze_aria_props(content),
            'semantic_html': self._analyze_semantic_html(content),
            'keyboard_handlers': self._analyze_keyboard_handlers(content),
            'focus_management': self._analyze_focus_management(content),
            'alt_texts': self._analyze_alt_texts(content)
        }

    def _compile_react_patterns(self):
        """Compile regex patterns for React analysis"""
        self.react_patterns = {
            'functional_component': re.compile(
                r'(?:export\s+)?(?:const|function)\s+([A-Z]\w+)\s*(?:=\s*)?(?:\([^)]*\)|\([^)]*\)\s*:\s*[^{]+)\s*=>\s*{([^}]+)}'
            ),
            'class_component': re.compile(
                r'class\s+([A-Z]\w+)\s+extends\s+(?:React\.)?Component\s*{([^}]+)}'
            ),
            'hoc': re.compile(
                r'(?:export\s+)?(?:const|function)\s+(?:with[A-Z]\w+)\s*\([^)]*\)\s*{([^}]+)}'
            ),
            'hook_usage': re.compile(
                r'(?:const|let)\s+\[[^,\]]+,\s*[^\]]+\]\s*=\s*use[A-Z]\w+\('
            ),
            'effect_hook': re.compile(
                r'useEffect\(\s*\(\)\s*=>\s*{([^}]+)},\s*\[(.*?)\]\)'
            ),
            'memo': re.compile(
                r'React\.memo\(\s*([A-Z]\w+)'
            ),
            'context': re.compile(
                r'(?:React\.)?createContext\((.*?)\)'
            ),
            'suspense': re.compile(
                r'<Suspense\s+fallback={([^}]+)}\s*>'
            ),
            'error_boundary': re.compile(
                r'static\s+getDerivedStateFromError|componentDidCatch'
            )
        }

    def _analyze_functional_components(self, content: str) -> List[Dict]:
        """Analyze functional component implementations"""
        components = []
        for match in self.react_patterns['functional_component'].finditer(content):
            name, body = match.groups()
            components.append({
                'name': name,
                'props': self._extract_props(body),
                'hooks': self._extract_hooks(body),
                'render_count': self._count_renders(body),
                'location': match.start()
            })
        return components

    def _analyze_class_components(self, content: str) -> List[Dict]:
        """Analyze class component implementations"""
        components = []
        for match in self.react_patterns['class_component'].finditer(content):
            name, body = match.groups()
            components.append({
                'name': name,
                'state': self._extract_state(body),
                'lifecycle_methods': self._extract_lifecycle_methods(body),
                'render_method': self._extract_render_method(body),
                'location': match.start()
            })
        return components

    def _analyze_hook_dependencies(self, content: str) -> List[Dict]:
        """Analyze hook dependency arrays"""
        dependencies = []
        for match in self.react_patterns['effect_hook'].finditer(content):
            effect_body, deps = match.groups()
            dependencies.append({
                'effect': effect_body.strip(),
                'dependencies': [d.strip() for d in deps.split(',')] if deps else [],
                'location': match.start()
            })
        return dependencies

    def _analyze_memo_usage(self, content: str) -> Dict[str, Any]:
        """Analyze React.memo usage and optimization"""
        memo_components = []
        for match in self.react_patterns['memo'].finditer(content):
            component_name = match.group(1)
            memo_components.append({
                'component': component_name,
                'custom_compare': 'areEqual' in content or 'compareProps' in content,
                'location': match.start()
            })
        return {
            'count': len(memo_components),
            'components': memo_components
        }

    def _analyze_context_usage(self, content: str) -> List[Dict]:
        """Analyze React Context usage"""
        contexts = []
        for match in self.react_patterns['context'].finditer(content):
            default_value = match.group(1)
            contexts.append({
                'default_value': default_value.strip(),
                'providers': len(re.findall(r'\.Provider', content)),
                'consumers': len(re.findall(r'\.Consumer|useContext', content)),
                'location': match.start()
            })
        return contexts

    def _analyze_error_boundaries(self, content: str) -> Dict[str, Any]:
        """Analyze error boundary implementation"""
        has_error_boundary = bool(self.react_patterns['error_boundary'].search(content))
        return {
            'implemented': has_error_boundary,
            'fallback_ui': 'fallback' in content,
            'error_reporting': 'reportError' in content or 'logError' in content
        }

    def _analyze_suspense_usage(self, content: str) -> List[Dict]:
        """Analyze React Suspense usage"""
        suspense_usage = []
        for match in self.react_patterns['suspense'].finditer(content):
            fallback = match.group(1)
            suspense_usage.append({
                'fallback': fallback.strip(),
                'lazy_components': len(re.findall(r'React\.lazy', content)),
                'location': match.start()
            })
        return suspense_usage

    def _extract_props(self, component_body: str) -> Dict[str, str]:
        """Extract and analyze component props"""
        props = {}
        prop_matches = re.finditer(r'props\.(\w+)|{\s*(\w+)\s*}', component_body)
        for match in prop_matches:
            prop_name = match.group(1) or match.group(2)
            props[prop_name] = self._infer_prop_type(component_body, prop_name)
        return props

    def _extract_hooks(self, component_body: str) -> List[Dict]:
        """Extract and analyze hook usage"""
        hooks = []
        hook_matches = re.finditer(r'use(\w+)\((.*?)\)', component_body)
        for match in hook_matches:
            hook_name, args = match.groups()
            hooks.append({
                'name': f'use{hook_name}',
                'arguments': [arg.strip() for arg in args.split(',') if arg.strip()],
                'location': match.start()
            })
        return hooks

    def _analyze_render_optimization(self, content: str) -> Dict[str, Any]:
        """Analyze render optimization techniques"""
        return {
            'memo_count': len(re.findall(r'React\.memo', content)),
            'callback_count': len(re.findall(r'useCallback', content)),
            'memo_hooks': len(re.findall(r'useMemo', content)),
            'pure_components': len(re.findall(r'extends PureComponent', content))
        }

    def _analyze_accessibility(self, content: str) -> Dict[str, Any]:
        """Analyze accessibility implementation"""
        return {
            'aria_attributes': len(re.findall(r'aria-\w+', content)),
            'role_attributes': len(re.findall(r'role=', content)),
            'semantic_elements': len(re.findall(r'<(?:nav|main|article|aside|footer|header|section)', content)),
            'alt_texts': len(re.findall(r'alt=', content))
        }
