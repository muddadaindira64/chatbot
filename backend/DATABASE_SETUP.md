# Database Configuration and Verification Guide

## Database Configuration

### SQLite Database URL
```
DATABASE_URL=sqlite:///./chatgpt_clone.db
```

### Async SQLite Configuration
The database uses `aiosqlite` for async operations with the following configuration:

```python
database_url = settings.sqlite_database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(
    database_url,
    echo=False,
    connect_args={"check_same_thread": False}
)
```

**Important**: `check_same_thread=False` is required for SQLite async operations.

## Database Schema

### Tables Created

#### 1. users
- `id` (Primary Key)
- `username` (Unique, Not Null)
- `email` (Unique, Not Null)
- `password_hash` (Not Null)
- `created_at` (Timestamp)

#### 2. user_memory
- `id` (Primary Key)
- `user_id` (Foreign Key -> users.id, Unique)
- `name` (Nullable)
- `role` (Nullable)
- `company` (Nullable)
- `skills` (JSON, Default: [])
- `preferences` (JSON, Default: {})
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Relationship**: One-to-One with User

#### 3. conversations
- `id` (Primary Key)
- `user_id` (Foreign Key -> users.id)
- `title` (Default: "New Chat")
- `created_at` (Timestamp)

**Relationship**: Many-to-One with User, One-to-Many with Messages

#### 4. messages
- `id` (Primary Key)
- `conversation_id` (Foreign Key -> conversations.id)
- `role` (Not Null)
- `content` (Text, Not Null)
- `created_at` (Timestamp)

**Relationship**: Many-to-One with Conversation

#### 5. feedback
- `id` (Primary Key)
- `user_id` (Foreign Key -> users.id)
- `conversation_id` (Foreign Key -> conversations.id)
- `message_id` (Foreign Key -> messages.id)
- `rating` (Not Null)
- `comment` (Nullable)
- `created_at` (Timestamp)

**Relationship**: Many-to-One with User, Conversation, Message

#### 6. evaluations
- `id` (Primary Key)
- `user_id` (Foreign Key -> users.id)
- `conversation_id` (Foreign Key -> conversations.id)
- `message_id` (Foreign Key -> messages.id)
- `question` (Text, Not Null)
- `answer` (Text, Not Null)
- `score` (Float, Not Null)
- `correctness` (Not Null)
- `relevance` (Not Null)
- `reason` (Nullable)
- `created_at` (Timestamp)

**Relationship**: Many-to-One with User, Conversation, Message

## Database Relationships

```
User (1) ────── (*) Conversation
  │
  │
  │
 (1) ────── (1) UserMemory
  │
  │
  │
 (*) ────── (*) Feedback
  │
  │
  │
 (*) ────── (*) Evaluation
```

### Relationship Rules

1. **User Isolation**: One user cannot access another user's data
2. **Cascade Delete**: When a user is deleted, all their conversations, messages, feedback, and evaluations are deleted
3. **Message Ownership**: Messages belong only to their conversation
4. **Memory Privacy**: User memory is private to each user

## Table Creation

Tables are automatically created when the application starts using:

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

This creates the file: `chatgpt_clone.db` in the backend directory.

## Environment Variables

### Required Variables

```env
# Database
SQLITE_DATABASE_URL=sqlite:///./chatgpt_clone.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# API Keys
OPENROUTER_API_KEY=your-openrouter-api-key
TAVILY_API_KEY=your-tavily-api-key
```

### Optional Variables

```env
APP_NAME=ChatGPT Clone Backend
APP_DESCRIPTION=Production-ready FastAPI foundation
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True
API_PREFIX=/api
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-20b
```

## Testing Database

### 1. Start the Backend

```bash
cd ChatGPT-Clone/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Verify Database File Created

```bash
# Check if database file exists
ls -la chatgpt_clone.db

# Should show:
# -rw-r--r-- 1 user user 0 Nov  5 12:00 chatgpt_clone.db
```

### 3. Verify Tables Created

```bash
# Install SQLite CLI if not available
# Then run:
sqlite3 chatgpt_clone.db ".tables"

