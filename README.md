# 📚 Intelligent Book Management System

This project is an AI-enhanced book management system using FastAPI, PostgreSQL, and a locally running LLaMA3 model.

---

## 🧰 Features

- Add/Retrieve/Update/Delete books
- Add and view reviews
- Generate AI summaries using LLaMA3
- Book recommendations (planned)
- Async API and database
- Token-based Authentication (OAuth2)
- Dockerized and deployable to AWS

---

## 🚀 How to Run

### 1. 🐳 Docker + Ollama

```bash
ollama run llama3
docker-compose up --build