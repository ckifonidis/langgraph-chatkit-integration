#!/bin/bash

# Push LangGraph ChatKit Integration Docker Image to Azure Container Registry
# This script builds and pushes the unified image (frontend + backend) to ACR

set -e

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <tag>" >&2
  echo "Example: $0 v1.0.0" >&2
  exit 1
fi

# Azure Container Registry Configuration
ACR_REGISTRY="idpdirectacr.azurecr.io"
ACR_USERNAME="${ACR_USERNAME:-57e01612-19cd-45f3-bdd6-0797a12371b8}"
ACR_PASSWORD="${ACR_PASSWORD:-jJM8Q~HrVYm~S8lEPlcKAsJosaHErONqR3pqxa2j}"
TAG="$1"

# Image Configuration
IMAGE_NAME="langgraph-chatkit-integration"
DOCKERFILE="Dockerfile"
LOCAL_IMAGE="${IMAGE_NAME}:${TAG}"
REMOTE_IMAGE="${ACR_REGISTRY}/${IMAGE_NAME}:${TAG}"
REMOTE_IMAGE_LATEST="${ACR_REGISTRY}/${IMAGE_NAME}:latest"

echo "🚀 Starting LangGraph ChatKit deployment to Azure Container Registry..."
echo "📍 Registry: $ACR_REGISTRY"
echo "🏷️  Tag: $TAG"
echo "🖼️  Image: $IMAGE_NAME"
echo ""

# Step 1: Validate required files
echo "🔍 Validating required files..."
if [[ ! -f "$DOCKERFILE" ]]; then
    echo "❌ Dockerfile not found in current directory"
    echo "Please run this script from the examples/langgraph-integration directory"
    exit 1
fi

if [[ ! -f "docker-compose.yml" ]]; then
    echo "⚠️  Warning: docker-compose.yml not found"
fi

if [[ ! -d "backend/app" ]]; then
    echo "❌ Backend directory not found"
    exit 1
fi

if [[ ! -d "frontend/src" ]]; then
    echo "❌ Frontend directory not found"
    exit 1
fi

echo "✅ All required files found"
echo ""

# Step 2: Setup buildx for cross-platform builds
echo "🔨 Setting up cross-platform builder..."
docker buildx create --use --name langgraph-builder 2>/dev/null || docker buildx use langgraph-builder
echo "✅ Builder configured"
echo ""

# Step 3: Login to Azure Container Registry
echo "🔐 Logging into Azure Container Registry..."
echo "$ACR_PASSWORD" | docker login $ACR_REGISTRY --username $ACR_USERNAME --password-stdin

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to login to Azure Container Registry"
    echo "Please check your credentials in environment variables:"
    echo "  - ACR_USERNAME"
    echo "  - ACR_PASSWORD"
    exit 1
fi

echo "✅ Successfully logged into ACR"
echo ""

# Step 4: Load environment variables for build
echo "📦 Loading build configuration..."
if [[ -f ".env" ]]; then
  export $(cat .env | grep -E "^VITE_" | xargs)
  echo "✅ Loaded VITE_* variables from .env"
else
  echo "⚠️  No .env file found, using environment variables"
fi

# Step 5: Build the image for linux/amd64 (Azure standard)
echo "🔨 Building LangGraph ChatKit image for linux/amd64..."
echo "   This may take several minutes (multi-stage build)..."
echo "   Build args:"
echo "     - VITE_CHATKIT_API_DOMAIN_KEY=${VITE_CHATKIT_API_DOMAIN_KEY:-<not set>}"
echo "     - VITE_GOOGLE_MAPS_API_KEY=${VITE_GOOGLE_MAPS_API_KEY:-<not set>}"
echo ""

docker buildx build \
  --platform linux/amd64 \
  -f "${DOCKERFILE}" \
  -t "${LOCAL_IMAGE}" \
  --build-arg VITE_CHATKIT_API_DOMAIN_KEY="${VITE_CHATKIT_API_DOMAIN_KEY}" \
  --build-arg VITE_GOOGLE_MAPS_API_KEY="${VITE_GOOGLE_MAPS_API_KEY}" \
  . \
  --load

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to build image"
    exit 1
fi

echo "✅ Image built successfully: ${LOCAL_IMAGE}"
echo ""

# Step 6: Tag the images
echo "🏷️  Tagging images..."

# Tag with specified version
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to tag image with version ${TAG}"
    exit 1
fi

# Also tag as latest
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE_LATEST}"

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to tag image as latest"
    exit 1
fi

echo "✅ Images tagged:"
echo "   - ${REMOTE_IMAGE}"
echo "   - ${REMOTE_IMAGE_LATEST}"
echo ""

# Step 7: Push the versioned image
echo "📤 Pushing versioned image (${TAG})..."
docker push "${REMOTE_IMAGE}"

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to push versioned image"
    exit 1
fi

echo "✅ Versioned image pushed successfully"
echo ""

# Step 8: Push the latest tag
echo "📤 Pushing latest tag..."
docker push "${REMOTE_IMAGE_LATEST}"

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to push latest tag"
    exit 1
fi

echo "✅ Latest tag pushed successfully"
echo ""

# Step 9: Verify the images in ACR
echo "🔍 Verifying images in registry..."
echo "   Checking: ${REMOTE_IMAGE}"

# Try to inspect the remote image
docker manifest inspect "${REMOTE_IMAGE}" > /dev/null 2>&1

if [[ $? -eq 0 ]]; then
    echo "✅ Image verified in registry"
else
    echo "⚠️  Could not verify image (this is normal for some registries)"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   Registry: ${ACR_REGISTRY}"
echo "   Image: ${IMAGE_NAME}"
echo "   Tags:"
echo "     - ${TAG}"
echo "     - latest"
echo ""
echo "   Full image URLs:"
echo "     - ${REMOTE_IMAGE}"
echo "     - ${REMOTE_IMAGE_LATEST}"
echo ""
echo "💡 Next steps:"
echo ""
echo "   1. Deploy to Azure Container Instances:"
echo "      az container create \\"
echo "        --resource-group <your-rg> \\"
echo "        --name langgraph-chatkit \\"
echo "        --image ${REMOTE_IMAGE} \\"
echo "        --dns-name-label langgraph-chatkit \\"
echo "        --ports 80 \\"
echo "        --environment-variables \\"
echo "          LANGGRAPH_API_URL='https://your-api.com' \\"
echo "          LANGGRAPH_ASSISTANT_ID='agent' \\"
echo "        --registry-login-server ${ACR_REGISTRY} \\"
echo "        --registry-username ${ACR_USERNAME} \\"
echo "        --registry-password <your-password>"
echo ""
echo "   2. Or deploy to Azure Kubernetes Service (AKS):"
echo "      kubectl set image deployment/langgraph-chatkit \\"
echo "        langgraph-chatkit=${REMOTE_IMAGE}"
echo ""
echo "   3. Or update your docker-compose.yml:"
echo "      image: ${REMOTE_IMAGE}"
echo ""
echo "   4. Required environment variables in production:"
echo "      - LANGGRAPH_API_URL (your LangGraph API endpoint)"
echo "      - LANGGRAPH_ASSISTANT_ID (default: agent)"
echo "      - VITE_LANGGRAPH_CHATKIT_API_DOMAIN_KEY (ChatKit domain key)"
echo ""
echo "✨ Deployment complete!"
