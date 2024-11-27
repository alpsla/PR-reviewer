// Type declarations for testing

declare interface User {
    id: number;
    name: string;
    email: string;
}

declare interface Post {
    id: number;
    title: string;
    content: string;
    author: User;
}

declare type PostStatus = 'draft' | 'published' | 'archived';

declare interface Comment {
    id: number;
    content: string;
    author: User;
    post: Post;
    status: PostStatus;
}
