import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import os
from services.code_analysis.collectors.typescript_collector import (
    TypeScriptCollector,
    TypeScriptCollectorConfig,
    CollectorContext
)

class TestTypeScriptCollector(unittest.TestCase):
    def setUp(self):
        self.config = TypeScriptCollectorConfig(
            min_type_coverage=0.8,
            min_doc_coverage=0.7,
            framework_check=True,
            temp_dir=os.path.join(os.path.dirname(__file__), '..', 'test_files', 'typescript_temp')
        )
        self.collector = TypeScriptCollector(self.config)
        self.context = CollectorContext(
            repository_url="https://github.com/test/repo",
            base_branch="main"
        )
        
        # Create temp directory
        os.makedirs(self.config.temp_dir, exist_ok=True)
        
        # Create test files
        self.create_test_files()
    
    def create_test_files(self):
        """Create test files in the temp directory."""
        files = {
            'types.d.ts': """
                declare module 'test-module' {
                    interface User {
                        id: number;
                        name: string;
                        email: string;
                    }
                    
                    type UserRole = 'admin' | 'user' | 'guest';
                    export type { User, UserRole };
                }
            """,
            'component.tsx': """
                import { User, UserRole } from 'test-module';
                
                type PartialUser = Partial<User>;
                
                function isAdmin(user: unknown): user is { role: 'admin' } {
                    return typeof user === 'object' && user !== null && 'role' in user && user.role === 'admin';
                }
                
                /**
                 * User component that displays user information
                 * @param props - The component props
                 * @returns JSX element
                 */
                export const UserComponent: React.FC<{user: User; role: UserRole}> = ({user, role}) => {
                    const userInfo = user as PartialUser;
                    
                    return (
                        <div>
                            <h1>{userInfo.name}</h1>
                            <p>{userInfo.email}</p>
                            {isAdmin(user) && <AdminPanel />}
                        </div>
                    );
                };
            """,
            'component.test.tsx': """
                import { render, screen } from '@testing-library/react';
                import { UserComponent } from './component';
                
                describe('UserComponent', () => {
                    it('renders user information', () => {
                        const user = {
                            id: 1,
                            name: 'Test User',
                            email: 'test@example.com'
                        };
                        
                        render(<UserComponent user={user} role="user" />);
                        expect(screen.getByText('Test User')).toBeInTheDocument();
                    });
                });
            """
        }
        
        for filename, content in files.items():
            filepath = os.path.join(self.config.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content.strip())
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.config.temp_dir):
            shutil.rmtree(self.config.temp_dir)
    
    @patch('services.code_analysis.collectors.typescript_collector.TypeScriptAnalyzer')
    async def test_collect_project(self, mock_analyzer):
        """Test project-wide collection with local files."""
        # Mock the download repository method
        async def mock_download(*args):
            return self.config.temp_dir
        
        self.collector._download_repository = mock_download
        
        # Call collect
        result = await self.collector.collect(self.context)
        
        # Check result structure
        self.assertIn('analysis', result)
        self.assertIn('metrics', result)
        self.assertIn('recommendations', result)
        self.assertIn('quality_score', result)
        self.assertIn('report', result)
        
        # Check metrics
        metrics = result.get('metrics', {})
        self.assertGreater(metrics.get('type_coverage', 0), 80)
        self.assertGreater(metrics.get('documentation_coverage', 0), 70)
        
        # Check file type metrics
        type_metrics = result.get('analysis', {}).get('type_analysis', {}).get('metrics', {})
        self.assertEqual(type_metrics.get('declaration_file_coverage', 0), 100)
        self.assertGreater(type_metrics.get('implementation_coverage', 0), 80)
        self.assertGreater(type_metrics.get('test_file_coverage', 0), 0)
    
    @patch('services.code_analysis.collectors.typescript_collector.TypeScriptAnalyzer')
    async def test_collect_pr_diff(self, mock_analyzer):
        """Test PR diff collection with local files."""
        # Set up PR context
        pr_context = CollectorContext(
            repository_url="https://github.com/test/repo",
            base_branch="main",
            pr_number=123,
            diff_only=True
        )
        
        # Mock the download repository method
        async def mock_download(*args):
            return self.config.temp_dir
        
        self.collector._download_repository = mock_download
        
        # Call collect_diff
        result = await self.collector.collect_diff(pr_context)
        
        # Check result structure
        self.assertIn('analysis', result)
        self.assertIn('base_analysis', result)
        self.assertIn('metrics', result)
        self.assertIn('recommendations', result)
        self.assertIn('quality_score', result)
        self.assertIn('report', result)
        
        # Check metrics
        metrics = result.get('metrics', {})
        self.assertGreater(metrics.get('type_coverage', 0), 80)
        self.assertGreater(metrics.get('documentation_coverage', 0), 70)
        
        # Check file type metrics
        type_metrics = result.get('analysis', {}).get('type_analysis', {}).get('metrics', {})
        self.assertEqual(type_metrics.get('declaration_file_coverage', 0), 100)
        self.assertGreater(type_metrics.get('implementation_coverage', 0), 80)
        self.assertGreater(type_metrics.get('test_file_coverage', 0), 0)
    
    def test_get_metrics(self):
        """Test metrics calculation"""
        self.collector.last_analysis = {
            'type_analysis': {'coverage': 0.9},
            'documentation_analysis': {'metrics': {'coverage': 0.8}},
            'summary': {
                'complexity_score': 0.85,
                'error_handling_score': 0.7,
                'best_practices_score': 0.75
            },
            'framework_analysis': {'metrics': {'framework_score': 0.8}}
        }
        
        metrics = self.collector.get_metrics()
        
        self.assertEqual(metrics['type_coverage'], 0.9)
        self.assertEqual(metrics['documentation_coverage'], 0.8)
        self.assertEqual(metrics['complexity_score'], 0.85)
        self.assertEqual(metrics['framework_score'], 0.8)
    
    def test_get_recommendations(self):
        """Test recommendations generation"""
        self.collector.last_analysis = {
            'type_analysis': {
                'coverage': 0.7,  # Below threshold
                'suggestions': ['Add type annotations']
            },
            'documentation_analysis': {
                'metrics': {'coverage': 0.6},  # Below threshold
                'suggestions': ['Add JSDoc comments']
            },
            'framework_analysis': {
                'suggestions': ['Use React hooks properly']
            }
        }
        
        recommendations = self.collector.get_recommendations()
        
        self.assertEqual(len(recommendations), 3)
        self.assertTrue(any(r['category'] == 'type_safety' for r in recommendations))
        self.assertTrue(any(r['category'] == 'documentation' for r in recommendations))
        self.assertTrue(any(r['category'] == 'framework' for r in recommendations))
    
    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        self.collector.last_analysis = {
            'type_analysis': {'coverage': 0.9},
            'documentation_analysis': {'metrics': {'coverage': 0.8}},
            'summary': {
                'complexity_score': 0.85,
                'error_handling_score': 0.7,
                'best_practices_score': 0.75
            },
            'framework_analysis': {'metrics': {'framework_score': 0.8}}
        }
        
        score = self.collector.get_quality_score()
        
        self.assertGreater(score, 75)  # Good quality score
        self.assertLessEqual(score, 100)  # Score should not exceed 100
    
    def test_empty_analysis(self):
        """Test handling of empty analysis"""
        self.collector.last_analysis = None
        
        self.assertEqual(self.collector.get_metrics(), {})
        self.assertEqual(self.collector.get_recommendations(), [])
        self.assertEqual(self.collector.get_quality_score(), 0.0)

def run_async_test(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

if __name__ == '__main__':
    unittest.main()
