# Authentication API

This directory contains the authentication API client for the Inventory Management System frontend.

## File Structure

```
api/
├── config.ts      # API configuration and constants
├── client.ts      # Base API client with fetch wrapper
└── auth.ts        # Authentication-specific API functions
```

## Setup

1. Create a `.env` file in the app root (copy from `.env.example`):

```bash
VITE_API_BASE_URL=http://localhost:8000
```

2. The API client will automatically use this base URL for all requests.

## Authentication Flow

### 1. Register

```typescript
import { register } from './api/auth';

const newUser = await register({
  tenant_id: 1,
  name: 'John Doe',
  email: 'john@example.com',
  password: 'securepassword',
  role: 'Staff', // or 'Admin'
});
```

### 2. Login

```typescript
import { login } from './api/auth';

const { access_token } = await login({
  email: 'john@example.com',
  password: 'securepassword',
});
// Token is automatically stored in localStorage
```

### 3. Get Current User

```typescript
import { getCurrentUser } from './api/auth';

const user = await getCurrentUser();
// Requires authentication token
```

### 4. Change Password

```typescript
import { changePassword } from './api/auth';

await changePassword({
  old_password: 'currentpassword',
  new_password: 'newsecurepassword',
});
```

### 5. Logout

```typescript
import { logout } from './api/auth';

logout();
// Clears token from localStorage
```

## Using with AuthContext

The recommended way to use authentication in your components is through the `AuthContext`:

```typescript
import { useAuth } from '../context/AuthContext';

function MyComponent() {
  const { 
    user, 
    isAuthenticated, 
    isAdmin, 
    login, 
    logout, 
    register 
  } = useAuth();

  // Use authentication state and methods
}
```

## Protected Routes

Protected routes are automatically handled in the App component:

```typescript
import { ProtectedRoute } from './App';

<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

## API Client Features

### Error Handling

The API client automatically handles errors and throws `ApiError`:

```typescript
try {
  await login({ email, password });
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`Error ${error.status}: ${error.message}`);
  }
}
```

### Automatic Token Management

- Tokens are automatically stored in `localStorage` after login
- Tokens are automatically attached to authenticated requests
- Tokens are removed on logout

## Backend API Endpoints

The frontend integrates with these backend endpoints:

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token
- `GET /auth/me` - Get current user info (requires auth)
- `POST /auth/change-password` - Change password (requires auth)

## Type Safety

All API requests and responses are fully typed:

```typescript
interface LoginRequest {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  id: number;
  tenant_id: number;
  name: string;
  email: string;
  role: 'Admin' | 'Staff';
  created_at: string;
}
```

## Security note

- Tokens are stored in `localStorage` (consider `httpOnly` cookies for production)
- All authenticated requests include `Bearer` token in Authorization header
- Password validation is done both client-side and server-side
- Failed login attempts show generic error messages to prevent user enumeration
