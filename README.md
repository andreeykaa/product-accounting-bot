# Product Accounting Telegram Bot

A Telegram bot for **managing product inventory** and **task workflows** with categories, quantity tracking, and process-based task lists.

## Features
### 📦 Product accounting
- Create, edit, and delete product categories
- Add products with quantity and minimum stock limit
- Edit product name, quantity, and limit separately
- View products within a specific category
- Automatic notifications when product quantity reaches or falls below the limit
- Works for multiple users at the same time

### ✅ Task management
- Maintain a shared task list across all users
- Three fixed task processes:
  - Холодний процес
  - Гарячий процес
  - Видача
- Add new tasks to a selected process
- Edit task text
- Mark tasks as completed
- View tasks filtered by process

### 🗄️ General
- Local SQLite database
- Clean modular project structure
- Separation of UI, handlers, and storage layers

## Tech Stack
- Python 3.11
- python-telegram-bot
- SQLite
- dotenv

## Purpose
This project was created as a practical learning project to practice:
- Telegram Bot API
- Asynchronous Python
- Project architecture and separation of concerns
- Working with databases
- Conversation handlers and state management
- Inline keyboards and callback-based navigation
- Shared data handling for multiple users

## Status
🚧 Actively developing
