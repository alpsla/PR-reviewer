/**
 * Example of a branded type for type-safe ID handling
 */
type UserId = string & { readonly __brand: unique symbol };

/**
 * Interface representing user data with documentation
 * @interface
 */
interface UserData {
    id: UserId;
    name: string;
    age: number | null;  // Example of strict null checks
}

/**
 * Type guard to check if value is UserData
 * @param value - The value to check
 * @returns True if value is UserData
 */
function isUserData(value: any): value is UserData {
    return (
        typeof value === 'object' &&
        value !== null &&
        typeof value.name === 'string' &&
        (typeof value.age === 'number' || value.age === null)
    );
}

/**
 * Utility function to create a user
 * @param name - The user's name
 * @param age - The user's age
 * @returns The created user object
 * @example
 * const user = createUser("John", 30);
 */
function createUser(name: string, age: number): UserData {
    const id = name.toLowerCase() as UserId;  // Example of type assertion
    return { id, name, age };
}

// Example of template literal type
type EmailLocale = `${string}@${string}.${string}`;

// Example of mapped type
type ReadonlyUser = {
    readonly [K in keyof UserData]: UserData[K];
};

// Example of conditional type
type UserAgeType<T> = T extends UserData ? number | null : never;

// Example of utility type usage
type PartialUser = Partial<UserData>;

const ADMIN_ROLES = ['admin', 'superadmin'] as const;  // const assertion
type AdminRole = typeof ADMIN_ROLES[number];

// Missing documentation example
function validateUser(user: unknown) {
    if (!isUserData(user)) {
        throw new Error('Invalid user data');
    }
    return user;
}

// Example with 'any' type that should be improved
function processUserData(data: any) {
    return data;
}
