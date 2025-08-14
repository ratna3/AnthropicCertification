# MCP Chat

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-blue?style=flat&logo=github)](https://ratna3.github.io/AnthropicCertification/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Google Gemini API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## 🌐 Live Demo

Visit our [GitHub Pages site](https://ratna3.github.io/AnthropicCertification/) to see the project showcase and documentation.

## Prerequisites

- Python 3.9+
- Google Gemini API Key

## Setup

### Step 1: Configure the environment variables

1. Create or edit the `.env` file in the project root and verify that the following variables are set correctly:

```
GEMINI_API_KEY=""  # Enter your Google Gemini API secret key
```

### Step 2: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Run the project

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install google-generativeai python-dotenv prompt-toolkit "mcp[cli]==1.8.0" fastapi uvicorn
```

3. Run the project

```bash
python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

### Linting and Typing Check

There are no lint or type checks implemented.

## 🚀 Deployment & Hosting

### GitHub Pages

This project is automatically deployed to GitHub Pages using GitHub Actions. The live demo is available at: https://ratna3.github.io/AnthropicCertification/

#### Deployment Process

1. **Automatic Deployment**: Every push to the `main` branch triggers the GitHub Actions workflow
2. **Static Site Generation**: The workflow builds a static site from the `docs/` directory
3. **GitHub Pages**: The site is deployed to GitHub Pages with a custom domain support

#### Manual Deployment Setup

To set up GitHub Pages for your fork:

1. Go to your repository settings
2. Navigate to "Pages" in the left sidebar
3. Under "Source", select "GitHub Actions"
4. The deployment workflow will automatically run on the next push to `main`

### Local Web Server

Run the web interface locally for development:

```bash
# Simple web interface (no MCP features)
uvicorn simple_web_server:app --reload --host 0.0.0.0 --port 8000

# Full web interface with MCP support
uvicorn web_server:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

For production deployment of the full application:

1. **Environment Setup**: Ensure all environment variables are properly configured
2. **Dependencies**: Install production dependencies
3. **ASGI Server**: Use a production ASGI server like Gunicorn with Uvicorn workers
4. **Reverse Proxy**: Set up Nginx or similar for SSL termination and load balancing

```bash
# Production server example
gunicorn web_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
