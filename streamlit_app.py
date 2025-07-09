import streamlit as st
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import os
from pinecone import Pinecone as PineconeClient

# Configure page
st.set_page_config(
    page_title="APRA Information Chatbot",
    page_icon="🏛️",
    layout="wide"
)

# App title and description
st.title("🏛️ APRA Information Chatbot")
st.markdown("Feel free to ask me any questions about APRA prudential standards, operational risk management, and regulatory guidance.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=ChatMessageHistory(),
        return_messages=True,
    )
if "chain" not in st.session_state:
    # Initialize the conversation chain
    namespace = "apra-information"
    embeddings = OpenAIEmbeddings()
    index_name = "jr-lab"
    
    # Initialize Pinecone
    pc = PineconeClient(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(index_name)
    
    vectorstore = Pinecone(
        index=index,
        embedding=embeddings,
        text_key="source",
        namespace=namespace,
    )
    
    st.session_state.chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        memory=st.session_state.memory,
        return_source_documents=True,
    )

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"]):
                    st.text_area(f"Source {i+1}", source, height=100, key=f"source_{len(st.session_state.messages)}_{i}")

# Chat input
if prompt := st.chat_input("Ask me about APRA regulations..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chain({"question": prompt})
                answer = response["answer"]
                source_documents = response.get("source_documents", [])
                
                # Display assistant response
                st.markdown(answer)
                
                # Prepare sources for storage
                sources = []
                if source_documents:
                    with st.expander("📚 Sources"):
                        for i, doc in enumerate(source_documents):
                            st.text_area(f"Source {i+1}", doc.page_content, height=100, key=f"source_new_{i}")
                            sources.append(doc.page_content)
                
                # Add assistant message to chat history
                assistant_message = {"role": "assistant", "content": answer}
                if sources:
                    assistant_message["sources"] = sources
                st.session_state.messages.append(assistant_message)
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.info(
        "This chatbot uses AI to answer questions about:\n"
        "- APRA Connect Guide\n"
        "- Prudential Standard CPS 230\n"
        "- Operational Risk Management\n"
        "- Other APRA regulatory guidance"
    )
    
    st.header("Clear Chat")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.rerun()