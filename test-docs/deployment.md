# Deployment Guide

## Prerequisites

Before deploying, ensure you have Docker installed, access to the container registry, and the required environment variables configured. You also need kubectl if deploying to Kubernetes.

## Building the Container

Build the Docker image using the provided Dockerfile: `docker build -t myapp:latest .`. The multi-stage build keeps the final image under 100MB. Tag the image with the commit SHA for traceability.

## Environment Variables

Required variables: DATABASE_URL, SECRET_KEY, REDIS_URL, and SENTRY_DSN. Optional: LOG_LEVEL (default: info), WORKERS (default: 4). Never commit secrets to version control — use your platform's secret management.

## Deploying to Production

Push the image to your container registry, then update the Kubernetes deployment. Use rolling updates to avoid downtime. The health check endpoint at `/health` ensures traffic only routes to healthy pods.

## Monitoring and Logging

Application logs are sent to stdout and collected by the logging infrastructure. Metrics are exposed at `/metrics` in Prometheus format. Set up alerts for error rate spikes, high latency, and low pod count.

## Rollback Procedure

If a deployment causes issues, roll back to the previous version immediately. Use `kubectl rollout undo deployment/myapp` for Kubernetes. Verify the rollback by checking the health endpoint and monitoring error rates.
