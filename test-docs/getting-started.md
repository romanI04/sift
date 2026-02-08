# Getting Started

## Quick Start

Clone the repository and install dependencies: `git clone https://github.com/example/myapp && cd myapp && pip install -r requirements.txt`. Copy the example environment file: `cp .env.example .env` and fill in your configuration values.

## Running Locally

Start the development server with `python manage.py runserver`. The app will be available at http://localhost:8000. Hot reload is enabled by default — changes to Python files restart the server automatically.

## Running Tests

Run the full test suite with `pytest`. For faster feedback during development, run specific test files: `pytest tests/test_auth.py`. Coverage reports are generated with `pytest --cov=myapp`.

## Project Structure

The project follows a standard layout: `myapp/` contains the application code, `tests/` has the test suite, `migrations/` stores database migrations, and `docs/` holds documentation. Configuration is centralized in `config.py`.

## Contributing

Fork the repository, create a feature branch, make your changes, and submit a pull request. All PRs require passing tests and a code review. Follow the existing code style and include tests for new functionality.
