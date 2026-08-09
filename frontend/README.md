# ChatGPT Clone Frontend

React + Vite frontend for the ChatGPT Clone application.

## Features

- User authentication (Login/Register)
- Protected routes
- ChatGPT-style interface
- Conversation management
- Real-time streaming responses
- Feedback system
- Responsive design (mobile & desktop)
- Collapsible sidebar

## Tech Stack

- React 18
- Vite 5
- Tailwind CSS 3
- React Router DOM 6
- Axios

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── axios.js          # Axios configuration with JWT
│   │   ├── chat.js           # Chat API functions
│   │   ├── conversations.js  # Conversation API functions
│   │   └── feedback.js       # Feedback API functions
│   ├── components/
│   │   ├── Sidebar.jsx       # Sidebar with conversation list
│   │   ├── ChatWindow.jsx    # Message display area
│   │   ├── Message.jsx       # Individual message component
│   │   ├── InputBox.jsx      # Message input form
│   │   └── Feedback.jsx      # Feedback buttons
│   ├── context/
│   │   └── AuthContext.jsx   # Authentication context
│   ├── pages/
│   │   ├── Login.jsx         # Login page
│   │   ├── Register.jsx      # Register page
│   │   └── Chat.jsx          # Main chat page
│   ├── routes/
│   │   └── ProtectedRoute.jsx # Route protection
│   ├── App.jsx               # Main app with routing
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env
├── .env.example
└── index.html
```

## Installation

1. Install dependencies:
```bash
cd ChatGPT-Clone/frontend
npm install
```

2. Configure environment:
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your backend URL
VITE_API_URL=http://localhost:8000/api/v1
```

3. Start development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_URL | Backend API URL | http://localhost:8000/api/v1 |

## API Endpoints Used

### Authentication
- POST /api/v1/auth/register - Register new user
- POST /api/v1/auth/login - Login user
- GET /api/v1/auth/me - Get current user

### Chat
- POST /api/v1/chat - Send message (streaming)
- POST /api/v1/chat/new-chat - Create new conversation

### Conversations
- GET /api/v1/conversations - Get all conversations
- GET /api/v1/conversations/{id}/messages - Get conversation messages

### Feedback
- POST /api/v1/feedback - Submit feedback

## Features in Detail

### Authentication
- JWT token-based authentication
- Automatic token refresh
- Protected routes
- Auto-redirect on 401 errors

### Chat
- Real-time streaming responses
- Multiple conversation support
- Conversation history
- Auto-scroll to latest message
- Loading states

### Feedback
- Thumbs up/down buttons
- Optional comments
- Success confirmation

### Responsive Design
- Desktop: Two-column layout (sidebar + chat)
- Mobile: Collapsible sidebar with overlay
- Touch-friendly interface

## Production Checklist

- [ ] Set VITE_API_URL to production backend URL
- [ ] Run `npm run build` to create production build
- [ ] Test all features in production mode
- [ ] Verify JWT token handling
- [ ] Check responsive design on mobile devices
- [ ] Test error handling
- [ ] Verify streaming works correctly
- [ ] Test feedback submission
- [ ] Check console for errors
- [ ] Optimize bundle size if needed

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT