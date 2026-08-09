# 3-Minute Demo Script

## 0:00-0:25 - Register and Login

Open the deployed frontend.

Register a new user, then log in.

Say:

```text
This application uses JWT authentication. After login, the frontend stores the token and protects the chat route. Backend APIs validate the bearer token before allowing chat, conversations, and feedback.
```

## 0:25-0:50 - Architecture Overview

Show the chat screen and sidebar.

Say:

```text
The React frontend talks to a FastAPI backend. The backend loads user memory and current conversation history, routes requests to tools when needed, streams the final assistant response back to the frontend, saves messages, and runs answer evaluation internally in the background.
```

Architecture:

```text
React Frontend
  |
  v
FastAPI Backend
  |
  v
Memory System + Conversation History
  |
  v
Tool Router
  |
  v
LLM
  |
  v
SQLite Database
```

## 0:50-1:10 - Normal Question

Ask:

```text
Explain FastAPI in simple words.
```

Show the streaming response.

Say:

```text
The assistant response streams token by token, which makes the interface feel responsive like ChatGPT.
```

## 1:10-1:35 - Save Personal Memory

Ask:

```text
My name is Indira.
```

Say:

```text
The backend analyzes the user message and stores personal information in the user_memory table.
```

## 1:35-1:55 - Demonstrate Memory Persistence

Click New Chat.

Ask:

```text
What is my name?
```

Expected:

```text
Your name is Indira.
```

Say:

```text
The old chat history is not loaded in the new chat, but user memory persists across conversations.
```

## 1:55-2:15 - Calculator Tool

Ask:

```text
Calculate 12345*67
```

Expected final answer:

```text
827115
```

Say:

```text
The backend routes math requests to the calculator tool, then sends only the final assistant answer to the frontend.
```

## 2:15-2:35 - Search Tool

Ask:

```text
Who is CM of AP?
```

Say:

```text
This type of current-information question is routed to Tavily search internally. The frontend does not expose tool names, API details, or the search process.
```

## 2:35-2:50 - Feedback

Click thumbs up on a good assistant response.

Click thumbs down on another response and add a short comment when testing the negative flow.

Say:

```text
Feedback is linked to the saved assistant message, authenticated user, and conversation.
```

## 2:50-3:00 - Internal Evaluation

Say:

```text
After each assistant answer is saved, the backend runs an internal evaluation and stores question, answer, score, correctness, relevance, and reason in the evaluations table. This is intentionally not displayed in the frontend.
```
