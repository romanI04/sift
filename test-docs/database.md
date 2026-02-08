# Database Setup

## Installation

Install PostgreSQL 15 or later. On macOS use Homebrew: `brew install postgresql@15`. On Ubuntu: `sudo apt install postgresql`. Start the service and create a database for your application.

## Connection Configuration

Set the DATABASE_URL environment variable with your connection string. Format: `postgresql://user:password@host:port/dbname`. For local development, the default is `postgresql://localhost:5432/myapp`.

## Migrations

We use Alembic for database migrations. Run `alembic upgrade head` to apply all pending migrations. To create a new migration after changing models, run `alembic revision --autogenerate -m "description"`.

## Schema Design

The database uses a normalized schema with foreign key constraints. The main tables are: users, projects, documents, and permissions. Each table has created_at and updated_at timestamps managed by database triggers.

## Backup and Recovery

Automated backups run daily at 3 AM UTC. Use `pg_dump` to create manual backups. To restore from a backup, use `pg_restore` with the appropriate flags. Always test your backups on a staging environment before relying on them in production.
