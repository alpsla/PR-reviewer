# TypeScript Code Quality Report

## Executive Summary
Overall Project Health: {{ health }}% {{ health_icon }}

### Key Metrics
├── Type Safety: {{ type_safety }}% {{ type_safety_icon }}
├── Documentation: {{ documentation }}% {{ documentation_icon }}
└── Code Quality: {{ code_quality }}% {{ code_quality_icon }}

### Trend (Last 30 days)
├── Type Safety: {{ type_safety_trend }}
├── Documentation: {{ documentation_trend }}
└── Code Quality: {{ code_quality_trend }}

## Quality Gates Status
{% for gate in quality_gates %}
├── {{ gate.name }}: {{ gate.threshold }}% > {{ gate.actual }}% {{ gate.status_icon }} {{ gate.trend_icon }}
{% endfor %}
└── Overall Status: {{ quality_gates_status }}

## Type System Analysis
### Distribution
{% for type, percentage in type_distribution.items() %}
├── {{ type }}: {{ percentage }}%
{% endfor %}

### Framework-Specific Types
{% for framework, count in framework_specific_types.items() %}
├── {{ framework }}: {{ count }}
{% endfor %}

### Type Complexity
{% for metric, value in type_complexity.items() %}
├── {{ metric }}: {{ value }}
{% endfor %}

## Documentation Coverage
### Overall: {{ doc_coverage }}%
├── Public API Coverage: {{ public_api_coverage }}%
├── Private API Coverage: {{ private_api_coverage }}%
└── Examples Quality: {{ examples_quality }}%

### Coverage by Complexity
{% for complexity, coverage in complexity_coverage.items() %}
├── {{ complexity }}: {{ coverage }}%
{% endfor %}

## File-Level Analysis
{% for file in file_analysis %}
### {{ file.filename }}
├── Type Coverage: {{ file.metrics.type_coverage }}%
├── Doc Coverage: {{ file.metrics.doc_coverage }}%
└── Code Quality: {{ file.metrics.code_quality }}%

#### Strengths
{% for strength in file.strengths %}
- {{ strength }}
{% endfor %}

#### Issues
{% for issue in file.issues %}
- {{ issue.description }} ({{ issue.severity }})
{% endfor %}

#### Recommendations
{% for rec in file.recommendations %}
- {{ rec }}
{% endfor %}
{% endfor %}

## Priority Actions
### Critical (Next Sprint)
{% for action in priority_actions.critical %}
- {{ action }}
{% endfor %}

### High (Next Month)
{% for action in priority_actions.high %}
- {{ action }}
{% endfor %}

### Medium (Next Quarter)
{% for action in priority_actions.medium %}
- {{ action }}
{% endfor %}

## Monitoring Plan
### Daily Checks
{% for check in monitoring_plan.daily %}
- {{ check }}
{% endfor %}

### Weekly Reviews
{% for review in monitoring_plan.weekly %}
- {{ review }}
{% endfor %}

### Monthly Audits
{% for audit in monitoring_plan.monthly %}
- {{ audit }}
{% endfor %}

## Critical Issues
{% for issue in critical_issues %}
### {{ issue.type }}
- File: {{ issue.file }}
- Line: {{ issue.line }}
- Code: `{{ issue.code }}`
- Suggestion: {{ issue.suggestion }}
{% endfor %}
