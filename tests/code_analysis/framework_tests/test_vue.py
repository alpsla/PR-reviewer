"""Vue.js-specific tests for TypeScript analyzer."""

from .base import BaseFrameworkTest

class VueFrameworkTest(BaseFrameworkTest):
    """Test TypeScript analyzer with Vue.js code."""
    
    framework_name = 'vue'
    
    def test_vue_component_detection(self):
        """Test detection of Vue components."""
        analysis = self.analyze_file('component.vue')
        self.assertFrameworkDetected(analysis, 'vue')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['vue_component'], 0)
        self.assertGreater(framework_analysis['patterns']['vue_template'], 0)
    
    def test_vue_composition_api_detection(self):
        """Test detection of Vue Composition API."""
        analysis = self.analyze_file('composition.ts')
        self.assertFrameworkDetected(analysis, 'vue')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['vue_composition'], 0)
    
    def test_vue_options_api_detection(self):
        """Test detection of Vue Options API."""
        analysis = self.analyze_file('options.ts')
        self.assertFrameworkDetected(analysis, 'vue')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['vue_options'], 0)
