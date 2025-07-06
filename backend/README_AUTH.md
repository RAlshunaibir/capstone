# JWT Authentication Implementation

This document describes the JWT (JSON Web Token) authentication system implemented in the chatbot application.

## Features

- **User Registration**: `/signup` endpoint for creating new user accounts
- **User Login**: `/login` endpoint for authenticating users
- **Password Hashing**: Secure password storage using bcrypt
- **JWT Tokens**: Stateless authentication using JWT tokens
- **Protected Endpoints**: Secure API endpoints using JWT verification
- **Token Refresh**: `/refresh` endpoint for extending token validity

## API Endpoints

### Authentication Endpoints

#### POST `/signup`
Register a new user account.

**Request Body:**
```json
{
    "username": "string",
    "email": "string", 
    "password": "string"
}
```

**Response:**
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "username": "string"
}
```

#### POST `/login`
Authenticate an existing user.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "username": "string"
}
```

#### POST `/refresh`
Refresh the current JWT token.

**Headers:**
```
Authorization: Bearer <current_token>
```

**Response:**
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "username": "string"
}
```

### Protected Endpoints

#### POST `/chat`
Send a message to the chatbot (requires authentication).

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "message": "string"
}
```

**Response:**
```json
{
    "response": "string"
}
```

#### GET `/me`
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "username": "string",
    "email": "string"
}
```

#### GET `/users`
List all registered users (requires authentication, for debugging).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "users": ["string"]
}
```

## Configuration

### Environment Variables

Set the following environment variables in your `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

**Important**: Change the `JWT_SECRET_KEY` in production to a secure random string.

### JWT Settings

- **Algorithm**: HS256
- **Token Expiration**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Token Type**: Bearer

## Security Features

1. **Password Hashing**: All passwords are hashed using bcrypt with salt
2. **JWT Tokens**: Stateless authentication without server-side sessions
3. **Token Expiration**: Tokens automatically expire after 30 minutes
4. **Secure Headers**: Proper HTTP authentication headers
5. **Input Validation**: Pydantic models for request validation

## Usage Examples

### Using curl

1. **Register a new user:**
```bash
curl -X POST "http://localhost:5001/signup" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

2. **Login:**
```bash
curl -X POST "http://localhost:5001/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "password123"}'
```

3. **Use protected endpoint:**
```bash
curl -X POST "http://localhost:5001/chat" \
     -H "Authorization: Bearer <your_jwt_token>" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, chatbot!"}'
```

### Using Python requests

```python
import requests

# Signup
signup_data = {
    "username": "testuser",
    "email": "test@example.com", 
    "password": "password123"
}
response = requests.post("http://localhost:5001/signup", json=signup_data)
token = response.json()["access_token"]

# Use protected endpoint
headers = {"Authorization": f"Bearer {token}"}
chat_data = {"message": "Hello!"}
response = requests.post("http://localhost:5001/chat", json=chat_data, headers=headers)
```

## Testing

Run the test script to verify the authentication system:

```bash
python test_auth.py
```

This will test:
- User registration
- User login
- Protected endpoint access
- Invalid token handling
- User information retrieval

## Implementation Details

### Password Security
- Uses bcrypt for password hashing
- Automatic salt generation
- Secure password verification

### JWT Implementation
- Uses PyJWT library
- HS256 algorithm for signing
- Configurable expiration time
- Stateless authentication

### Error Handling
- Proper HTTP status codes
- Descriptive error messages
- Security headers for authentication failures

## Next Steps

1. **Database Integration**: Replace in-memory storage with a proper database
2. **Password Reset**: Implement password reset functionality
3. **Email Verification**: Add email verification for new accounts
4. **Rate Limiting**: Add rate limiting for authentication endpoints
5. **Logging**: Add comprehensive logging for security events
6. **CORS**: Configure CORS for frontend integration 