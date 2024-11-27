/**
 * Example TypeScript component demonstrating various TypeScript features
 */

// Type definitions and interfaces
interface User {
    id: number;
    name: string;
    email?: string;  // Optional property
    readonly createdAt: Date;  // Read-only property
}

// Generic type
type Result<T> = {
    data: T;
    error: string | null;
};

// Union and intersection types
type Status = 'active' | 'inactive' | 'pending';
type UserWithRole = User & { role: string };

// Utility types
type PartialUser = Partial<User>;
type ReadonlyUser = Readonly<User>;

// Type guard
function isUser(obj: any): obj is User {
    return (
        typeof obj === 'object' &&
        'id' in obj &&
        'name' in obj
    );
}

// React component with TypeScript
interface Props {
    user: User;
    onUpdate: (user: User) => void;
}

function UserProfile({ user, onUpdate }: Props): JSX.Element {
    const [loading, setLoading] = useState<boolean>(false);
    const theme = useContext<Theme>(ThemeContext);

    useEffect(() => {
        // Example of type inference
        const timer = setTimeout(() => {
            setLoading(false);
        }, 1000);

        return () => clearTimeout(timer);
    }, []);

    // Template literal type
    type ButtonVariant = `${Status}-button`;
    const buttonClass: ButtonVariant = 'active-button';

    // Mapped type
    type UserFlags = {
        [K in keyof User]: boolean;
    };

    return (
        <div className={theme.profile}>
            <h1>{user.name}</h1>
            {user.email && <p>{user.email}</p>}
            <button onClick={() => onUpdate(user)}>
                Update Profile
            </button>
        </div>
    );
}

// Example of advanced TypeScript features
class UserService {
    // Method overloading
    async getUser(id: number): Promise<User>;
    async getUser(email: string): Promise<User>;
    async getUser(identifier: number | string): Promise<User> {
        // Implementation
        return {} as User;
    }

    // Generic method with constraints
    async updateUser<T extends Partial<User>>(id: number, data: T): Promise<User> {
        return {} as User;
    }
}

export { UserProfile, UserService, type User, type Result };
