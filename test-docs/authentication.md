# Authentication

## Overview

Authentication in our API uses JSON Web Tokens (JWT). Every request to a protected endpoint must include a valid bearer token in the Authorization header. Tokens expire after 24 hours and must be refreshed.

## Getting a Token

To obtain a token, send a POST request to `/auth/login` with your email and password. The response includes an access token and a refresh token. Store both securely — never expose them in client-side code.

## Token Refresh

When your access token expires, use the refresh token to obtain a new one. Send a POST to `/auth/refresh` with the refresh token in the request body. This returns a new access token without requiring the user to log in again.

## Role-Based Access Control

Users are assigned roles: admin, editor, or viewer. Each role has different permissions. Admins can create and delete resources. Editors can modify existing resources. Viewers have read-only access to all public endpoints.
