# 📚 Intelligent Book Management System

[![Run FastAPI Route Tests](https://github.com/turbotrail/book_manager/actions/workflows/unit_test.yaml/badge.svg)](https://github.com/turbotrail/book_manager/actions/workflows/unit_test.yaml) [![Build and Check Docker Compose](https://github.com/turbotrail/book_manager/actions/workflows/build.yaml/badge.svg)](https://github.com/turbotrail/book_manager/actions/workflows/build.yaml) [![Linting Workflow](https://github.com/turbotrail/book_manager/actions/workflows/liniting.yaml/badge.svg)](https://github.com/turbotrail/book_manager/actions/workflows/liniting.yaml)

This is an AI-powered book management system built with FastAPI, PostgreSQL, and LLaMA3 for generating summaries and personalized book recommendations. It supports core features like user authentication, book and review management, background AI summarization, and recommendation using user preferences.

---

## 🧰 Features

- 🔐 User Registration and Token-Based Authentication (OAuth2)
- 📖 Add, view, and manage books
- 📝 Add and retrieve user reviews for books
- 🤖 Generate book summaries using LLaMA3 locally
- 📊 Save and use user preferences for AI-based recommendations
- 🧠 Contextual book suggestions powered by LLaMA3
- 🪄 Background summary processing for efficiency
- 🐳 Fully dockerized setup with PostgreSQL and Ollama

---

## 🛠 Tech Stack

- **FastAPI** – for building async APIs
- **SQLAlchemy + PostgreSQL** – async database access
- **LangChain + Ollama (LLaMA3)** – for AI summarization and recommendations
- **Docker + Docker Compose** – for containerized development
- **Pytest** – for test coverage
- **Coverage Reports** – integrated with Codecov

---

## 🚀 How to Run

### 1. 🐳 Docker + Ollama Setup

Ensure you have [Ollama](https://ollama.ai) installed and running:

```bash
ollama run llama3
```

Then, build and run the app using Docker Compose:

```bash
docker-compose up --build
```

App will be available at: `http://localhost:8000/docs`

---

## 🔑 Authentication

- Register using `/auth/register` with `username` and `password`.
- Login at `/auth/token` to get a JWT token.
- Use the token in the `Authorization` header: `Bearer <token>`.

---

## 📚 API Endpoints

### 📘 Book Management

- `POST /books/`  
  Add a new book with an uploaded PDF. Generates summary in background.

- `GET /books/`  
  List all books.

- `GET /books/{book_id}`  
  Get details of a single book.

- `GET /books/{book_id}/summary/status`  
  Check if summary is generated.

- `GET /books/{book_id}/summary`  
  Get AI-generated summary.

---

### ✍️ Reviews

- `POST /books/{book_id}/reviews`  
  Add a review for a book.

- `GET /books/{book_id}/reviews`  
  Get all reviews for a book.

---

### ⭐ User Preferences & Recommendations

- `POST /preferences`  
  Save or update user preferences (genre, author, year range).

- `GET /recommendations`  
  Get AI-enhanced personalized book recommendations based on preferences.

---

## 📂 Project Structure

```
book_manager/
├── app/
│   ├── api/               # API routes (books, reviews, auth, recommendations)
│   ├── core/              # Security utils
│   ├── db/                # DB models and session
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # AI summary service
│   └── main.py            # App entrypoint
├── tests/                 # Unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

Run tests and generate coverage report:

```bash
pytest --cov=app --cov-report=term --cov-report=xml
```

Codecov badge in header updates coverage metrics.

---

## 📝 Contributions

Contributions are welcome. Please fork the repo, create a feature branch, and open a PR! Note: This project was created as part of an Evaluation process and not an Production ready tool

---

## 📄 License

MIT License © 2025
