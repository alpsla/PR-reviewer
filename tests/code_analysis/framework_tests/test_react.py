"""React-specific tests for TypeScript analyzer."""

import os
from .base import BaseFrameworkTest

class ReactFrameworkTest(BaseFrameworkTest):
    """Test TypeScript analyzer with React code."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.test_files = {
            'component.tsx': """
                import { User, UserRole, PartialUser } from 'test-module';
                import React, { useState, useEffect, useCallback } from 'react';
                
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
                 * Custom hook for user authentication
                 * @param userId - The user ID to authenticate
                 * @returns The authenticated user and loading state
                 */
                function useAuth(userId: string) {
                    const [user, setUser] = useState<User | null>(null);
                    const [loading, setLoading] = useState(true);
                    
                    useEffect(() => {
                        async function loadUser() {
                            setLoading(true);
                            const userData = await fetchUser(userId);
                            setUser(userData);
                            setLoading(false);
                        }
                        loadUser();
                    }, [userId]);
                    
                    return { user, loading };
                }
                
                interface Props {
                    /** The user object */
                    user: User;
                    /** The user's role */
                    role: UserRole;
                    /** Optional callback when user is updated */
                    onUpdate?: (user: User) => void;
                }
                
                /**
                 * User component that displays user information
                 * @param props - The component props
                 * @returns JSX element
                 */
                export const UserComponent: React.FC<Props> = ({user, role, onUpdate}) => {
                    const [isEditing, setIsEditing] = useState(false);
                    const userInfo = user as PartialUser;
                    
                    const handleUpdate = useCallback(() => {
                        if (onUpdate) {
                            onUpdate(user);
                        }
                        setIsEditing(false);
                    }, [user, onUpdate]);
                    
                    return (
                        <div className="user-component">
                            <h1>{userInfo.name}</h1>
                            <p>{userInfo.email}</p>
                            {isAdmin(user) && <AdminPanel />}
                            <button onClick={() => setIsEditing(!isEditing)}>
                                {isEditing ? 'Cancel' : 'Edit'}
                            </button>
                            {isEditing && (
                                <button onClick={handleUpdate}>Save</button>
                            )}
                        </div>
                    );
                };
            """,
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
            """
        }
        
        # Create test files
        for filename, content in self.test_files.items():
            filepath = os.path.join(self.framework_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def test_react_component_detection(self):
        """Test detection of React components."""
        analysis = self.analyze_file('component.tsx')
        self.assertFrameworkDetected(analysis, 'react')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['react_component'], 0)
        self.assertGreater(framework_analysis['patterns']['react_jsx'], 0)
    
    def test_type_definitions(self):
        """Test analysis of React type definitions."""
        analysis = self.analyze_file('types.d.ts')
        
        # Verify type analysis results
        self.assertIsInstance(analysis, dict)
        self.assertIn('type_analysis', analysis)
        type_analysis = analysis['type_analysis']
        
        # Check for type declarations
        self.assertIn('metrics', type_analysis)
        metrics = type_analysis['metrics']
        self.assertGreater(metrics['total_declarations'], 0)
        self.assertEqual(metrics['type_coverage'], 100.0)
        self.assertGreater(metrics['interfaces'], 0)

    def test_react_hooks_detection(self):
        """Test detection of React hooks."""
        analysis = self.analyze_file('component.tsx')
        self.assertFrameworkDetected(analysis, 'react')
        
        framework_analysis = analysis['framework_analysis']
        self.assertGreater(framework_analysis['patterns']['react_hook'], 0)
        self.assertGreater(framework_analysis['patterns']['react_state'], 0)
    
    def test_jsx_element_analysis(self):
        """Test analysis of JSX elements."""
        analysis = self.analyze_file('component.tsx')
        framework_analysis = analysis['framework_analysis']
        
        # Check for JSX patterns
        self.assertGreater(framework_analysis['patterns']['react_jsx'], 0)
        
        # Check for component structure
        type_analysis = analysis['type_analysis']
        self.assertIn('metrics', type_analysis)
        metrics = type_analysis['metrics']
        self.assertGreater(metrics['total_declarations'], 0)
    
    def test_react_state_management(self):
        """Test detection of React state management."""
        analysis = self.analyze_file('component.tsx')
        framework_analysis = analysis['framework_analysis']
        
        # Check for state hooks
        self.assertGreater(framework_analysis['patterns']['react_state'], 0)
        
        # Check for state updates
        type_analysis = analysis['type_analysis']
        self.assertIn('metrics', type_analysis)
        metrics = type_analysis['metrics']
        self.assertGreater(metrics['type_coverage'], 0)
    
    def test_react_props_validation(self):
        """Test validation of React props."""
        analysis = self.analyze_file('component.tsx')
        type_analysis = analysis['type_analysis']
        
        # Check for interface declarations
        self.assertIn('metrics', type_analysis)
        metrics = type_analysis['metrics']
        self.assertGreater(metrics['interfaces'], 0)
        self.assertEqual(metrics['type_coverage'], 100.0)
    
    def test_react_component_documentation(self):
        """Test analysis of React component documentation."""
        analysis = self.analyze_file('component.tsx')
        type_analysis = analysis['type_analysis']
        
        # Check for documentation coverage
        self.assertIn('metrics', type_analysis)
        metrics = type_analysis['metrics']
        self.assertGreater(metrics['total_declarations'], 0)
