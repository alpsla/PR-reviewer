"""Angular-specific tests for TypeScript analyzer."""

from .base import BaseFrameworkTest

class AngularFrameworkTest(BaseFrameworkTest):
    """Test TypeScript analyzer with Angular code."""
    
    framework_name = 'angular'
    
    def test_angular_component_detection(self):
        """Test detection of Angular components."""
        analysis = self.analyze_file('component.ts')
        self.assertFrameworkDetected(analysis, 'angular')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['angular_component'], 0)
    
    def test_angular_service_detection(self):
        """Test detection of Angular services."""
        analysis = self.analyze_file('service.ts')
        self.assertFrameworkDetected(analysis, 'angular')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['angular_service'], 0)
    
    def test_angular_directive_detection(self):
        """Test detection of Angular directives."""
        analysis = self.analyze_file('directive.ts')
        self.assertFrameworkDetected(analysis, 'angular')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['angular_directive'], 0)
    
    def test_angular_module_detection(self):
        """Test detection of Angular modules."""
        analysis = self.analyze_file('module.ts')
        self.assertFrameworkDetected(analysis, 'angular')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['angular_module'], 0)
