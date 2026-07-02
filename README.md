# Portfolio Bot

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-webhook-009688?logo=fastapi&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2A5CAA)
![Build](https://img.shields.io/badge/Build-GitHub%20Actions-informational)
![License](https://img.shields.io/badge/License-MIT-green)

AI Telegram portfolio bot built with Python, aiogram 3, SQLAlchemy, SQLite, and Gemini API.

## Who This Project Is For

- recruiters who want a quick interactive way to review a developer profile;
- clients who prefer a Telegram-first product demo;
- junior backend interviews where architecture, configuration, and bot workflows matter.

## Key Features

- Telegram portfolio navigation with sections about projects, skills, and contacts;
- Gemini-powered AI answers about the developer profile and experience;
- FastAPI webhook server with `/` and `/health` endpoints;
- SQLite analytics table for bot visitors;
- environment-based configuration with Pydantic Settings;
- deployment-ready structure for Render.

## Stack

- Python 3.12
- aiogram 3.x
- FastAPI
- SQLAlchemy 2.x
- aiosqlite
- Pydantic Settings
- Google Gemini API
- Render

## Architecture

```mermaid
flowchart LR
    TG[Telegram User] --> BOT[aiogram Handlers]
    BOT --> AI[Gemini AI Service]
    BOT --> CFG[Settings / .env]
    BOT --> DB[SQLAlchemy + SQLite]
    WEB[FastAPI Webhook App] --> BOT
    WEB --> OPS[/health endpoint]
```

## Project Structure

```text
main.py
src/
├── config.py
├── bot/
│   ├── ai_service.py
│   ├── content.py
│   ├── handlers.py
│   └── keyboards.py
└── db/
    ├── models.py
    └── session.py
docs/screenshots/
```

## Example Commands And Flow

- `/start` — opens the main menu
- `About` — short profile section
- `Projects` — portfolio links and descriptions
- `Skills` — current stack overview
- `Ask AI` — free-form questions answered via Gemini
- `Contacts` — quick links to GitHub and messenger profiles

## Screenshots

Place real screenshots in [docs/screenshots](docs/screenshots/README.md) for:

- start screen
- projects section
- AI chat flow
- contacts section

## Deployment On Render

1. Create a new Web Service from this repository.
2. Set Python runtime `3.12`.
3. Install dependencies with `pip install -r requirements.txt`.
4. Start the app with `python main.py`.
5. Add environment variables from `.env.example`.
6. Set the public hostname in `RENDER_EXTERNAL_HOSTNAME`.

## Environment Variables

Copy `.env.example` to `.env` and set:

- `BOT_TOKEN`
- `GEMINI_API_KEY`
- `DATABASE_URL`
- `RENDER_EXTERNAL_HOSTNAME`
- public profile links (`OWNER_*`)

## Health Check

- `GET /` returns basic service info
- `GET /health` returns service status for uptime checks and deployment verification

## Installation And Local Run

```bash
git clone https://github.com/agaidarovdawlet-web/portfolio_bot.git
cd portfolio_bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## What I Implemented Personally

- webhook-based Telegram bot architecture;
- Gemini integration for AI Q&A;
- async SQLAlchemy persistence layer;
- FastAPI health endpoints and deployment entrypoint;
- environment-based configuration and portfolio content structure.

## Security

- no real Telegram or Gemini tokens are stored in the repository;
- secrets must be provided through `.env` or hosting environment variables;
- `.env.example` contains placeholders only.

## Status

Portfolio-ready demo project. Suitable for showcasing Telegram bot architecture, AI integration, config management, and lightweight backend deployment.

## Roadmap

- add admin analytics screen;
- store chat history with retention policy;
- add tests for handlers and configuration;
- add screenshots and short GIF demo to the repository.
