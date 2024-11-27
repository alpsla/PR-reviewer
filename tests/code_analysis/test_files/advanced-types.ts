// Advanced TypeScript type features example

// Mapped Types
type Readonly<T> = {
    readonly [P in keyof T]: T[P];
};

// Conditional Types
type NonNullable<T> = T extends null | undefined ? never : T;

// Utility Types
type Pick<T, K extends keyof T> = {
    [P in K]: T[P];
};

// Type Assertions
const value: any = "hello";
const length: number = (value as string).length;

// Type Guards
function isString(value: any): value is string {
    return typeof value === "string";
}

function processValue(value: string | number) {
    if (isString(value)) {
        // TypeScript knows value is string here
        return value.toLowerCase();
    }
    // TypeScript knows value is number here
    return value.toFixed(2);
}
