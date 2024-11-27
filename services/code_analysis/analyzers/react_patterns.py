from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import re
from enum import Enum

class ReactPatternType(Enum):
    """Types of React patterns"""
    PERFORMANCE = "performance"
    STATE_MANAGEMENT = "state_management"
    COMPONENT_COMPOSITION = "component_composition"
    ERROR_HANDLING = "error_handling"
    CODE_SPLITTING = "code_splitting"

@dataclass
class ReactPatternInfo:
    """Information about a React pattern"""
    pattern_type: ReactPatternType
    name: str
    implementation: str
    issues: List[str]
    suggestions: List[str]

@dataclass
class ReactHookPattern:
    """Information about a React hook pattern"""
    hook_name: str
    dependencies: List[str]
    cleanup_function: bool
    async_usage: bool
    potential_issues: List[str]

class ReactPatternAnalyzer:
    """Analyzer for modern React patterns and best practices"""

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for React pattern analysis"""
        self.patterns = {
            'performance': {
                'memo': re.compile(r'React\.memo\(([^)]+)\)'),
                'use_callback': re.compile(
                    r'useCallback\(\s*(?:\([^)]*\)\s*=>\s*[^,]+),\s*\[([^\]]*)\]'
                ),
                'use_memo': re.compile(
                    r'useMemo\(\s*\(\)\s*=>\s*([^,]+),\s*\[([^\]]*)\]'
                ),
                'use_transition': re.compile(r'useTransition\(\)'),
                'use_deferred_value': re.compile(r'useDeferredValue\(([^)]+)\)')
            },
            'state_management': {
                'use_reducer': re.compile(r'useReducer\(([^,]+),\s*([^,]+)\)'),
                'use_context': re.compile(r'useContext\(([^)]+)\)'),
                'use_state': re.compile(
                    r'const\s+\[([^,]+),\s*set([^]]+)\]\s*=\s*useState[<(]'
                )
            },
            'error_handling': {
                'error_boundary': re.compile(
                    r'class\s+\w+\s+extends\s+(?:React\.)?Component\s*{[^}]*componentDidCatch'
                ),
                'try_catch': re.compile(r'try\s*{[^}]+}\s*catch\s*\([^)]+\)\s*{'),
                'error_handler': re.compile(r'function\s+\w+ErrorHandler\s*\(')
            },
            'code_splitting': {
                'lazy': re.compile(r'React\.lazy\(\s*\(\)\s*=>\s*import\([^)]+\)\)'),
                'suspense': re.compile(r'<Suspense\b[^>]*>'),
                'dynamic_import': re.compile(r'import\([^)]+\)')
            }
        }

    def analyze_patterns(self, content: str) -> Dict[ReactPatternType, List[ReactPatternInfo]]:
        """Analyze React patterns in the code"""
        patterns = {
            ReactPatternType.PERFORMANCE: self._analyze_performance_patterns(content),
            ReactPatternType.STATE_MANAGEMENT: self._analyze_state_patterns(content),
            ReactPatternType.ERROR_HANDLING: self._analyze_error_patterns(content),
            ReactPatternType.CODE_SPLITTING: self._analyze_code_splitting(content)
        }
        return patterns

    def _analyze_performance_patterns(self, content: str) -> List[ReactPatternInfo]:
        """Analyze performance optimization patterns"""
        patterns = []

        # Analyze memo usage
        memo_matches = self.patterns['performance']['memo'].finditer(content)
        for match in memo_matches:
            component = match.group(1)
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.PERFORMANCE,
                name="React.memo",
                implementation=component,
                issues=self._check_memo_issues(content, component),
                suggestions=self._get_memo_suggestions(content, component)
            ))

        # Analyze useCallback usage
        callback_matches = self.patterns['performance']['use_callback'].finditer(content)
        for match in callback_matches:
            deps = match.group(1)
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.PERFORMANCE,
                name="useCallback",
                implementation="useCallback with deps: " + deps,
                issues=self._check_callback_issues(deps),
                suggestions=self._get_callback_suggestions(deps)
            ))

        return patterns

    def _analyze_state_patterns(self, content: str) -> List[ReactPatternInfo]:
        """Analyze state management patterns"""
        patterns = []

        # Analyze useReducer usage
        reducer_matches = self.patterns['state_management']['use_reducer'].finditer(content)
        for match in reducer_matches:
            reducer, initial = match.groups()
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.STATE_MANAGEMENT,
                name="useReducer",
                implementation=f"Reducer: {reducer}, Initial: {initial}",
                issues=self._check_reducer_issues(content, reducer),
                suggestions=self._get_reducer_suggestions(content, reducer)
            ))

        # Analyze Context usage
        context_matches = self.patterns['state_management']['use_context'].finditer(content)
        for match in context_matches:
            context = match.group(1)
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.STATE_MANAGEMENT,
                name="useContext",
                implementation=f"Context: {context}",
                issues=self._check_context_issues(content, context),
                suggestions=self._get_context_suggestions(content, context)
            ))

        return patterns

    def _analyze_error_patterns(self, content: str) -> List[ReactPatternInfo]:
        """Analyze error handling patterns"""
        patterns = []

        # Analyze Error Boundaries
        if self.patterns['error_handling']['error_boundary'].search(content):
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.ERROR_HANDLING,
                name="ErrorBoundary",
                implementation="Class-based Error Boundary",
                issues=self._check_error_boundary_issues(content),
                suggestions=self._get_error_boundary_suggestions()
            ))

        # Analyze try-catch blocks
        try_catch_matches = self.patterns['error_handling']['try_catch'].finditer(content)
        for match in try_catch_matches:
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.ERROR_HANDLING,
                name="TryCatch",
                implementation="Try-Catch Block",
                issues=self._check_try_catch_issues(content),
                suggestions=self._get_try_catch_suggestions()
            ))

        return patterns

    def _analyze_code_splitting(self, content: str) -> List[ReactPatternInfo]:
        """Analyze code splitting patterns"""
        patterns = []

        # Analyze React.lazy usage
        lazy_matches = self.patterns['code_splitting']['lazy'].finditer(content)
        for match in lazy_matches:
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.CODE_SPLITTING,
                name="React.lazy",
                implementation="Dynamic Import with React.lazy",
                issues=self._check_lazy_loading_issues(content),
                suggestions=self._get_lazy_loading_suggestions()
            ))

        # Analyze Suspense usage
        suspense_matches = self.patterns['code_splitting']['suspense'].finditer(content)
        for match in suspense_matches:
            patterns.append(ReactPatternInfo(
                pattern_type=ReactPatternType.CODE_SPLITTING,
                name="Suspense",
                implementation="Suspense Boundary",
                issues=self._check_suspense_issues(content),
                suggestions=self._get_suspense_suggestions()
            ))

        return patterns

    def _check_memo_issues(self, content: str, component: str) -> List[str]:
        """Check for potential issues with React.memo usage"""
        issues = []
        if re.search(r'useCallback\(.*\[\s*\]', content):
            issues.append("Empty dependency array in useCallback with memo")
        if re.search(r'props\s*=>\s*{[^}]+return', content):
            issues.append("Complex comparison function in memo may impact performance")
        return issues

    def _get_memo_suggestions(self, content: str, component: str) -> List[str]:
        """Get suggestions for React.memo usage"""
        return [
            "Consider using useMemo for expensive computations",
            "Ensure proper dependency arrays in child components",
            "Use React DevTools Profiler to verify performance impact"
        ]

    def _check_callback_issues(self, deps: str) -> List[str]:
        """Check for potential issues with useCallback usage"""
        issues = []
        if not deps.strip():
            issues.append("Empty dependency array in useCallback")
        elif len(deps.split(',')) > 3:
            issues.append("Large number of dependencies may indicate need for restructuring")
        return issues

    def _get_callback_suggestions(self, deps: str) -> List[str]:
        """Get suggestions for useCallback usage"""
        return [
            "Consider moving callback definition outside if no dependencies",
            "Use object destructuring in dependency array",
            "Consider useReducer for complex state updates"
        ]

    def _check_reducer_issues(self, content: str, reducer: str) -> List[str]:
        """Check for potential issues with useReducer usage"""
        issues = []
        if 'useState' in content and 'useReducer' in content:
            issues.append("Mixed usage of useState and useReducer may indicate inconsistent state management")
        return issues

    def _get_reducer_suggestions(self, content: str, reducer: str) -> List[str]:
        """Get suggestions for useReducer usage"""
        return [
            "Consider using TypeScript for better action typing",
            "Implement action creators for complex state updates",
            "Use context with reducer for global state management"
        ]

    def _check_context_issues(self, content: str, context: str) -> List[str]:
        """Check for potential issues with Context usage"""
        issues = []
        if len(re.findall(r'useContext\(', content)) > 3:
            issues.append("Multiple context usage may indicate need for composition")
        return issues

    def _get_context_suggestions(self, content: str, context: str) -> List[str]:
        """Get suggestions for Context usage"""
        return [
            "Consider using context selectors to prevent unnecessary rerenders",
            "Split context by domain for better code organization",
            "Use memo with context consumers for better performance"
        ]

    def _check_error_boundary_issues(self, content: str) -> List[str]:
        """Check for potential issues with Error Boundaries"""
        issues = []
        if not re.search(r'static\s+getDerivedStateFromError', content):
            issues.append("Missing static getDerivedStateFromError method")
        return issues

    def _get_error_boundary_suggestions(self) -> List[str]:
        """Get suggestions for Error Boundaries"""
        return [
            "Implement retry mechanism in error boundary",
            "Add error reporting service integration",
            "Consider using error boundary as a higher-order component"
        ]

    def _check_try_catch_issues(self, content: str) -> List[str]:
        """Check for potential issues with try-catch blocks"""
        issues = []
        if re.search(r'catch\s*\([^)]*\)\s*{\s*}', content):
            issues.append("Empty catch block detected")
        return issues

    def _get_try_catch_suggestions(self) -> List[str]:
        """Get suggestions for try-catch usage"""
        return [
            "Add error logging in catch blocks",
            "Consider using custom error classes",
            "Implement proper error recovery mechanisms"
        ]

    def _check_lazy_loading_issues(self, content: str) -> List[str]:
        """Check for potential issues with lazy loading"""
        issues = []
        if not re.search(r'<Suspense', content):
            issues.append("Lazy loading without Suspense boundary")
        return issues

    def _get_lazy_loading_suggestions(self) -> List[str]:
        """Get suggestions for lazy loading"""
        return [
            "Add retry mechanism for failed imports",
            "Implement loading states in Suspense fallback",
            "Consider using preload pattern for critical components"
        ]

    def _check_suspense_issues(self, content: str) -> List[str]:
        """Check for potential issues with Suspense"""
        issues = []
        if not re.search(r'fallback\s*=\s*{', content):
            issues.append("Suspense without meaningful fallback")
        return issues

    def _get_suspense_suggestions(self) -> List[str]:
        """Get suggestions for Suspense usage"""
        return [
            "Implement skeleton screens in fallback",
            "Consider nested Suspense boundaries",
            "Add error boundaries around Suspense components"
        ]