# Expected output:
# conversations
# evaluations
# feedback
# messages
# user_memory
# users
```

### 4. Verify Table Schema

```bash
# Check users table
sqlite3 chatgpt_clone.db ".schema users"

# Expected output:
# CREATE TABLE users (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     username VARCHAR(50) UNIQUE NOT NULL,
#     email VARCHAR(255) UNIQUE NOT NULL,
#     password_hash VARCHAR(255) NOT NULL,
#     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
# )
```

### 5. Test Complete Flow

#### Test 1: Register User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Verify**: Check users table
```bash
sqlite3 chatgpt_clone.db "SELECT * FROM users;"
```

Expected: 1 row with username, email, and password_hash

#### Test 2: Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Verify**: Response contains `access_token`

#### Test 3: Send Message with Personal Info
```bash
# First, get token from login
TOKEN="your-token-here"

# Send message
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is Indira"
  }'
```

**Verify**: Check user_memory table
```bash
sqlite3 chatgpt_clone.db "SELECT * FROM user_memory;"
```

Expected: 1 row with name="Indira"

#### Test 4: Create New Chat
```bash
curl -X POST "http://localhost:8000/api/v1/chat/new-chat" \
  -H "Authorization: Bearer $TOKEN"
```

**Verify**: Check conversations table
```bash
sqlite3 chatgpt_clone.db "SELECT * FROM conversations;"
```

Expected: 1 row with user_id and title="New Chat"

#### Test 5: Send Normal Message
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python?",
    "conversation_id": 1
  }'
```

**Verify**: Check messages table
```bash
sqlite3 chatgpt_clone.db "SELECT * FROM messages;"
```

Expected: 2 rows (user message and assistant message)

#### Test 6: Submit Feedback
```bash
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 2,
    "rating": "positive",
    "comment": "Good answer"
  }'
```

**Verify**: Check feedback table
```bash
sqlite3 chatgpt_clone.db "SELECT * FROM feedback;"
```

Expected: 1 row with rating="positive"

#### Test 7: Run Evaluation
Send another message and wait for background evaluation to complete.

**Verify**: Check evaluations table
```bash
sqlite3 chatgpt_clone.db "SELECT * FROM evaluations;"
```

Expected: 1 row with score, correctness, relevance

## Database Verification Checklist

- [ ] Database file `chatgpt_clone.db` created
- [ ] All 6 tables created (users, user_memory, conversations, messages, feedback, evaluations)
- [ ] Foreign keys properly configured
- [ ] User registration creates user in database
- [ ] User memory created/updated correctly
- [ ] Conversations created with correct user_id
- [ ] Messages linked to correct conversation
- [ ] Feedback linked to correct message and user
- [ ] Evaluations created in background
- [ ] Cascade delete works (delete user deletes all related data)
- [ ] User isolation maintained (users can't access other users' data)

## Production Considerations

### 1. Database Backups
```bash
# Backup database
cp chatgpt_clone.db chatgpt_clone.db.backup

# Restore database
cp chatgpt_clone.db.backup chatgpt_clone.db
```

### 2. Database Migration
For production, consider using Alembic for database migrations:

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 3. Database Security
- Keep `chatgpt_clone.db` file permissions restricted
- Never commit database file to version control
- Use strong SECRET_KEY in production
- Regular backups

### 4. Performance
- SQLite is suitable for small to medium applications
- For high traffic, consider PostgreSQL
- Add indexes for frequently queried fields
- Regular VACUUM to optimize database

## Troubleshooting

### Issue: "database is locked"
**Solution**: Ensure only one process is accessing the database at a time

### Issue: "check_same_thread" error
**Solution**: Ensure `connect_args={"check_same_thread": False}` is set

### Issue: Tables not created
**Solution**: Check that `Base.metadata.create_all()` is called in lifespan

### Issue: Foreign key constraint failed
**Solution**: Ensure referenced records exist before creating related records

## Summary

✅ SQLite database configured correctly
✅ All 6 tables created with proper relationships
✅ Environment variables properly set
✅ Database file: `chatgpt_clone.db`
✅ Async operations configured with `aiosqlite`
✅ User isolation maintained
✅ Cascade delete configured
✅ Production-ready configuration

The database is ready for deployment!