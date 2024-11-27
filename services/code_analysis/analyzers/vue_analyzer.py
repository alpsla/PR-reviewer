from typing import Dict, List, Optional, Any
import re
from .typescript_analyzer import TypeScriptAnalyzer

class VueAnalyzer(TypeScriptAnalyzer):
    """Enhanced Vue-specific analyzer building on TypeScript capabilities"""

    def __init__(self):
        super().__init__()
        self._compile_vue_patterns()

    def analyze(self, content: str, filename: str) -> Dict:
        """Main analysis entry point"""
        # Get base TypeScript analysis
        ts_analysis = super().analyze(content, filename)
        
        # Add Vue-specific analysis
        return {
            **ts_analysis,
            'components': self.analyze_components(content),
            'composition': self.analyze_composition_api(content),
            'options': self.analyze_options_api(content),
            'templates': self.analyze_templates(content),
            'performance': self.analyze_performance(content),
            'patterns': self.analyze_vue_patterns(content)
        }

    def analyze_components(self, content: str) -> Dict:
        """Analyze Vue component structure"""
        return {
            'single_file': self._analyze_sfc_structure(content),
            'script_setup': self._analyze_script_setup(content),
            'props': self._analyze_props(content),
            'emits': self._analyze_emits(content),
            'slots': self._analyze_slots(content),
            'lifecycle': self._analyze_lifecycle_hooks(content)
        }

    def analyze_composition_api(self, content: str) -> Dict:
        """Analyze Vue 3 Composition API usage"""
        return {
            'refs': self._analyze_refs(content),
            'reactive': self._analyze_reactive(content),
            'computed': self._analyze_computed(content),
            'watch': self._analyze_watchers(content),
            'provide_inject': self._analyze_provide_inject(content),
            'composables': self._analyze_composables(content)
        }

    def analyze_options_api(self, content: str) -> Dict:
        """Analyze Vue 2 Options API usage"""
        return {
            'data': self._analyze_data_option(content),
            'methods': self._analyze_methods(content),
            'computed_props': self._analyze_computed_properties(content),
            'watchers': self._analyze_watch_options(content),
            'mixins': self._analyze_mixins(content),
            'filters': self._analyze_filters(content)
        }

    def analyze_templates(self, content: str) -> Dict:
        """Analyze Vue template structure and directives"""
        return {
            'directives': self._analyze_directives(content),
            'interpolation': self._analyze_interpolation(content),
            'events': self._analyze_event_handlers(content),
            'bindings': self._analyze_bindings(content),
            'conditionals': self._analyze_conditionals(content),
            'loops': self._analyze_loops(content)
        }

    def analyze_performance(self, content: str) -> Dict:
        """Analyze Vue performance optimizations"""
        return {
            'keep_alive': self._analyze_keep_alive(content),
            'memo': self._analyze_memo_usage(content),
            'v_once': self._analyze_v_once(content),
            'virtual_list': self._analyze_virtual_list(content),
            'dynamic_imports': self._analyze_dynamic_imports(content)
        }

    def analyze_vue_patterns(self, content: str) -> Dict:
        """Analyze Vue-specific patterns and best practices"""
        return {
            'store_usage': self._analyze_store_usage(content),
            'router_usage': self._analyze_router_usage(content),
            'i18n': self._analyze_i18n(content),
            'teleport': self._analyze_teleport(content),
            'suspense': self._analyze_suspense(content)
        }

    def _compile_vue_patterns(self):
        """Compile regex patterns for Vue analysis"""
        self.vue_patterns = {
            'sfc': re.compile(
                r'<template[^>]*>(.*?)</template>.*?<script[^>]*>(.*?)</script>',
                re.DOTALL
            ),
            'script_setup': re.compile(
                r'<script\s+setup[^>]*>(.*?)</script>',
                re.DOTALL
            ),
            'props': re.compile(
                r'props:\s*{([^}]+)}|defineProps\s*\(\s*{([^}]+)}'
            ),
            'emits': re.compile(
                r'emits:\s*{([^}]+)}|defineEmits\s*\(\s*{([^}]+)}'
            ),
            'refs': re.compile(
                r'ref\s*\(\s*([^)]+)\s*\)'
            ),
            'reactive': re.compile(
                r'reactive\s*\(\s*{([^}]+)}\s*\)'
            ),
            'computed': re.compile(
                r'computed\s*\(\s*\(\)\s*=>\s*{([^}]+)}'
            ),
            'watch': re.compile(
                r'watch\s*\(\s*([^,]+),\s*\([^)]*\)\s*=>\s*{([^}]+)}'
            ),
            'lifecycle': re.compile(
                r'on(?:Mounted|Updated|Unmounted|Created)\s*\(\s*\(\)\s*=>\s*{([^}]+)}'
            ),
            'directives': re.compile(
                r'v-(?:if|else|else-if|for|show|bind|model|on)[:\.]'
            )
        }

    def _analyze_sfc_structure(self, content: str) -> Dict[str, Any]:
        """Analyze Single File Component structure"""
        match = self.vue_patterns['sfc'].search(content)
        if not match:
            return {'valid': False}
        
        template, script = match.groups()
        return {
            'valid': True,
            'has_template': bool(template.strip()),
            'has_script': bool(script.strip()),
            'has_style': '<style' in content,
            'scoped_styles': 'scoped' in content
        }

    def _analyze_script_setup(self, content: str) -> Dict[str, Any]:
        """Analyze script setup syntax"""
        match = self.vue_patterns['script_setup'].search(content)
        if not match:
            return {'used': False}
        
        setup_content = match.group(1)
        return {
            'used': True,
            'typescript': 'lang="ts"' in content,
            'imports': self._analyze_imports(setup_content),
            'top_level_await': 'await' in setup_content
        }

    def _analyze_refs(self, content: str) -> List[Dict]:
        """Analyze ref declarations"""
        refs = []
        for match in self.vue_patterns['refs'].finditer(content):
            value = match.group(1)
            refs.append({
                'value': value.strip(),
                'type': self._infer_ref_type(value),
                'location': match.start()
            })
        return refs

    def _analyze_reactive(self, content: str) -> List[Dict]:
        """Analyze reactive state"""
        reactive_states = []
        for match in self.vue_patterns['reactive'].finditer(content):
            state = match.group(1)
            reactive_states.append({
                'properties': self._parse_object_properties(state),
                'location': match.start()
            })
        return reactive_states

    def _analyze_computed(self, content: str) -> List[Dict]:
        """Analyze computed properties"""
        computed_props = []
        for match in self.vue_patterns['computed'].finditer(content):
            body = match.group(1)
            computed_props.append({
                'body': body.strip(),
                'dependencies': self._extract_dependencies(body),
                'location': match.start()
            })
        return computed_props

    def _analyze_watchers(self, content: str) -> List[Dict]:
        """Analyze watchers"""
        watchers = []
        for match in self.vue_patterns['watch'].finditer(content):
            source, callback = match.groups()
            watchers.append({
                'source': source.strip(),
                'callback': callback.strip(),
                'immediate': 'immediate: true' in content,
                'deep': 'deep: true' in content,
                'location': match.start()
            })
        return watchers

    def _analyze_lifecycle_hooks(self, content: str) -> Dict[str, List[Dict]]:
        """Analyze lifecycle hooks"""
        hooks = {}
        for match in self.vue_patterns['lifecycle'].finditer(content):
            hook_name = match.re.pattern.split(r'\(')[0]
            body = match.group(1)
            if hook_name not in hooks:
                hooks[hook_name] = []
            hooks[hook_name].append({
                'body': body.strip(),
                'async': 'async' in body,
                'location': match.start()
            })
        return hooks

    def _analyze_directives(self, content: str) -> Dict[str, int]:
        """Analyze directive usage"""
        directives = {}
        for match in self.vue_patterns['directives'].finditer(content):
            directive = match.group(0)
            directives[directive] = directives.get(directive, 0) + 1
        return directives

    def _infer_ref_type(self, value: str) -> str:
        """Infer the type of a ref value"""
        if value.isdigit():
            return 'number'
        if value.lower() in ['true', 'false']:
            return 'boolean'
        if value.startswith('"') or value.startswith("'"):
            return 'string'
        if value.startswith('['):
            return 'array'
        if value.startswith('{'):
            return 'object'
        return 'unknown'

    def _parse_object_properties(self, obj_str: str) -> Dict[str, str]:
        """Parse object properties and their types"""
        properties = {}
        prop_matches = re.finditer(r'(\w+):\s*([^,}]+)', obj_str)
        for match in prop_matches:
            name, value = match.groups()
            properties[name.strip()] = self._infer_ref_type(value.strip())
        return properties

    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract reactive dependencies from code"""
        deps = []
        ref_matches = re.finditer(r'(\w+)\.value', code)
        for match in ref_matches:
            deps.append(match.group(1))
        return list(set(deps))
