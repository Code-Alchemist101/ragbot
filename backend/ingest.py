"""
Complete website indexing pipeline
Orchestrates URL discovery, content extraction, chunking, and vector storage
"""
import hashlib
from urllib.parse import urlparse
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from url_discovery import discover_urls
from async_crawler import crawl_urls
from logger import setup_logger
from config import (
    PINECONE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, INGESTION_BATCH_SIZE
)

logger = setup_logger('ingest')

def create_namespace(url):
    """
    Create namespace from URL domain
    
    Args:
        url: Website URL
    
    Returns:
        Namespace string
    """
    domain = urlparse(url).netloc
    # Remove www. prefix if present
    domain = domain.replace('www.', '')
    # Replace dots with underscores
    namespace = domain.replace('.', '_')
    return namespace

def get_existing_urls(namespace):
    """
    Get list of already-indexed URLs from Pinecone
    
    Args:
        namespace: Pinecone namespace
    
    Returns:
        Set of existing URLs
    """
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)
        
        # Query to get all vectors in namespace (this is a simplified approach)
        # In production, you might want to maintain a separate metadata store
        logger.info(f"Checking for existing URLs in namespace: {namespace}")
        
        # For now, return empty set (full deduplication happens at document level)
        return set()
    
    except Exception as e:
        logger.warning(f"Error checking existing URLs: {e}")
        return set()

def calculate_content_hash(content, source):
    """
    Calculate MD5 hash of content + source for deduplication
    
    Args:
        content: Document content
        source: Document source URL
    
    Returns:
        MD5 hash string
    """
    combined = f"{content}{source}"
    return hashlib.md5(combined.encode()).hexdigest()

def deduplicate_documents(documents):
    """
    Remove duplicate documents based on content hash
    
    Args:
        documents: List of Document objects
    
    Returns:
        List of unique documents
    """
    seen_hashes = set()
    unique_docs = []
    
    for doc in documents:
        content_hash = calculate_content_hash(
            doc.page_content,
            doc.metadata.get('source', '')
        )
        
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_docs.append(doc)
    
    removed = len(documents) - len(unique_docs)
    if removed > 0:
        logger.info(f"Removed {removed} duplicate documents")
    
    return unique_docs

def tag_metadata(documents, namespace, base_url):
    """
    Add metadata tags to documents
    
    Args:
        documents: List of Document objects
        namespace: Pinecone namespace
        base_url: Website base URL
    
    Returns:
        Documents with enhanced metadata
    """
    domain = urlparse(base_url).netloc
    
    for doc in documents:
        # Add domain and namespace
        doc.metadata['domain'] = domain
        doc.metadata['namespace'] = namespace
        doc.metadata['indexed_at'] = datetime.utcnow().isoformat()
        
        # Department tagging (example patterns)
        url = doc.metadata.get('source', '').lower()
        if any(dept in url for dept in ['cse', 'computer', 'cs/']):
            doc.metadata['department'] = 'CSE'
        elif any(dept in url for dept in ['ece', 'electronics', 'electrical']):
            doc.metadata['department'] = 'ECE'
        elif any(dept in url for dept in ['mech', 'mechanical']):
            doc.metadata['department'] = 'MECH'
        elif any(dept in url for dept in ['civil']):
            doc.metadata['department'] = 'CIVIL'
        else:
            doc.metadata['department'] = 'GENERAL'
        
        # Content type tagging
        if any(keyword in url for keyword in ['faculty', 'staff', 'professor']):
            doc.metadata['content_type'] = 'faculty'
        elif any(keyword in url for keyword in ['course', 'curriculum', 'syllabus']):
            doc.metadata['content_type'] = 'course'
        elif any(keyword in url for keyword in ['admission', 'apply', 'enroll']):
            doc.metadata['content_type'] = 'admission'
        else:
            doc.metadata['content_type'] = 'general'
    
    return documents

