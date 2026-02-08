# API Reference

## Users

### List Users
GET `/api/users` — Returns a paginated list of all users. Supports query parameters: page, per_page, search, and role. Requires admin or viewer role.

### Create User
POST `/api/users` — Creates a new user account. Requires admin role. Body must include email, name, and role. Returns the created user object with an auto-generated ID.

### Get User
GET `/api/users/:id` — Returns a single user by ID. Users can access their own profile. Admins can access any user profile.

## Projects

### List Projects
GET `/api/projects` — Returns all projects the authenticated user has access to. Supports filtering by status (active, archived) and sorting by name or created_at.

### Create Project
POST `/api/projects` — Creates a new project. Requires editor or admin role. Body must include name and optional description. The creating user is automatically added as project owner.

## Documents

### Upload Document
POST `/api/projects/:id/documents` — Uploads a document to a project. Supports markdown, HTML, and plain text files up to 10MB. The document is automatically indexed for search.

### Search Documents
GET `/api/projects/:id/search?q=query` — Searches documents within a project. Returns matching documents ranked by relevance. Supports both keyword and semantic search when enabled.
