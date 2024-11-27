from typing import Dict, List, Optional, Any
import re
from .typescript_analyzer import TypeScriptAnalyzer

class AngularAnalyzer(TypeScriptAnalyzer):
    """Enhanced Angular-specific analyzer building on TypeScript capabilities"""

    def __init__(self):
        super().__init__()
        self._compile_angular_patterns()

    def analyze(self, content: str, filename: str) -> Dict:
        """Main analysis entry point"""
        # Get base TypeScript analysis
        ts_analysis = super().analyze(content, filename)
        
        # Add Angular-specific analysis
        return {
            **ts_analysis,
            'components': self.analyze_components(content),
            'decorators': self.analyze_decorators(content),
            'services': self.analyze_services(content),
            'templates': self.analyze_templates(content),
            'performance': self.analyze_performance(content),
            'patterns': self.analyze_angular_patterns(content)
        }

    def analyze_components(self, content: str) -> Dict:
        """Analyze Angular component structure"""
        return {
            'metadata': self._analyze_component_metadata(content),
            'lifecycle': self._analyze_lifecycle_hooks(content),
            'inputs': self._analyze_inputs(content),
            'outputs': self._analyze_outputs(content),
            'view_child': self._analyze_view_children(content),
            'content_child': self._analyze_content_children(content)
        }

    def analyze_decorators(self, content: str) -> Dict:
        """Analyze Angular decorators"""
        return {
            'component': self._analyze_component_decorator(content),
            'directive': self._analyze_directive_decorator(content),
            'pipe': self._analyze_pipe_decorator(content),
            'injectable': self._analyze_injectable_decorator(content),
            'host_bindings': self._analyze_host_bindings(content),
            'host_listeners': self._analyze_host_listeners(content)
        }

    def analyze_services(self, content: str) -> Dict:
        """Analyze Angular services"""
        return {
            'dependency_injection': self._analyze_di_patterns(content),
            'http_client': self._analyze_http_usage(content),
            'observables': self._analyze_observables(content),
            'state_management': self._analyze_state_management(content),
            'providers': self._analyze_providers(content)
        }

    def analyze_templates(self, content: str) -> Dict:
        """Analyze Angular template syntax"""
        return {
            'bindings': self._analyze_bindings(content),
            'events': self._analyze_event_bindings(content),
            'structural_directives': self._analyze_structural_directives(content),
            'pipes': self._analyze_pipe_usage(content),
            'forms': self._analyze_forms(content),
            'template_refs': self._analyze_template_refs(content)
        }

    def analyze_performance(self, content: str) -> Dict:
        """Analyze Angular performance optimizations"""
        return {
            'change_detection': self._analyze_change_detection(content),
            'pure_pipes': self._analyze_pure_pipes(content),
            'track_by': self._analyze_track_by(content),
            'async_pipe': self._analyze_async_pipe(content),
            'lazy_loading': self._analyze_lazy_loading(content)
        }

    def analyze_angular_patterns(self, content: str) -> Dict:
        """Analyze Angular-specific patterns and best practices"""
        return {
            'routing': self._analyze_routing(content),
            'guards': self._analyze_guards(content),
            'interceptors': self._analyze_interceptors(content),
            'resolvers': self._analyze_resolvers(content),
            'modules': self._analyze_modules(content)
        }

    def _compile_angular_patterns(self):
        """Compile regex patterns for Angular analysis"""
        self.angular_patterns = {
            'component': re.compile(
                r'@Component\(\s*({[^}]+})\s*\)'
            ),
            'directive': re.compile(
                r'@Directive\(\s*({[^}]+})\s*\)'
            ),
            'injectable': re.compile(
                r'@Injectable\(\s*({[^}]+})\s*\)'
            ),
            'input': re.compile(
                r'@Input\(\s*(?:\'([^\']+)\')?\s*\)\s*(\w+)'
            ),
            'output': re.compile(
                r'@Output\(\s*(?:\'([^\']+)\')?\s*\)\s*(\w+)\s*=\s*new\s+EventEmitter'
            ),
            'lifecycle': re.compile(
                r'(?:ng|after|before)(?:OnInit|OnDestroy|OnChanges|DoCheck|AfterViewInit|AfterViewChecked|AfterContentInit|AfterContentChecked)\('
            ),
            'view_child': re.compile(
                r'@ViewChild\(\s*([^,)]+)(?:,\s*({[^}]+}))?\s*\)'
            ),
            'content_child': re.compile(
                r'@ContentChild\(\s*([^,)]+)(?:,\s*({[^}]+}))?\s*\)'
            ),
            'host_binding': re.compile(
                r'@HostBinding\(\s*\'([^\']+)\'\s*\)'
            ),
            'host_listener': re.compile(
                r'@HostListener\(\s*\'([^\']+)\'(?:,\s*\[([^\]]+)\])?\s*\)'
            )
        }

    def _analyze_component_metadata(self, content: str) -> Dict[str, Any]:
        """Analyze component metadata configuration"""
        match = self.angular_patterns['component'].search(content)
        if not match:
            return {'valid': False}
        
        metadata = match.group(1)
        return {
            'valid': True,
            'selector': self._extract_metadata_value(metadata, 'selector'),
            'template_url': self._extract_metadata_value(metadata, 'templateUrl'),
            'style_urls': self._extract_metadata_value(metadata, 'styleUrls'),
            'change_detection': self._extract_metadata_value(metadata, 'changeDetection'),
            'encapsulation': self._extract_metadata_value(metadata, 'encapsulation')
        }

    def _analyze_inputs(self, content: str) -> List[Dict]:
        """Analyze component inputs"""
        inputs = []
        for match in self.angular_patterns['input'].finditer(content):
            alias, prop_name = match.groups()
            inputs.append({
                'name': prop_name,
                'alias': alias if alias else prop_name,
                'type': self._infer_property_type(content, prop_name),
                'location': match.start()
            })
        return inputs

    def _analyze_outputs(self, content: str) -> List[Dict]:
        """Analyze component outputs"""
        outputs = []
        for match in self.angular_patterns['output'].finditer(content):
            alias, event_name = match.groups()
            outputs.append({
                'name': event_name,
                'alias': alias if alias else event_name,
                'event_type': self._infer_event_type(content, event_name),
                'location': match.start()
            })
        return outputs

    def _analyze_lifecycle_hooks(self, content: str) -> Dict[str, List[Dict]]:
        """Analyze lifecycle hook implementations"""
        hooks = {}
        for match in self.angular_patterns['lifecycle'].finditer(content):
            hook_name = match.group(0).rstrip('(')
            if hook_name not in hooks:
                hooks[hook_name] = []
            
            # Find the hook implementation
            implementation = self._find_method_implementation(content, hook_name)
            if implementation:
                hooks[hook_name].append({
                    'body': implementation,
                    'async': 'async' in implementation,
                    'location': match.start()
                })
        return hooks

    def _analyze_di_patterns(self, content: str) -> Dict[str, Any]:
        """Analyze dependency injection patterns"""
        constructor = re.search(r'constructor\s*\(([^)]+)\)', content)
        if not constructor:
            return {'dependencies': []}

        params = constructor.group(1)
        dependencies = []
        for param in params.split(','):
            param = param.strip()
            if param:
                visibility = 'private' if 'private' in param else 'public'
                type_match = re.search(r':\s*(\w+)', param)
                if type_match:
                    dependencies.append({
                        'type': type_match.group(1),
                        'visibility': visibility,
                        'name': re.search(r'\b\w+\s*:', param).group(0).rstrip(':').strip()
                    })
        
        return {
            'dependencies': dependencies,
            'has_optional': 'Optional' in content,
            'has_self': 'Self' in content,
            'has_skip_self': 'SkipSelf' in content
        }

    def _analyze_http_usage(self, content: str) -> Dict[str, Any]:
        """Analyze HttpClient usage"""
        return {
            'get': len(re.findall(r'\.get\s*\<', content)),
            'post': len(re.findall(r'\.post\s*\<', content)),
            'put': len(re.findall(r'\.put\s*\<', content)),
            'delete': len(re.findall(r'\.delete\s*\<', content)),
            'interceptors': bool(re.search(r'implements\s+HttpInterceptor', content)),
            'error_handling': 'catchError' in content or 'handleError' in content
        }

    def _analyze_observables(self, content: str) -> Dict[str, Any]:
        """Analyze RxJS usage"""
        return {
            'subscriptions': len(re.findall(r'\.subscribe\s*\(', content)),
            'pipes': len(re.findall(r'\.pipe\s*\(', content)),
            'subjects': len(re.findall(r'Subject\<', content)),
            'behavior_subjects': len(re.findall(r'BehaviorSubject\<', content)),
            'replay_subjects': len(re.findall(r'ReplaySubject\<', content)),
            'operators': self._extract_rxjs_operators(content)
        }

    def _analyze_change_detection(self, content: str) -> Dict[str, Any]:
        """Analyze change detection strategy"""
        return {
            'strategy': 'OnPush' if 'ChangeDetectionStrategy.OnPush' in content else 'Default',
            'manual_triggers': len(re.findall(r'\.detectChanges\(\)', content)),
            'async_pipe_usage': len(re.findall(r'\|\s*async', content)),
            'mark_for_check': len(re.findall(r'\.markForCheck\(\)', content))
        }

    def _extract_metadata_value(self, metadata: str, key: str) -> Any:
        """Extract value from component metadata"""
        match = re.search(fr'{key}:\s*([^,}}]+)', metadata)
        if not match:
            return None
        value = match.group(1).strip()
        if value.startswith('[') and value.endswith(']'):
            return [v.strip().strip("'\"") for v in value[1:-1].split(',')]
        return value.strip("'\"")

    def _infer_property_type(self, content: str, prop_name: str) -> str:
        """Infer the type of an input property"""
        type_match = re.search(fr'{prop_name}\s*:\s*([^;{{]+)', content)
        return type_match.group(1).strip() if type_match else 'any'

    def _infer_event_type(self, content: str, event_name: str) -> str:
        """Infer the type of an output event"""
        type_match = re.search(fr'EventEmitter\s*<\s*([^>]+)\s*>', content)
        return type_match.group(1).strip() if type_match else 'any'

    def _find_method_implementation(self, content: str, method_name: str) -> Optional[str]:
        """Find the implementation of a method"""
        match = re.search(fr'{method_name}\s*\([^)]*\)\s*{{([^}}]+)}}', content)
        return match.group(1).strip() if match else None

    def _extract_rxjs_operators(self, content: str) -> Dict[str, int]:
        """Extract RxJS operator usage"""
        common_operators = ['map', 'filter', 'tap', 'catchError', 'switchMap', 
                          'mergeMap', 'concatMap', 'debounceTime', 'distinctUntilChanged']
        operators = {}
        for op in common_operators:
            count = len(re.findall(fr'\b{op}\s*\(', content))
            if count > 0:
                operators[op] = count
        return operators
