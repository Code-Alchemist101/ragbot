"""
Async content extraction from URLs
High-speed HTML parsing and text extraction using aiohttp
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import time
from logger import setup_logger
from langchain_core.documents import Document

logger = setup_logger('async_crawler')

async def fetch_content(session, url, semaphore, timeout=15):
    """
    Fetch and extract content from a single URL
    
    Args:
        session: aiohttp ClientSession
        url: URL to fetch
        semaphore: Asyncio semaphore for concurrency control
        timeout: Request timeout in seconds
    
    Returns:
        Document object or None
    """
    async with semaphore:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True) as response:
                if response.status != 200:
                    logger.debug(f"Non-200 status for {url}: {response.status}")
                    return None
                
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    logger.debug(f"Skipping non-HTML content: {url}")
                    return None
                
                html = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                    element.decompose()
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else urlparse(url).path
                
                # Extract main content
                # Try to find main content area
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
                
                if main_content:
                    text = main_content.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)
                
                # Clean up whitespace
                text = ' '.join(text.split())
                
                # Skip if content is too short
                if len(text) < 100:
                    logger.debug(f"Skipping short content: {url}")
                    return None
                
                # Create Document object
                doc = Document(
                    page_content=text,
                    metadata={
                        'source': url,
                        'title': title_text,
                        'extracted_at': datetime.utcnow().isoformat()
                    }
                )
                
                logger.debug(f"Extracted {len(text)} chars from {url}")
                return doc
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"Client error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing {url}: {e}")
            return None

async def crawl_batch(urls, base_url, concurrency=20, timeout=15):
    """
    Crawl a batch of URLs concurrently
    
    Args:
        urls: List of URLs to crawl
        base_url: Base URL for the website
        concurrency: Maximum concurrent requests
        timeout: Request timeout per URL
    
    Returns:
        List of Document objects
    """
    semaphore = asyncio.Semaphore(concurrency)
    documents = []
    
    # Create timeout for entire session
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        tasks = [fetch_content(session, url, semaphore, timeout) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Document):
                documents.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
    
    return documents

async def crawl_urls_async(urls, base_url, max_pages=100000, concurrency=20):
    """
    Crawl multiple URLs asynchronously with progress logging
    
    Args:
        urls: List of URLs to crawl
        base_url: Base URL for the website
        max_pages: Maximum number of pages to crawl
        concurrency: Maximum concurrent requests
    
    Returns:
        Tuple of (documents, log_file_path)
    """
    logger.info(f"Starting async crawl of {len(urls)} URLs")
    logger.info(f"Concurrency: {concurrency}, Max pages: {max_pages}")
    
    start_time = time.time()
    all_documents = []
    
    # Limit URLs to max_pages
    urls_to_crawl = urls[:max_pages]
    
    # Process in batches to avoid overwhelming the system
    batch_size = 100
    total_batches = (len(urls_to_crawl) + batch_size - 1) // batch_size
    
    for i in range(0, len(urls_to_crawl), batch_size):
        batch = urls_to_crawl[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} URLs)")
        
        documents = await crawl_batch(batch, base_url, concurrency)
        all_documents.extend(documents)
        
        # Log progress
        elapsed = time.time() - start_time
        rate = len(all_documents) / elapsed if elapsed > 0 else 0
        logger.info(f"Progress: {len(all_documents)} documents extracted ({rate:.1f} docs/sec)")
    
    elapsed = time.time() - start_time
    logger.info(f"Crawl completed: {len(all_documents)} documents in {elapsed:.1f}s")
    
    # Create log file path (for compatibility)
    log_file = f"logs/crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    return all_documents, log_file

def crawl_urls(urls, base_url, max_pages=100000, concurrency=20):
    """
    Synchronous wrapper for async crawling
    
    Args:
        urls: List of URLs to crawl
        base_url: Base URL for the website
        max_pages: Maximum number of pages to crawl
        concurrency: Maximum concurrent requests
    
    Returns:
        Tuple of (documents, log_file_path)
    """
    return asyncio.run(crawl_urls_async(urls, base_url, max_pages, concurrency))
