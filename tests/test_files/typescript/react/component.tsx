import { User, UserRole, PartialUser } from 'test-module';
import React, { useState, useEffect, useCallback, Dispatch, SetStateAction, ReactElement } from 'react';

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

// Type definitions for state setters
type SetUserFn = Dispatch<SetStateAction<User | null>>;
type SetLoadingFn = Dispatch<SetStateAction<boolean>>;
type SetEditingFn = Dispatch<SetStateAction<boolean>>;

// Type for fetchUser function
type FetchUserFn = (id: string) => Promise<User>;

// Type for useAuth hook result
interface AuthHookResult {
    user: User | null;
    loading: boolean;
}

// Mock fetchUser implementation
const fetchUser: FetchUserFn = async (id: string): Promise<User> => {
    // Mock implementation
    return {
        id: parseInt(id),
        name: 'John Doe',
        email: 'john@example.com'
    };
};

/**
 * Custom hook for user authentication
 * @param userId - The user ID to authenticate
 * @returns The authenticated user and loading state
 */
function useAuth(userId: string): AuthHookResult {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    
    useEffect(() => {
        const loadUser = async (): Promise<void> => {
            setLoading(true);
            const userData = await fetchUser(userId);
            setUser(userData);
            setLoading(false);
        };
        
        void loadUser();
        
        return (): void => {
            // Cleanup function
            setLoading(false);
            setUser(null);
        };
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

interface AdminPanelProps {
    user: User;
}

/**
 * Admin panel component for admin users
 * @param props - The component props
 * @returns JSX element
 */
const AdminPanel: React.FC<AdminPanelProps> = ({ user }): ReactElement => {
    return (
        <div className="admin-panel">
            <h2>Admin Panel</h2>
            <p>Welcome, {user.name}</p>
        </div>
    );
};

/**
 * User component that displays user information
 * @param props - The component props
 * @returns JSX element
 */
export const UserComponent: React.FC<Props> = ({ user, role, onUpdate }): ReactElement => {
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const userInfo: PartialUser = user as PartialUser;
    
    const handleUpdate = useCallback((): void => {
        if (onUpdate) {
            onUpdate(user);
        }
        setIsEditing(false);
    }, [user, onUpdate]);
    
    return (
        <div className="user-component">
            <h1>{userInfo.name}</h1>
            <p>{userInfo.email}</p>
            {isAdmin(user) && <AdminPanel user={user} />}
            <button onClick={(): void => setIsEditing(!isEditing)}>
                {isEditing ? 'Cancel' : 'Edit'}
            </button>
            {isEditing && (
                <button onClick={handleUpdate}>Save</button>
            )}
        </div>
    );
};
