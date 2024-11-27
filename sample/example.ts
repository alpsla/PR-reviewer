interface User {
    id: number;
    name: string;
    email: string;
    preferences?: UserPreferences;
}

interface UserPreferences {
    theme: 'light' | 'dark';
    notifications: boolean;
    language: string;
}

type UserId = Brand<number, 'UserId'>;

function isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function createUser(name: string, email: string): Result<User, string> {
    if (!name.trim()) {
        return { ok: false, error: 'Name is required' };
    }

    if (!isValidEmail(email)) {
        return { ok: false, error: 'Invalid email format' };
    }

    const user: User = {
        id: Math.floor(Math.random() * 1000000),
        name: name.trim(),
        email,
        preferences: {
            theme: 'light',
            notifications: true,
            language: 'en'
        }
    };

    return { ok: true, value: user };
}

class UserService {
    private users: Map<UserId, User> = new Map();

    async findUserById(id: UserId): Promise<User | null> {
        return this.users.get(id) || null;
    }

    async updateUser(id: UserId, updates: Partial<User>): Promise<Result<User, string>> {
        const user = await this.findUserById(id);
        if (!user) {
            return { ok: false, error: 'User not found' };
        }

        const updatedUser: User = {
            ...user,
            ...updates,
            id: user.id // Prevent id from being updated
        };

        this.users.set(id, updatedUser);
        return { ok: true, value: updatedUser };
    }
}

// Type guard example
function isUserPreferences(obj: unknown): obj is UserPreferences {
    if (typeof obj !== 'object' || obj === null) return false;
    
    const pref = obj as UserPreferences;
    return (
        typeof pref.theme === 'string' &&
        typeof pref.notifications === 'boolean' &&
        typeof pref.language === 'string'
    );
}

// Utility type usage
type UpdateUserRequest = Omit<User, 'id'>;
type UserResponse = Pick<User, 'id' | 'name' | 'email'>;

// Generic error handling
interface Result<T, E = string> {
    ok: boolean;
    value?: T;
    error?: E;
}

// Branded type for type-safe IDs
type Brand<T, B> = T & { __brand: B };

/**
 * Processes a user update request with full type safety and validation
 * @param id - The user's unique identifier
 * @param updates - Partial user object containing fields to update
 * @returns A Result containing either the updated user or an error message
 * @example
 * const result = await processUserUpdate(userId, { name: "John Doe" });
 * if (result.ok) {
 *     console.log("User updated:", result.value);
 * } else {
 *     console.error("Error:", result.error);
 * }
 */
async function processUserUpdate(
    id: UserId,
    updates: Partial<UpdateUserRequest>
): Promise<Result<UserResponse, string>> {
    const service = new UserService();
    const result = await service.updateUser(id, updates);

    if (!result.ok) {
        return result;
    }

    const { id: userId, name, email } = result.value;
    return {
        ok: true,
        value: { id: userId, name, email }
    };
}
