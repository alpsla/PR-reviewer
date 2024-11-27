import React, { useState, useEffect, useCallback, useMemo } from 'react';

interface Props {
  userId: number;
  onUserUpdate: (user: User) => void;
}

interface User {
  id: number;
  name: string;
  email?: string;
}

const UserProfile: React.FC<Props> = ({ userId, onUserUpdate }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        setUser(data);
      } catch (error) {
        console.error('Failed to fetch user:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]);

  const handleNameChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (user) {
      const updatedUser = { ...user, name: event.target.value };
      setUser(updatedUser);
      onUserUpdate(updatedUser);
    }
  }, [user, onUserUpdate]);

  const userEmail = useMemo(() => {
    return user?.email || 'No email provided';
  }, [user?.email]);

  if (loading) return <div>Loading...</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div className="user-profile" role="main" aria-label="User Profile">
      <h1>User Profile</h1>
      <div>
        <label htmlFor="name">Name:</label>
        <input
          id="name"
          type="text"
          value={user.name}
          onChange={handleNameChange}
          aria-label="User name"
        />
      </div>
      <div>
        <label htmlFor="email">Email:</label>
        <p id="email">{userEmail}</p>
      </div>
    </div>
  );
};
