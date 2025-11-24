"""
RAG Pipeline with LangChain Expression Language (LCEL)
History-aware retrieval and generation using Google Gemini
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.messages import HumanMessage, AIMessage
from logger import setup_logger
from config import (
    GOOGLE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL,
    LLM_MODEL, LLM_TEMPERATURE, RETRIEVAL_TOP_K
)

logger = setup_logger('rag')

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    google_api_key=GOOGLE_API_KEY,
    convert_system_message_to_human=True
)

# Initialize embeddings (CRITICAL: Must match ingest.py)
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Initialize vector store
vector_store = PineconeVectorStore(
    index_name=PINECONE_INDEX,
    embedding=embeddings
)

# Contextualize question prompt
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# QA system prompt
qa_system_prompt = """You are a helpful AI assistant. Answer the question based on the provided context with specific details.

Context from the website:
{context}

Instructions:
- Provide SPECIFIC and DETAILED information based on the context
- Include names, email addresses, phone numbers, and other precise details when available
- If the context doesn't contain relevant information, say "I don't have specific information about that in my knowledge base."
- Be concise but complete
- Use a friendly, professional tone
- Prioritize factual accuracy over general statements
- If you're unsure, acknowledge it rather than making assumptions"""

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

def format_docs(docs):
    """
    Format retrieved documents into a single string
    
    Args:
        docs: List of Document objects
    
    Returns:
        Formatted context string
    """
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain(namespace=None):
    """
    Create RAG chain with optional namespace filtering
    
    Args:
        namespace: Optional Pinecone namespace for filtering
    
    Returns:
        Configured RAG chain
    """
    # Create retriever with namespace
    search_kwargs = {"k": RETRIEVAL_TOP_K}
    if namespace:
        search_kwargs["namespace"] = namespace
    
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    
    # History-aware retriever
    # If there's chat history, reformulate the question first
    # Otherwise, use the question directly
    history_aware_retriever = RunnableBranch(
        (
            lambda x: len(x.get("chat_history", [])) > 0,
            contextualize_q_prompt | llm | StrOutputParser() | retriever,
        ),
        (lambda x: x["input"]) | retriever,
    )
    
    # Full RAG chain
    rag_chain = (
        RunnablePassthrough.assign(
            context=history_aware_retriever | format_docs
        )
        | qa_prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def get_answer(question, filters=None, namespace=None, chat_history=None):
    """
    Get answer for a question (non-streaming)
    
    Args:
        question: User question
        filters: Optional metadata filters (not implemented)
        namespace: Optional Pinecone namespace
        chat_history: List of previous messages
    
    Returns:
        Answer string
    """
    try:
        # Convert chat history to LangChain message format
        formatted_history = []
        if chat_history:
            for msg in chat_history:
                if msg.get('role') == 'user':
                    formatted_history.append(HumanMessage(content=msg['content']))
                elif msg.get('role') == 'assistant':
                    formatted_history.append(AIMessage(content=msg['content']))
        
        # Get RAG chain
        chain = get_rag_chain(namespace)
        
        # Invoke chain
        answer = chain.invoke({
            "input": question,
            "chat_history": formatted_history
        })
        
        logger.info(f"Generated answer for question: {question[:50]}...")
        return answer
    
    except Exception as e:
        logger.error(f"Error generating answer: {e}", exc_info=True)
        raise

def get_answer_stream(question, filters=None, namespace=None, chat_history=None):
    """
    Get streaming answer for a question
    
    Args:
        question: User question
        filters: Optional metadata filters (not implemented)
        namespace: Optional Pinecone namespace
        chat_history: List of previous messages
    
    Yields:
        Answer chunks
    """
    try:
        # Convert chat history to LangChain message format
        formatted_history = []
        if chat_history:
            for msg in chat_history:
                if msg.get('role') == 'user':
                    formatted_history.append(HumanMessage(content=msg['content']))
                elif msg.get('role') == 'assistant':
                    formatted_history.append(AIMessage(content=msg['content']))
        
        # Get RAG chain
        chain = get_rag_chain(namespace)
        
        # Stream response
        logger.info(f"Streaming answer for question: {question[:50]}...")
        for chunk in chain.stream({
            "input": question,
            "chat_history": formatted_history
        }):
            yield chunk
    
    except Exception as e:
        logger.error(f"Error streaming answer: {e}", exc_info=True)
        raise
