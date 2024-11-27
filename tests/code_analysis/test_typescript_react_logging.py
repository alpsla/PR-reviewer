import unittest
import logging
import os
from services.code_analysis.analyzers.typescript_react_analyzer import TypeScriptReactAnalyzer
from logging_config import setup_logging

class TestTypeScriptReactLogging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Set up logging for tests
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize logging with test configuration
        setup_logging(
            component="typescript_react_test",
            log_level="DEBUG",
            max_bytes=1024 * 1024,  # 1MB
            backup_count=3,
            log_to_console=True
        )

    def setUp(self):
        self.analyzer = TypeScriptReactAnalyzer()
        
    def test_react_component_analysis(self):
        # Sample React component with hooks and JSX
        react_code = '''
        const CounterComponent = () => {
            const [count, setCount] = React.useState(0);
            const [name, setName] = React.useState("User");
            
            React.useEffect(() => {
                console.log(`Count changed to ${count}`);
            }, [count]);
            
            return (
                <div className="counter">
                    <h1>Hello, {name}!</h1>
                    <p>Count: {count}</p>
                    <button onClick={() => setCount(count + 1)}>
                        Increment
                    </button>
                </div>
            );
        };
        '''
        
        # Analyze the code and generate logs
        analysis_result = self.analyzer.analyze_file(react_code, "test_component.tsx")
        
        # Basic assertions to ensure analysis worked
        self.assertIsNotNone(analysis_result)
        
        # Convert to dictionary for easier assertions
        result_dict = analysis_result.to_dict()
        
        # Verify framework analysis
        framework_analysis = result_dict.get('framework_analysis', {})
        self.assertEqual(framework_analysis.get('framework'), 'react')
        
        # Get patterns from framework analysis
        patterns = framework_analysis.get('patterns', {})
        
        # Verify hooks usage
        hooks_usage = patterns.get('hooks_usage', {})
        self.assertGreaterEqual(hooks_usage.get('useState', 0), 2)  # Should find 2 useState hooks
        self.assertGreaterEqual(hooks_usage.get('useEffect', 0), 1)  # Should find 1 useEffect hook
        
        # Verify JSX usage
        jsx_usage = patterns.get('jsx_usage', {})
        self.assertGreaterEqual(jsx_usage.get('elements', 0), 1)  # Should find at least 1 JSX element
        
        # Verify component detection
        components = patterns.get('components', {})
        self.assertGreaterEqual(components.get('functional', 0), 1)  # Should find 1 functional component
        
        # Check logs directory for React analyzer logs
        logging.info("Test completed successfully", 
                        extra={
                            "hooks_found": hooks_usage,
                            "jsx_elements": jsx_usage.get('elements', 0),
                            "components": components
                        })
        
        return result_dict

if __name__ == '__main__':
    unittest.main()
