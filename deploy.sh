#!/bin/bash
# ============================================================
# Audio Transcriber — GCP Cloud Run Deploy Script
# Usage:
#   ./deploy.sh          # Full deployment (build + deploy)
#   ./deploy.sh --build  # Build only (push image)
#   ./deploy.sh --deploy # Deploy only (use existing image)
# ============================================================
set -e

# ── Configuration ──
PROJECT_ID="gen-lang-client-0997313422"
REGION="asia-east1"
SERVICE_NAME="audio-transcriber"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Audio Transcriber — Cloud Run Deploy  ${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  Project:  ${CYAN}${PROJECT_ID}${NC}"
echo -e "  Region:   ${CYAN}${REGION}${NC}"
echo -e "  Service:  ${CYAN}${SERVICE_NAME}${NC}"
echo ""

# Check gcloud auth
if ! gcloud auth print-identity-token &>/dev/null; then
  echo -e "${YELLOW}⚠ Not authenticated. Running gcloud auth login...${NC}"
  gcloud auth login
fi

# Set project
gcloud config set project "$PROJECT_ID" 2>/dev/null

# Enable required APIs (idempotent)
echo -e "${CYAN}📦 Enabling required APIs...${NC}"
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  2>/dev/null || true

# ── Build ──
if [[ "$1" != "--deploy" ]]; then
  echo ""
  echo -e "${CYAN}🔨 Building container image via Cloud Build...${NC}"
  echo -e "   (This builds in GCP, no local Docker needed)"
  echo ""
  gcloud builds submit \
    --tag "$IMAGE" \
    --timeout=1200s \
    --machine-type=e2-highcpu-8 \
    .
  echo -e "${GREEN}✅ Image built: ${IMAGE}${NC}"
fi

# ── Deploy ──
if [[ "$1" != "--build" ]]; then
  echo ""
  echo -e "${CYAN}🚀 Deploying to Cloud Run...${NC}"

  # Check if .env exists for secrets
  ENV_VARS=""
  if [ -f .env ]; then
    # Extract key env vars from .env
    GEMINI_KEY=$(grep -E '^GEMINI_API_KEY=' .env | cut -d= -f2-)
    SECRET=$(grep -E '^SECRET_KEY=' .env | cut -d= -f2-)
    JWT_SECRET=$(grep -E '^JWT_SECRET_KEY=' .env | cut -d= -f2- || echo "")

    ENV_VARS="GEMINI_API_KEY=${GEMINI_KEY}"
    ENV_VARS="${ENV_VARS},SECRET_KEY=${SECRET:-$(openssl rand -hex 32)}"
    ENV_VARS="${ENV_VARS},FLASK_ENV=production"

    if [ -n "$JWT_SECRET" ]; then
      ENV_VARS="${ENV_VARS},JWT_SECRET_KEY=${JWT_SECRET}"
    else
      ENV_VARS="${ENV_VARS},JWT_SECRET_KEY=$(openssl rand -hex 32)"
    fi
  else
    echo -e "${YELLOW}⚠ No .env file found. Set environment variables manually in Cloud Console.${NC}"
    ENV_VARS="FLASK_ENV=production"
  fi

  gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 2 \
    --timeout 600s \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 3 \
    --set-env-vars "$ENV_VARS" \
    --port 8080

  echo ""
  echo -e "${GREEN}════════════════════════════════════════${NC}"
  echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
  echo -e "${GREEN}════════════════════════════════════════${NC}"

  # Get service URL
  SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format="value(status.url)" 2>/dev/null)

  echo -e "  URL: ${CYAN}${SERVICE_URL}${NC}"
  echo ""

  # Health check
  echo -e "${CYAN}🏥 Running health check...${NC}"
  if curl -sf "${SERVICE_URL}/api/v2/health" | grep -q '"ok"'; then
    echo -e "${GREEN}  ✅ Backend healthy${NC}"
  else
    echo -e "${YELLOW}  ⚠ Backend health check failed (may need a moment to start)${NC}"
  fi

  if curl -sf "${SERVICE_URL}/" | grep -q '<html'; then
    echo -e "${GREEN}  ✅ Frontend accessible${NC}"
  else
    echo -e "${YELLOW}  ⚠ Frontend check failed${NC}"
  fi

  echo ""
  echo -e "  Open: ${CYAN}${SERVICE_URL}${NC}"
fi
