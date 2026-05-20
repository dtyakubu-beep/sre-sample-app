# sre-sample-app

A Python Flask application instrumented with Prometheus metrics, containerised with Docker, and deployed to EKS via a GitOps pipeline using GitHub Actions, Amazon ECR, and Kustomize.

## Overview

This repository demonstrates a production-style application deployment pipeline — from code commit to running container in Kubernetes. The app exposes a `/metrics` endpoint that Prometheus scrapes, enabling real SLI/SLO tracking in Grafana.

## Architecture

```
GitHub (Push to main)
        │
        ▼
GitHub Actions
        │
        ├── Build Docker image
        ├── Push to Amazon ECR
        ├── Update image tag in kustomization.yaml
        ├── Commit updated tag back to repo
        │
        ▼
ArgoCD detects change in kustomization.yaml
        │
        ▼
EKS Cluster (default namespace)
└── sre-sample-app (2 replicas)
    ├── /          — main endpoint
    ├── /health    — liveness probe
    ├── /ready     — readiness probe
    ├── /metrics   — Prometheus metrics
    ├── /error     — simulates errors (SLO testing)
    └── /slow      — simulates latency (SLO testing)
```

## Key Design Decisions

**Prometheus Instrumentation** — The app exposes four custom SRE metrics:
- `app_request_count_total` — request counter by endpoint and status code
- `app_request_latency_seconds` — latency histogram per endpoint
- `app_error_count_total` — error counter per endpoint
- `app_active_requests` — gauge of in-flight requests

**Kustomize Image Management** — The build pipeline updates the image tag in `kustomization.yaml` and commits it back to the repo. ArgoCD detects the commit and automatically deploys the new image — no manual `kubectl` commands required.

**Non-Root Container** — The Docker image runs as a non-root user, following container security best practices.

**Health and Readiness Probes** — Separate `/health` and `/ready` endpoints allow Kubernetes to distinguish between liveness and readiness, enabling zero-downtime deployments.

**SLO Testing Endpoints** — Dedicated `/error` and `/slow` endpoints allow deliberate injection of errors and latency to test alerting rules and validate SLO dashboards.

## Repository Structure

```
sre-sample-app/
├── .github/
│   └── workflows/
│       ├── build.yaml       # Build, push to ECR, update image tag
│       └── destroy.yaml     # Remove from EKS
├── app/
│   ├── main.py              # Flask app with Prometheus metrics
│   └── requirements.txt     # Flask and prometheus-client
├── kubernetes/
│   ├── deployment.yaml      # Kubernetes deployment manifest
│   ├── service.yaml         # Kubernetes service manifest
│   └── kustomization.yaml   # Kustomize image tag management
└── Dockerfile               # Multi-stage container build
```

## CI/CD Pipeline

| Trigger | Action |
|---|---|
| Push to `main` | Build image, push to ECR, update image tag, deploy to EKS |
| Manual (`workflow_dispatch`) | Remove deployment from EKS |

## Prometheus Metrics

```promql
# Request rate
rate(app_request_count_total[5m])

# Error rate
rate(app_error_count_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(app_request_latency_seconds_bucket[5m]))

# SLO — availability (successful requests)
sum(rate(app_request_count_total{status="200"}[5m])) /
sum(rate(app_request_count_total[5m]))
```

## Running Locally

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run the app
python app/main.py

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/metrics

# Generate traffic
for i in {1..10}; do curl -s http://localhost:5000/; done
for i in {1..5}; do curl -s http://localhost:5000/error; done
```

## Running with Docker

```bash
# Build
docker build -t sre-sample-app .

# Run
docker run -p 5000:5000 sre-sample-app

# Test
curl http://localhost:5000/health
curl http://localhost:5000/metrics
```

## Prerequisites

- EKS cluster provisioned by [sre-infra-aws](https://github.com/dtyakubu-beep/sre-infra-aws)
- ArgoCD configured by [sre-gitops-config](https://github.com/dtyakubu-beep/sre-gitops-config)
- GitHub repository secrets:
  - `AWS_ROLE_ARN` — IAM role ARN

## Technologies

| Technology | Purpose |
|---|---|
| Python / Flask | Application framework |
| prometheus-client | Prometheus metrics instrumentation |
| Docker | Containerisation |
| Amazon ECR | Container registry |
| Kustomize | Image tag management |
| Kubernetes | Container orchestration |
| ArgoCD | GitOps continuous delivery |
| GitHub Actions | CI/CD pipeline |

## Related Repositories

| Repo | Description |
|---|---|
| [sre-infra-aws](https://github.com/dtyakubu-beep/sre-infra-aws) | EKS cluster this app deploys into |
| [sre-monitoring-stack](https://github.com/dtyakubu-beep/sre-monitoring-stack) | Observability stack that monitors this app |
| [sre-gitops-config](https://github.com/dtyakubu-beep/sre-gitops-config) | ArgoCD configuration that manages this app |