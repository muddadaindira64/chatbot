# API Documentation

Base backend URL:

```text
http://localhost:8000
```

Default API prefix:

```text
/api
```

Most application endpoints are mounted under `/api/v1`. Protected endpoints require:

```http
Authorization: Bearer <jwt_token>
```

## Authentication APIs

### Register User

```http
POST /api/v1/auth/register
```

Request:

```json
{
  "username": "indira",
  "email": "indira@example.com",
  "password": "secret123"
}
```

Response:

```json
{
  "id": 1,
  "username": "indira",
  "email": "indira@example.com",
  "created_at": "2026-08-05T10:00:00"
}
```

### Login User

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "indira@example.com",
  "password": "secret123"
}
```

Response:

```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

### Current User

```http
GET /api/v1/auth/me
```

Response:

```json
{
  "id": 1,
  "username": "indira",
  "email": "indira@example.com",
  "created_at": "2026-08-05T10:00:00"
}
```

## Chat APIs

### Send Chat Message

```http
POST /api/v1/chat
```

Authentication: required.

Request:

```json
{
  "conversation_id": 1,
  "message": "Calculate 12345*67"
}
```

Response:

```text
Streaming text/event-stream assistant response.
```

Behavior:

- Creates a conversation when `conversation_id` is omitted.
- Loads user memory.
- Loads current conversation history.
- Routes to tools when needed.
- Streams the assistant answer.
- Saves user and assistant messages.
- Runs background evaluation internally.

### Create New Chat

```http
POST /api/v1/new-chat
```

Authentication: required.

Response:

```json
{
  "conversation_id": 1,
  "message": "New chat created"
}
```

## Conversation APIs

### Create Conversation

```http
POST /api/conversations/
```

Authentication: required.

Response:

```json
{
  "conversation_id": 1,
  "title": "New Chat"
}
```

Note: frontend code also expects list, message-history, and delete conversation endpoints. Confirm those routes are present before final deployment smoke testing.

## Feedback APIs

### Submit Feedback

```http
POST /api/v1/feedback/
```

Authentication: required.

Request:

```json
{
  "message_id": 10,
  "rating": "positive",
  "comment": null
}
```

Negative feedback with comment:

```json
{
  "message_id": 10,
  "rating": "negative",
  "comment": "The answer missed context."
}
```

Response:

```json
{
  "message": "Feedback saved successfully",
  "feedback_id": 1
}
```

Validation:

- Message must exist.
- Message must belong to a conversation owned by the authenticated user.
- Rating must be `positive` or `negative`.

## Health APIs

### Root Health

```http
GET /health
```

Response:

```json
{
  "status": "healthy",
  "service": "ChatGPT Clone Backend",
  "version": "1.0.0"
}
```

### API Health

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "healthy",
  "service": "ChatGPT Clone Backend",
  "version": "1.0.0"
}
```
