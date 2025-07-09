#!/bin/bash

# AWS Lightsail Container Deployment Script
# Make sure you have AWS CLI configured with proper credentials

SERVICE_NAME="knowledgebase-chatbot"
CONTAINER_NAME="chatbot"
IMAGE_NAME="knowledgebase-chatbot:latest"

echo "🚀 Starting deployment to AWS Lightsail..."

# Step 1: Build the Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

# Step 2: Push image to Lightsail
echo "📤 Pushing image to Lightsail..."
aws lightsail push-container-image \
    --service-name $SERVICE_NAME \
    --label $CONTAINER_NAME \
    --image $IMAGE_NAME

# Step 3: Get the image URI
echo "🔍 Getting image URI..."
IMAGE_URI=$(aws lightsail get-container-images --service-name $SERVICE_NAME --query 'containerImages[0].image' --output text)

# Step 4: Update deployment configuration with actual image URI
echo "⚙️ Updating deployment configuration..."
sed "s|knowledgebase-chatbot:latest|$IMAGE_URI|g" lightsail-deployment.json > deployment-config.json

# Step 5: Deploy the container
echo "🚀 Deploying container..."
aws lightsail create-container-service-deployment \
    --service-name $SERVICE_NAME \
    --cli-input-json file://deployment-config.json

echo "✅ Deployment initiated! Check AWS Lightsail console for status."
echo "📱 Your app will be available at: https://$SERVICE_NAME.service.lightsail.aws.amazon.com"

# Clean up
rm deployment-config.json