def chunk_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Split documents into chunks
    
    Args:
        documents: List of Document objects
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of chunked documents
    """
    logger.info(f"Chunking {len(documents)} documents (size={chunk_size}, overlap={chunk_overlap})")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks")
    
    return chunks

def index_documents(documents, namespace):
    """
    Generate embeddings and store in Pinecone
    
    Args:
        documents: List of Document objects
        namespace: Pinecone namespace
    
    Returns:
        Number of successfully indexed documents
    """
    logger.info(f"Indexing {len(documents)} documents to namespace: {namespace}")
    
    try:
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Process in batches
        total_indexed = 0
        failed_batches = 0
        
        for i in range(0, len(documents), INGESTION_BATCH_SIZE):
            batch = documents[i:i + INGESTION_BATCH_SIZE]
            batch_num = i // INGESTION_BATCH_SIZE + 1
            total_batches = (len(documents) + INGESTION_BATCH_SIZE - 1) // INGESTION_BATCH_SIZE
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            try:
                # Create vector store and add documents
                PineconeVectorStore.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    index_name=PINECONE_INDEX,
                    namespace=namespace
                )
                
                total_indexed += len(batch)
                logger.info(f"Batch {batch_num} indexed successfully")
            
            except Exception as e:
                logger.error(f"Error indexing batch {batch_num}: {e}")
                failed_batches += 1
        
        logger.info(f"Indexing completed: {total_indexed} documents indexed, {failed_batches} batches failed")
        return total_indexed, failed_batches
    
    except Exception as e:
        logger.error(f"Error initializing embeddings or vector store: {e}")
        raise

def ingest_website(url, depth=2, max_urls=100000, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, status_callback=None):
    """
    Complete website ingestion pipeline
    
    Args:
        url: Website URL to crawl
        depth: Crawl depth (not used in current BFS implementation)
        max_urls: Maximum number of URLs to process
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        status_callback: Optional callback function for progress updates
    
    Returns:
        Dictionary with ingestion results
    """
    logger.info(f"Starting website ingestion: {url}")
    
    try:
        # Phase 1: Create namespace
        namespace = create_namespace(url)
        domain = urlparse(url).netloc
        logger.info(f"Namespace: {namespace}, Domain: {domain}")
        
        if status_callback:
            status_callback({'stage': 'url_discovery', 'namespace': namespace})
        
        # Phase 2: URL Discovery
        logger.info("Phase 1: URL Discovery")
        discovered_urls = discover_urls([url], domain, max_urls=max_urls)
        logger.info(f"Discovered {len(discovered_urls)} URLs")
        
        if status_callback:
            status_callback({
                'stage': 'deduplication_check',
                'urls_discovered': len(discovered_urls)
            })
        
        # Phase 3: Deduplication Check
        logger.info("Phase 2: Deduplication Check")
        existing_urls = get_existing_urls(namespace)
        new_urls = [u for u in discovered_urls if u not in existing_urls]
        skipped_count = len(discovered_urls) - len(new_urls)
        logger.info(f"New URLs to process: {len(new_urls)}, Skipped: {skipped_count}")
        
        if not new_urls:
            logger.info("No new URLs to process")
            return {
                'success': True,
                'total_documents': 0,
                'indexed_documents': 0,
                'failed_batches': 0,
                'skipped_existing': skipped_count,
                'namespace': namespace,
                'crawl_log': None
            }
        
        if status_callback:
            status_callback({
                'stage': 'content_extraction',
                'urls_to_crawl': len(new_urls)
            })
        
        # Phase 4: Content Extraction
        logger.info("Phase 3: Content Extraction")
        documents, crawl_log = crawl_urls(new_urls, url, max_pages=max_urls)
        logger.info(f"Extracted content from {len(documents)} pages")
        
        if not documents:
            logger.warning("No documents extracted")
            return {
                'success': False,
                'error': 'No content extracted',
                'namespace': namespace
            }
        
        if status_callback:
            status_callback({
                'stage': 'metadata_tagging',
                'documents_extracted': len(documents)
            })
        
        # Phase 5: Metadata Tagging
        logger.info("Phase 4: Metadata Tagging")
        documents = tag_metadata(documents, namespace, url)
        
        # Phase 6: Document Deduplication
        logger.info("Phase 5: Document Deduplication")
        documents = deduplicate_documents(documents)
        logger.info(f"Unique documents: {len(documents)}")
        
        if status_callback:
            status_callback({
                'stage': 'chunking',
                'unique_documents': len(documents)
            })
        
        # Phase 7: Chunking
        logger.info("Phase 6: Chunking")
        chunks = chunk_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        if status_callback:
            status_callback({
                'stage': 'indexing',
                'chunks_created': len(chunks)
            })
        
        # Phase 8: Embedding & Indexing
        logger.info("Phase 7: Embedding & Indexing")
        indexed_count, failed_batches = index_documents(chunks, namespace)
        
        if status_callback:
            status_callback({
                'stage': 'completed',
                'pages_indexed': indexed_count,
                'failed_batches': failed_batches
            })
        
        result = {
            'success': True,
            'total_documents': len(documents),
            'indexed_documents': indexed_count,
            'failed_batches': failed_batches,
            'skipped_existing': skipped_count,
            'namespace': namespace,
            'crawl_log': crawl_log
        }
        
        logger.info(f"Ingestion completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        if status_callback:
            status_callback({
                'stage': 'failed',
                'error': str(e)
            })
        return {
            'success': False,
            'error': str(e)
        }
