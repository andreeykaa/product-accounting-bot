# Product Accounting Telegram Bot

A Telegram bot for **managing product inventory**, **technical cards**, and **task workflows** with categories, quantity tracking, and process-based task lists.

## Features

### 📦 Product accounting
- Create, edit, and delete product categories
- Add products with quantity and minimum stock limit
- Edit product name, quantity, and limit separately
- View products within a specific category
- Automatic notifications when product quantity reaches or falls below the limit
- Works for multiple users at the same time

### 🧾 Technical cards
- Maintain technical cards grouped by process and target type
- Three fixed processes:
  - Холодний процес
  - Гарячий процес
  - Видача
- Two target types:
  - Страва
  - Заготовка
- Add, edit, and delete technical cards
- Optional photo attachment for each technical card
- Edit card name and photo independently
- View technical cards filtered by process and type
- Designed for kitchen workflows and recipe management

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

### 🔍 Global quick search
- Fast global search across:
  - Products
  - Technical cards
- Search supports:
  - Partial matches
  - Different word forms (e.g. *курка → куркою*)
  - Long names with multiple words
- Smart search behavior:
  - Exact and word-based matches are always included
  - Fuzzy matching is used for typos and approximate queries
- Search results open products or technical cards directly
- Navigation support:
  - Return back to search results after opening an item
  - Search context resets automatically when navigating via bottom menu

### 🗄️ General
- Local SQLite database
- FTS5-based search index for high performance
- Clean modular project structure
- Separation of UI, handlers, and storage layers
- Shared data access for multiple users

## Tech Stack
- Python 3.11
- python-telegram-bot
- SQLite (with FTS5)
- dotenv

## Purpose
This project was created as a practical learning project to practice:
- Telegram Bot API
- Asynchronous Python
- Project architecture and separation of concerns
- Working with databases and search indexes
- Conversation handlers and state management
- Inline keyboards and callback-based navigation
- Full-text search and fuzzy matching
- Shared data handling for multiple users

## Status
🚧 Actively developing
