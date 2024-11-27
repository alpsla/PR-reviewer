import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import json
from services.code_analysis.analyzers.typescript_analyzer import (
    TypeScriptAnalyzer, TypeMetrics, DocumentationMetrics, 
    FrameworkMetrics, TypeAnalysis, DocumentationAnalysis,
    FrameworkAnalysis, AnalysisOutput
)

class TestTypeScriptAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Set up logging for tests
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize logging with test configuration
        from logging_config import setup_logging
        setup_logging(
            component="typescript_analyzer_test",
            log_level="DEBUG",
            max_bytes=1024 * 1024,  # 1MB
            backup_count=3,
            log_to_console=True
        )
    
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()
        self.test_dir = os.path.join(os.path.dirname(__file__), '..', 'test_files', 'typescript')
        
        # Ensure test directory exists
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create test files
        self.create_test_files()
        
        # Verify files were created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'types.d.ts')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'component.tsx')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'component.test.tsx')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'advanced-types.ts')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'documentation.ts')))
    
    def create_test_files(self):
        """Create test files with different types."""
        files = {
            'types.d.ts': """
                // Type definitions for test module
                declare module 'test-module' {
                    export interface User {
                        id: number;
                        name: string;
                        email: string;
                    }
                    
                    export type UserRole = 'admin' | 'user' | 'guest';
                    export type PartialUser = Partial<User>;
                    
                    declare namespace Auth {
                        interface Credentials {
                            username: string;
                            password: string;
                        }
                        
                        type AuthResponse = {
                            token: string;
                            expires: Date;
                        }
                        
                        export function login(creds: Credentials): Promise<AuthResponse>;
                    }
                }
            """,
            'component.tsx': """
                import { User, UserRole, PartialUser } from 'test-module';
                
                // Type guard for admin check
                function isAdmin(user: unknown): user is { role: 'admin' } {
                    return typeof user === 'object' && user !== null && 'role' in user && user.role === 'admin';
                }
                
                // Mapped type for user permissions
                type UserPermissions = {
                    [K in UserRole]: boolean;
                }
                
                // Conditional type for admin-only properties
                type AdminProperties<T> = T extends { role: 'admin' } ? T & { adminSince: Date } : never;
                
                // Utility types
                type ReadonlyUser = Readonly<User>;
                type UserKeys = Pick<User, 'id' | 'name'>;
                
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
                import { User, UserRole } from 'test-module';
                import { UserComponent } from './component';
                
                describe('UserComponent', () => {
                    interface TestUser extends User {
                        role: UserRole;
                    }
                    
                    const createTestUser = (): TestUser => ({
                        id: 1,
                        name: 'Test User',
                        email: 'test@example.com',
                        role: 'user'
                    });
                    
                    it('renders user information', () => {
                        const user = createTestUser();
                        render(<UserComponent user={user} role={user.role} />);
                        expect(screen.getByText('Test User')).toBeInTheDocument();
                    });
                });
            """,
            'advanced-types.ts': """
                // Advanced TypeScript type features
                
                // Mapped types
                type Nullable<T> = { [P in keyof T]: T[P] | null };
                type ReadonlyRecord<K extends keyof any, T> = { readonly [P in K]: T };
                
                // Conditional types
                type NonNullable<T> = T extends null | undefined ? never : T;
                type ReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any;
                
                // Template literal types
                type EventName = `on${Capitalize<string>}`;
                type CSSProperty = `${string}-${string}`;
                
                // Utility types usage
                type Props = {
                    name: string;
                    age: number;
                    email: string;
                };
                
                type PartialProps = Partial<Props>;
                type RequiredProps = Required<Props>;
                type ReadonlyProps = Readonly<Props>;
                type PickedProps = Pick<Props, 'name' | 'age'>;
                type OmittedProps = Omit<Props, 'email'>;
                
                // Type assertions and guards
                function isString(value: unknown): value is string {
                    return typeof value === 'string';
                }
                
                const value = 'test' as const;
                const num = 42 as number;
            """,
            'documentation.ts': """
                /**
                 * Represents a user in the system
                 * @interface
                 */
                interface User {
                    /** Unique identifier for the user */
                    id: number;
                    /** User's full name */
                    name: string;
                    /** User's email address */
                    email: string;
                }
                
                /**
                 * Service for managing users
                 * @class
                 */
                class UserService {
                    /**
                     * Creates a new user
                     * @param {User} user - The user to create
                     * @returns {Promise<User>} The created user
                     */
                    async createUser(user: User): Promise<User> {
                        return user;
                    }
                    
                    /**
                     * Updates an existing user
                     * @param {number} id - The user ID
                     * @param {Partial<User>} updates - The updates to apply
                     * @returns {Promise<User>} The updated user
                     */
                    async updateUser(id: number, updates: Partial<User>): Promise<User> {
                        return { id, ...updates } as User;
                    }
                }
            """
        }
        
        for filename, content in files.items():
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content.strip())
    
    def tearDown(self):
        """Clean up test files."""
        try:
            import shutil
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Error cleaning up test files: {e}")
    
    def test_analyze_directory(self):
        """Test analyzing a directory of TypeScript files."""
        # Verify test files exist
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'types.d.ts')))
        
        # Run analysis
        analysis = self.analyzer.analyze_directory(self.test_dir)
        
        # Check that files were analyzed
        self.assertIsNotNone(analysis)
        self.assertIsInstance(analysis, dict)
        
        # Check type analysis results
        type_analysis = analysis.get('type_analysis', {})
        self.assertIsInstance(type_analysis, dict)
        
        metrics = type_analysis.get('metrics', {})
        self.assertGreater(metrics.get('total_declarations', 0), 0)
        self.assertGreater(metrics.get('interfaces', 0), 0)
        self.assertGreater(metrics.get('type_aliases', 0), 0)
        self.assertGreater(metrics.get('type_coverage', 0), 80)
        self.assertEqual(metrics.get('declaration_file_coverage', 0), 100)
    
    def test_analyze_files_by_type(self):
        """Test analyzing files grouped by type."""
        # Verify test files exist
        self.assertTrue(os.path.exists(self.test_dir))
        
        # Get all files
        files = []
        for filename in os.listdir(self.test_dir):
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                files.append({
                    'path': filename,
                    'content': f.read()
                })
        
        # Run analysis
        analysis = self.analyzer.analyze_files(files).to_dict()
        
        # Check metrics for each file type
        metrics = analysis.get('type_analysis', {}).get('metrics', {})
        
        # Declaration file metrics
        self.assertEqual(metrics.get('declaration_file_coverage', 0), 100)
        self.assertEqual(metrics.get('declaration_any_types', 0), 0)
        
        # Test file metrics
        self.assertGreater(metrics.get('test_file_coverage', 0), 0)
        self.assertLessEqual(metrics.get('test_assertions', 0), 10)
        
        # Implementation file metrics
        self.assertGreater(metrics.get('implementation_coverage', 0), 80)
        self.assertLessEqual(metrics.get('implementation_any_types', 0), 5)
    
    def test_advanced_type_features(self):
        """Test analyzing advanced TypeScript type features."""
        filepath = os.path.join(self.test_dir, 'advanced-types.ts')
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = self.analyzer.analyze_files([{'path': 'advanced-types.ts', 'content': content}]).to_dict()
        metrics = analysis.get('type_analysis', {}).get('metrics', {})
        
        # Check advanced type metrics
        self.assertGreater(metrics.get('mapped_types', 0), 0, "Should detect mapped types")
        self.assertGreater(metrics.get('conditional_types', 0), 0, "Should detect conditional types")
        self.assertGreater(metrics.get('utility_types', 0), 0, "Should detect utility type usage")
        self.assertGreater(metrics.get('type_assertions', 0), 0, "Should detect type assertions")
        self.assertGreater(metrics.get('type_guards', 0), 0, "Should detect type guards")
    
    def test_documentation_analysis(self):
        """Test analyzing TypeScript documentation."""
        filepath = os.path.join(self.test_dir, 'documentation.ts')
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = self.analyzer.analyze_files([{'path': 'documentation.ts', 'content': content}]).to_dict()
        doc_metrics = analysis.get('doc_analysis', {}).get('metrics', {})
        
        # Check documentation metrics
        self.assertGreater(doc_metrics.get('coverage', 0), 80, "Should have good documentation coverage")
        self.assertGreater(doc_metrics.get('param_docs', 0), 0, "Should detect parameter documentation")
        self.assertGreater(doc_metrics.get('return_docs', 0), 0, "Should detect return type documentation")
        self.assertGreater(doc_metrics.get('interface_docs', 0), 0, "Should detect interface documentation")
        self.assertGreater(doc_metrics.get('class_docs', 0), 0, "Should detect class documentation")
    
    def test_type_coverage_calculation(self):
        """Test type coverage calculation for different scenarios."""
        test_cases = [
            {
                'name': 'fully_typed.ts',
                'content': """
                    interface User { id: number; name: string; }
                    const user: User = { id: 1, name: 'Test' };
                    function greet(user: User): string {
                        return `Hello ${user.name}`;
                    }
                """,
                'expected_coverage': 100
            },
            {
                'name': 'partially_typed.ts',
                'content': """
                    interface User { id: number; name: string; }
                    const user = { id: 1, name: 'Test' };
                    function greet(user) {
                        return `Hello ${user.name}`;
                    }
                """,
                'expected_coverage': 50
            },
            {
                'name': 'untyped.ts',
                'content': """
                    const user = { id: 1, name: 'Test' };
                    function greet(user) {
                        return `Hello ${user.name}`;
                    }
                """,
                'expected_coverage': 0
            }
        ]
        
        for test_case in test_cases:
            analysis = self.analyzer.analyze_files([{
                'path': test_case['name'],
                'content': test_case['content']
            }]).to_dict()
            
            metrics = analysis.get('type_analysis', {}).get('metrics', {})
            self.assertAlmostEqual(
                metrics.get('type_coverage', 0),
                test_case['expected_coverage'],
                delta=5,  # Allow 5% margin of error
                msg=f"Type coverage for {test_case['name']} should be ~{test_case['expected_coverage']}%"
            )

if __name__ == '__main__':
    unittest.main()
