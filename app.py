import os
import uuid
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Validate required environment variables for production
required_env_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these environment variables before starting the application.")
    exit(1)

print("✅ Required environment variables validated")

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings
from custom_retriever import CustomPineconeRetriever
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import chainlit as cl

# Import with error handling
try:
    from langfuse.langchain import CallbackHandler
    LANGFUSE_AVAILABLE = True
    print("✅ Langfuse callback handler available")
except ImportError:
    print("Warning: Langfuse not available. Evaluation features disabled.")
    CallbackHandler = None
    LANGFUSE_AVAILABLE = False

try:
    from evaluation_full import evaluate_conversation_background
    EVALUATION_AVAILABLE = True
    print("✅ Full evaluation system loaded (RAGAS + LLM Judge)")
except ImportError:
    try:
        from evaluation import evaluate_conversation_background
        EVALUATION_AVAILABLE = True
        print("✅ Simple evaluation system loaded (LLM Judge only)")
    except ImportError as e:
        print(f"Warning: Evaluation modules not available: {e}")
        EVALUATION_AVAILABLE = False

welcome_message = "Hello! I am your APRA Information Chatbot. Feel free to ask me any questions about APRA prudential standards, operational risk management, and regulatory guidance."
namespace = "apra-information"
index_name = "jr-lab"

# Initialize embeddings after environment variables are loaded
embeddings = OpenAIEmbeddings()

# Initialize Langfuse callback handler if available
langfuse_handler = None
if LANGFUSE_AVAILABLE and CallbackHandler:
    try:
        langfuse_handler = CallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        print("✅ Langfuse callback handler enabled")
    except Exception as e:
        print(f"⚠️ Could not initialize Langfuse callback: {e}")
        langfuse_handler = None
else:
    print("ℹ️ Langfuse callback disabled")

# template = """You are a research assistant. Your task is to read the relevant content from academic paper or journal articles, then convert it to plain languages
#             such that the general public can understand.\n\n"""


@cl.on_chat_start
async def start():
    await cl.Message(content=welcome_message).send()
    
    # Use custom retriever instead of broken PineconeVectorStore
    custom_retriever = CustomPineconeRetriever(
        index_name=index_name,
        namespace=namespace,
        k=4
    )
    
    # Test retrieval to verify it's working
    test_docs = custom_retriever.search_documents("CPS 230")
    print(f"🔍 Retrieval test: Found {len(test_docs)} documents")
    if test_docs:
        preview = test_docs[0].page_content[:100].replace('\n', ' ')
        print(f"📄 Sample content: {preview}...")
    else:
        print("⚠️ WARNING: No documents retrieved in test!")

    message_history = ChatMessageHistory()

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    # Use the custom retriever directly
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1, streaming=True),
        chain_type="stuff",
        retriever=custom_retriever,
        memory=memory,
        return_source_documents=True,
        # prompt=PromptTemplate.from_template(template),
    )
    cl.user_session.set("chain", chain)
    
    # Generate unique user session ID for tracing
    user_session_id = str(uuid.uuid4())
    cl.user_session.set("user_session_id", user_session_id)


@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")  # type: ConversationalRetrievalChain
    user_session_id = cl.user_session.get("user_session_id")

    # Generate unique trace ID for this conversation
    trace_id = str(uuid.uuid4())
    
    # Create Chainlit callback handler
    cb = cl.AsyncLangchainCallbackHandler()

    # Prepare callbacks
    callbacks = [cb]
    if langfuse_handler:
        callbacks.append(langfuse_handler)
    
    # Debug: Print the question being asked
    print(f"🔍 Question received: {message.content}")
    
    # Use "question" key instead of direct message content for ConversationalRetrievalChain
    res = await chain.acall(
        {"question": message.content}, 
        callbacks=callbacks,
        metadata={"trace_id": trace_id, "user_id": user_session_id}
    )
    answer = res["answer"]
    source_documents = res["source_documents"]  # type: List[Document]
    
    # Debug: Print retrieval results
    print(f"📊 Retrieved {len(source_documents)} source documents")
    for i, doc in enumerate(source_documents[:2], 1):
        preview = doc.page_content[:80].replace('\n', ' ')
        print(f"  {i}. {preview}...")

    text_elements = []  # type: List[cl.Text]
    context_texts = []

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            # Create the text element referenced in the message
            text_elements.append(
                cl.Text(
                    content=source_doc.page_content, name=source_name, display="side"
                )
            )
            # Collect context texts for evaluation
            context_texts.append(source_doc.page_content)
        
        source_names = [text_el.name for text_el in text_elements]

        if source_names:
            answer += f"\nSources: {', '.join(source_names)}"
        else:
            answer += "\nNo sources found"

    # Send response to user first
    await cl.Message(content=answer, elements=text_elements).send()
    
    # Run evaluation in background (non-blocking) if available
    if EVALUATION_AVAILABLE and context_texts:  # Only evaluate if we have context and evaluation is available
        try:
            evaluate_conversation_background(
                question=message.content,
                answer=answer,
                contexts=context_texts,
                trace_id=trace_id,
                user_id=user_session_id
            )
        except Exception as e:
            print(f"Warning: Evaluation failed: {e}")
