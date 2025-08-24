# Deploying APRA Chatbot to Render.com 🚀

## Prerequisites

Before deploying, make sure you have:

1. **GitHub Repository**: Your code pushed to a GitHub repo
2. **API Keys**:
   - OpenAI API key from https://platform.openai.com/api-keys
   - Pinecone API key from https://app.pinecone.io/
   - Langfuse keys from https://us.cloud.langfuse.com/

## Step-by-Step Deployment

### 1. Create Render Account
- Go to https://render.com
- Sign up with GitHub account

### 2. Create New Web Service
- Click "New" → "Web Service"
- Connect your GitHub repository
- Select your chatbot repository

### 3. Configure Build Settings
Render should auto-detect the configuration from `render.yaml`, but verify:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `chainlit run app.py --host 0.0.0.0 --port $PORT`
- **Python Version**: `3.11.13`

### 4. Set Environment Variables
In Render dashboard, go to "Environment" and add:

```
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

### 5. Deploy
- Click "Create Web Service"
- Render will automatically build and deploy your app
- Build process takes ~5-10 minutes

### 6. Access Your App
Once deployed, your app will be available at:
`https://your-service-name.onrender.com`

## Features Included in Deployment ✨

✅ **APRA Document Retrieval** - Full vector database access  
✅ **Custom Pinecone Retriever** - Fixed retrieval system  
✅ **Evaluation System** - RAGAS + LLM Judge  
✅ **Langfuse Integration** - Observability and monitoring  
✅ **Conversational Memory** - Multi-turn conversations  
✅ **Source Citations** - Document references  

## Troubleshooting

### Build Issues
- Check that `requirements.txt` includes all dependencies
- Verify Python version is 3.11.13
- Check build logs in Render dashboard

### Runtime Issues
- Verify all environment variables are set
- Check service logs in Render dashboard
- Ensure Pinecone index "jr-lab" exists with namespace "apra-information"

### Performance
- Free tier has limitations (750 hours/month)
- Consider upgrading to paid plan for production use

## Monitoring

Once deployed, you can monitor:
- **Render Dashboard**: Service health, logs, metrics
- **Langfuse**: Conversation quality, evaluation scores
- **Application Logs**: Debug information and errors

## Updates

To update your deployed app:
1. Push changes to your GitHub repository
2. Render will automatically redeploy
3. No manual intervention needed

---

Your APRA Information Chatbot is now ready for production! 🎉