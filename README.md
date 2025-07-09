# APRA Information Chatbot 🏛️

An AI-powered chatbot that provides information about Australian Prudential Regulation Authority (APRA) standards and guidelines. Built using RAG (Retrieval-Augmented Generation) technology with Chainlit, LangChain, Pinecone, and OpenAI.

## 📋 About

This chatbot uses **publicly available APRA documentation** to answer questions about:
- APRA Connect Guide (May 2025)
- Prudential Standard CPS 230 (Operational Risk Management)
- Prudential Practice Guide CPG 230 (Operational Risk Management)
- Other APRA regulatory guidance

**Note**: This chatbot uses only public APRA documents and is intended for informational purposes.

## ✨ Features

- 🤖 **Conversational AI Interface** - Beautiful Chainlit UI for natural conversations
- 📚 **Vector Database Search** - Pinecone-powered document retrieval
- 🔍 **Source Citations** - Shows exact document sources for each answer
- 💬 **Memory-Enabled Chat** - Maintains conversation context
- 🏛️ **APRA-Specific Knowledge** - Focused on Australian prudential regulation

## 🚀 Live Demo

**Deployed on Railway**: [Your App URL]

## 🛠️ Technology Stack

- **Frontend**: Chainlit (Python-based chat interface)
- **Backend**: LangChain (LLM orchestration)
- **Vector Database**: Pinecone (document embeddings storage)
- **LLM**: OpenAI GPT-3.5-turbo
- **PDF Processing**: PyMuPDF
- **Deployment**: Railway (Docker container)

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.11+
- OpenAI API key
- Pinecone API key
- Docker (for deployment)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/xichaow/knowledgebase_chatbot.git
   cd knowledgebase_chatbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   ```

4. **Process PDFs and build vector store:**
   ```bash
   python vector_store.py
   ```
   This will process the APRA PDFs in the `pdf/` directory and create embeddings in Pinecone.

5. **Run the chatbot:**
   ```bash
   chainlit run app.py
   ```

6. **Open your browser** to `http://localhost:8000`

## 🐳 Deployment

### Railway Deployment (Recommended)

This app is configured for easy deployment on Railway:

1. **Fork this repository**
2. **Sign up at [Railway](https://railway.app)**
3. **Create new project** → Deploy from GitHub repo
4. **Add environment variables** in Railway dashboard:
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
5. **Deploy automatically** - Railway will build and deploy using the Dockerfile

**Cost**: ~$5/month on Railway

### Other Deployment Options

- **Google Cloud Run**: Use the included Dockerfile
- **AWS ECS/Fargate**: Container-ready deployment
- **DigitalOcean App Platform**: Simple container deployment
- **Render**: Alternative to Railway

## 📁 Project Structure

```
knowledgebase_chatbot/
├── app.py                      # Main Chainlit application
├── vector_store.py             # PDF processing and Pinecone setup
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── .env.example               # Environment variables template
├── .gitignore                 # Security exclusions
├── pdf/                       # APRA PDF documents
│   ├── APRA Connect Guide May 2025_0.pdf
│   ├── Prudential Practice Guide CPG 230.pdf
│   └── Prudential Standard CPS 230.pdf
└── README.md                  # This file
```

## 🔒 Security & Privacy

- **Environment Variables**: API keys stored securely, not in code
- **Public Documents Only**: Uses only publicly available APRA documents
- **No Sensitive Data**: PDF directory excluded from git repository
- **Secure Deployment**: Environment variables injected at runtime

## 💡 Usage Examples

Ask the chatbot questions like:

- *"What is CPS 230?"*
- *"How do I access APRA Connect?"*
- *"What are the operational risk management requirements?"*
- *"Explain prudential standards for operational risk"*
- *"How do I create returns in APRA Connect?"*

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

This project is open source. The APRA documents used are publicly available from the [APRA website](https://www.apra.gov.au/).

## ⚠️ Disclaimer

This chatbot provides information based on publicly available APRA documents. It is not official APRA guidance and should not be used as a substitute for professional advice or official APRA communications. Always refer to the official APRA website for the most current information.

---

**Built with ❤️ for the Australian financial services community**