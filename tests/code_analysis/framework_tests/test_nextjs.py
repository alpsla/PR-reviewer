"""Next.js-specific tests for TypeScript analyzer."""

from .base import BaseFrameworkTest

class NextJSFrameworkTest(BaseFrameworkTest):
    """Test TypeScript analyzer with Next.js code."""
    
    framework_name = 'nextjs'
    
    def test_nextjs_page_detection(self):
        """Test detection of Next.js pages."""
        analysis = self.analyze_file('page.tsx')
        self.assertFrameworkDetected(analysis, 'nextjs')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['nextjs_page'], 0)
    
    def test_nextjs_api_detection(self):
        """Test detection of Next.js API routes."""
        analysis = self.analyze_file('api.ts')
        self.assertFrameworkDetected(analysis, 'nextjs')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['nextjs_api'], 0)
    
    def test_nextjs_data_fetching_detection(self):
        """Test detection of Next.js data fetching methods."""
        analysis = self.analyze_file('data.tsx')
        self.assertFrameworkDetected(analysis, 'nextjs')
        
        framework_analysis = analysis['framework_analysis']
        self.assertTrue(
            framework_analysis['patterns']['nextjs_getServerSideProps'] > 0 or
            framework_analysis['patterns']['nextjs_getStaticProps'] > 0
        )
