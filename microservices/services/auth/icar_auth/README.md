# Django JWT Authentication Project

A complete Django REST API with JWT authentication system featuring role-based access control for users and admins.

## Features

- **User Authentication**: Signup, Login, Logout with JWT tokens
- **User Management**: Profile view/update, password change, password reset
- **Admin Panel**: List users, edit users, delete users, reset user passwords
- **Role-based Access Control**: User and Admin roles with different permissions

## Project Structure

```
django_jwt_project/
├── manage.py
├── requirements.txt
├── jwt_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── users/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── serializers.py
    ├── urls.py
    ├── views.py
    └── permissions.py
```

## Setup Instructions

### 1. Create Virtual Environment and Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser

```bash
python manage.py createsuperuser
```

### 4. Run the Server

```bash
python manage.py runserver
```

## API Endpoints

### Free Access (No Authentication Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/signup/` | POST | Create new user account |
| `/api/login/` | POST | Login and get JWT tokens |
| `/api/forgot-password/` | POST | Request password reset link |
| `/api/reset-password/` | POST | Reset password with email |

### User Access (Authentication Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/profile/` | GET | Get user profile |
| `/api/profile/` | PUT | Update user profile |
| `/api/change-password/` | POST | Change password |
| `/api/logout/` | POST | Logout (blacklist refresh token) |

### Admin Access (Admin Role Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/` | GET | List all users |
| `/api/users/<id>/` | GET | Get user details |
| `/api/users/<id>/` | PUT | Update user details |
| `/api/users/<id>/` | DELETE | Delete user |
| `/api/admin/reset-password/<user_id>/` | POST | Reset any user's password |

## Testing the API

### Sample Requests

**Signup:**
```bash
curl -X POST http://localhost:8000/api/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "number": "1234567890",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

**Get Profile (with JWT token):**
```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Update Profile:**
```bash
curl -X PUT http://localhost:8000/api/profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "John Updated",
    "email": "john@example.com",
    "number": "0987654321"
  }'
```

**Change Password:**
```bash
curl -X POST http://localhost:8000/api/change-password/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "old_password": "SecurePass123",
    "new_password": "NewSecurePass456",
    "confirm_password": "NewSecurePass456"
  }'
```

**Logout:**
```bash
curl -X POST http://localhost:8000/api/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### Admin Operations

**List All Users:**
```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Update User:**
```bash
curl -X PUT http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -d '{
    "name": "Updated Name",
    "email": "updated@example.com",
    "role": "admin"
  }'
```

**Delete User:**
```bash
curl -X DELETE http://localhost:8000/api/users/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Admin Reset User Password:**
```bash
curl -X POST http://localhost:8000/api/admin/reset-password/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -d '{
    "new_password": "NewPassword123"
  }'
```

## User Model Fields

- `id` - Auto-generated primary key
- `name` - User's full name
- `email` - Unique email address (used for login)
- `number` - Phone number (optional)
- `role` - User role: 'user' or 'admin'
- `is_active` - Account status
- `date_joined` - Registration date
- `last_login` - Last login timestamp

## JWT Token Configuration

- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 1 day
- **Rotate Refresh Tokens**: Enabled
- **Blacklist After Rotation**: Enabled

## Security Notes

1. Change `SECRET_KEY` in production
2. Set `DEBUG = False` in production
3. Configure proper `ALLOWED_HOSTS`
4. Use environment variables for sensitive settings
5. Configure proper email backend for production
6. Set up CORS properly for production
