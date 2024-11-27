import unittest
from pathlib import Path
from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer

class TestTypeScriptAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()
        self.test_file = Path(__file__).parent / 'test_files' / 'typescript' / 'test_analyzer.ts'
        with open(self.test_file, 'r') as f:
            self.test_content = f.read()

    def test_type_system_analysis(self):
        """Test type system analysis capabilities"""
        result = self.analyzer.analyze_file(self.test_content, str(self.test_file))
        
        # Check type metrics
        type_metrics = result.type_analysis
        self.assertGreaterEqual(type_metrics.metrics.utility_types, 0)
        self.assertGreaterEqual(type_metrics.metrics.mapped_types, 0)
        self.assertGreaterEqual(type_metrics.metrics.type_guards, 0)
        
        # Check for code samples
        self.assertTrue(type_metrics.code_samples)
        
        # Check for suggestions
        self.assertTrue(isinstance(type_metrics.suggestions, list))

    def test_documentation_analysis(self):
        """Test documentation analysis capabilities"""
        result = self.analyzer.analyze_file(self.test_content, str(self.test_file))
        
        # Check documentation metrics
        doc_metrics = result.doc_analysis
        self.assertGreaterEqual(doc_metrics.metrics.coverage, 0)
        self.assertGreaterEqual(doc_metrics.metrics.jsdoc_coverage, 0)
        self.assertGreaterEqual(doc_metrics.metrics.param_docs, 0)
        
        # Check for documentation suggestions
        self.assertTrue(isinstance(doc_metrics.quality_improvements, list))

    def test_quality_score(self):
        """Test quality score calculation"""
        result = self.analyzer.analyze_file(self.test_content, str(self.test_file))
        
        # Verify quality score is between 0 and 100
        self.assertGreaterEqual(result.quality_score, 0)
        self.assertLessEqual(result.quality_score, 100)

    def test_pattern_analysis(self):
        """Test code pattern analysis capabilities"""
        result = self.analyzer.analyze_file(self.test_content, str(self.test_file))
        
        # Check type patterns
        type_metrics = result.type_analysis
        self.assertGreaterEqual(type_metrics.metrics.utility_types, 0)
        self.assertGreaterEqual(type_metrics.metrics.mapped_types, 0)
        self.assertGreaterEqual(type_metrics.metrics.type_guards, 0)
        
        # Check for code samples
        self.assertTrue(type_metrics.code_samples)
        
        # Check for suggestions
        self.assertTrue(isinstance(type_metrics.suggestions, list))

    def test_framework_detection(self):
        """Test framework detection capabilities"""
        result = self.analyzer.analyze_file(self.test_content, str(self.test_file))
        
        if result.framework_analysis:
            # If framework is detected, verify its properties
            self.assertTrue(hasattr(result.framework_analysis, 'framework'))
            self.assertTrue(hasattr(result.framework_analysis, 'patterns'))
            self.assertTrue(hasattr(result.framework_analysis, 'suggestions'))
            
            # Check that patterns and suggestions are properly structured
            self.assertIsInstance(result.framework_analysis.patterns, dict)
            self.assertIsInstance(result.framework_analysis.suggestions, list)

    def test_suggestions_format(self):
        """Test that suggestions are properly formatted"""
        result = self.analyzer.analyze_file(self.test_content, str(self.test_file))
        
        # Check type analysis suggestions
        for suggestion in result.type_analysis.suggestions:
            self.assertIsInstance(suggestion, str)
            self.assertTrue(len(suggestion) > 0)
        
        # Check documentation suggestions
        for suggestion in result.doc_analysis.quality_improvements:
            self.assertIsInstance(suggestion, str)
            self.assertTrue(len(suggestion) > 0)

if __name__ == '__main__':
    unittest.main()
