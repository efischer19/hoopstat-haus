# Contributing to Hoopstat Haus

First off, thank you for your interest in Hoopstat Haus! I'm excited you're here.

This project is currently in a very early and experimental stage. My primary goal is to use it as a personal learning ground to explore AI-driven software development and build my own skills.

That said, I'm open to collaboration, even if the process looks a little different for now.

## Our Current Development Workflow

To stay true to the project's mission, `hoopstat-haus` follows a specific, AI-assisted workflow:

1.  An **Issue** is created, either by me or a contributor, that clearly defines a bug or a feature.
2.  An **AI assistant** (like GitHub Copilot) is used to generate the code to address the issue. This results in a **Pull Request**.
3.  The PR is then reviewed, tested, and **merged by me**.

This unique process is the core of the experiment.

## How You Can Help Right Now

While I'm not actively seeking code contributions from external developers at this time, there are several incredibly valuable ways you can contribute:

#### 🐛 Report Bugs or Suggest Features

This is the most helpful way to contribute. If you find a bug, have an idea for a feature, or think something could be improved, please **[open an issue](https://github.com/efischer19/hoopstat-haus/issues)**! Clear issues are the starting point for the entire AI workflow.

#### 💬 Provide Feedback

Have thoughts on the project's direction, architecture, or even the AI-driven process itself? Feel free to open an issue to start a discussion. I'd love to hear your perspective.

#### 📖 Improve Documentation

If you find a typo, feel something is unclear in the `README` or other documents, or have a question that could be answered in the docs, please let me know by opening an issue.

## What About Code Contributions?

For now, I'm handling the code generation and merging myself as part of the experiment. This helps me maintain a consistent "voice" in the code and focus on the AI-centric workflow.

As the project matures, this process will likely evolve. Thank you for your understanding!

## Python Development Environment

### Setting Up a New Python Project

All Python applications in Hoopstat Haus follow a standard structure and tooling approach. To create a new Python project:

1. **Copy the template:**
   ```bash
   cp -r templates/python-app-template apps/your-new-app
   cd apps/your-new-app
   ```

2. **Update project configuration:**
   Edit `pyproject.toml` to update:
   - Project name (change from "python-app-template")
   - Description and authors
   - Package name in the `packages` field

3. **Install dependencies:**
   ```bash
   poetry install
   ```

4. **Verify setup:**
   ```bash
   poetry run start    # Should run the hello world app
   poetry run test     # Should run and pass all tests
   poetry run lint     # Should show no linting errors
   poetry run format   # Should format the code
   ```

### Development Workflow for Python Projects

All Python projects use the same standard commands:

#### Standard Scripts
- `poetry run start` - Run the application
- `poetry run test` - Run tests with pytest
- `poetry run lint` - Run linting with Ruff
- `poetry run format` - Format code with Black

#### Development Commands
```bash
# Install/update dependencies
poetry install
poetry add package-name              # Add runtime dependency
poetry add --group dev package-name  # Add development dependency

# Run application directly
poetry run python -m app.main

# Test with coverage
poetry run pytest --cov=app

# Fix linting issues automatically
poetry run ruff check --fix .

# Check formatting without changing files
poetry run black --check .
```

#### Docker Usage
```bash
# Build development image
docker build --target development -t your-app:dev .

# Build production image  
docker build --target production -t your-app:prod .

# Run containers
docker run -it your-app:dev      # Development
docker run your-app:prod         # Production
```

### Code Quality Standards

Before committing any Python code:

1. **Run all checks:**
   ```bash
   poetry run format   # Format code
   poetry run lint     # Check for issues
   poetry run test     # Run tests
   ```

2. **Follow the patterns:**
   - Use type hints on function signatures
   - Add docstrings to public functions and classes
   - Write tests for new functionality
   - Keep functions simple and focused

3. **Project structure:**
   ```
   your-app/
   ├── app/              # Application source code
   │   ├── __init__.py
   │   ├── main.py       # Entry point
   │   └── scripts.py    # Development scripts
   ├── tests/            # Test files
   │   ├── __init__.py
   │   └── test_*.py
   ├── Dockerfile        # Multi-stage Docker build
   ├── pyproject.toml    # Poetry configuration
   └── README.md
   ```

## Code of Conduct

Finally, all participants are expected to follow our [Code of Conduct](./CODE_OF_CONDUCT.md). Please be respectful and considerate in all your interactions.
