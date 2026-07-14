# Deploying Disease Prediction on Google Cloud Run

## Prerequisites

- Google Cloud Project
- Billing enabled
- Google Cloud CLI (`gcloud`)
- Docker
- Git

## Enable Required APIs

```bash
gcloud services enable \
run.googleapis.com \
cloudbuild.googleapis.com \
artifactregistry.googleapis.com
```

## Create Artifact Registry

```bash
gcloud artifacts repositories create disease-prediction \
    --repository-format=docker \
    --location=asia-south1
```

## Configure Docker Authentication

```bash
gcloud auth configure-docker asia-south1-docker.pkg.dev
```

## Build and Push the Image

```bash
gcloud builds submit \
    --tag asia-south1-docker.pkg.dev/<PROJECT_ID>/disease-prediction/app
```

## Deploy to Cloud Run

```bash
gcloud run deploy disease-prediction \
    --image asia-south1-docker.pkg.dev/<PROJECT_ID>/disease-prediction/app \
    --region asia-south1 \
    --platform managed \
    --allow-unauthenticated
```

## Required Environment Variables

The following environment variables must be configured in Cloud Run:

| Variable | Required |
|----------|----------|
| `SECRET_KEY` | Yes |
| `GEMINI_API_KEY` | Yes |
| `DATABASE_URL` | Optional |

## Resource Configuration

Recommended Cloud Run configuration:

- Memory: **2 GiB**
- CPU: **2 vCPU**

The increased memory is recommended because the application loads TensorFlow models during startup.

## Verification

After deployment:

- Verify the service URL is accessible.
- Confirm static assets load successfully.
- Confirm backend endpoints are reachable.

## Notes

The deployment infrastructure has been validated successfully on Google Cloud Run.

During post-deployment testing, the application homepage loaded successfully and the backend started correctly. The `/api/ml/predict-multiple` endpoint currently returns a `400 Bad Request`, which appears to be an application-level request validation issue rather than a deployment issue.