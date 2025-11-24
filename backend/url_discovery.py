"""
Fast URL discovery using BFS traversal
Discovers all URLs on a domain without extracting content
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import time
from logger import setup_logger

logger = setup_logger('url_discovery')

# File extensions to skip
SKIP_EXTENSIONS = {
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp4', '.avi', '.mov', '.wmv',
    '.mp3', '.wav', '.ogg',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.exe', '.dmg', '.pkg', '.deb', '.rpm'
}

def normalize_url(url):
    """
    Normalize URL by removing fragments and sorting query parameters
    
    Args:
        url: URL to normalize
    
    Returns:
        Normalized URL string
    """
    parsed = urlparse(url)
    # Remove fragment and rebuild URL
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip('/'),
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))
    return normalized

def should_skip_url(url):
    """
    Check if URL should be skipped based on extension
    
    Args:
        url: URL to check
    
    Returns:
        True if URL should be skipped
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Check file extensions
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            return True
    
    return False

def is_same_domain(url, domain):
    """
    Check if URL belongs to the same domain
    
    Args:
        url: URL to check
        domain: Target domain
    
    Returns:
        True if URL is on same domain
    """
    parsed = urlparse(url)
    return parsed.netloc == domain or parsed.netloc == f'www.{domain}' or parsed.netloc == domain.replace('www.', '')

def fetch_links(url, domain, timeout=10):
    """
    Fetch all links from a single URL
    
    Args:
        url: URL to fetch
        domain: Target domain for filtering
        timeout: Request timeout in seconds
    
    Returns:
        Set of discovered URLs
    """
    links = set()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code != 200:
            logger.debug(f"Non-200 status for {url}: {response.status_code}")
            return links
        
        # Only process HTML content
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            return links
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all anchor tags
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Normalize URL
            normalized = normalize_url(absolute_url)
            
            # Filter: same domain, not skipped extension
            if is_same_domain(normalized, domain) and not should_skip_url(normalized):
                links.add(normalized)
        
        logger.debug(f"Found {len(links)} links on {url}")
        
    except requests.Timeout:
        logger.warning(f"Timeout fetching {url}")
    except requests.RequestException as e:
        logger.warning(f"Error fetching {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {e}")
    
    return links

def discover_urls(seed_urls, domain, max_urls=100000, max_workers=10, timeout=10):
    """
    Discover all URLs on a domain using BFS traversal
    
    Args:
        seed_urls: List of starting URLs
        domain: Target domain
        max_urls: Maximum number of URLs to discover
        max_workers: Number of concurrent workers
        timeout: Request timeout per URL
    
    Returns:
        List of discovered URLs
    """
    logger.info(f"Starting URL discovery for domain: {domain}")
    logger.info(f"Seed URLs: {seed_urls}")
    
    # Initialize data structures
    discovered = set()
    visited = set()
    queue = deque()
    
    # Add seed URLs to queue
    for url in seed_urls:
        normalized = normalize_url(url)
        if not should_skip_url(normalized):
            queue.append(normalized)
            discovered.add(normalized)
    
    start_time = time.time()
    
    # BFS traversal with concurrent fetching
    while queue and len(discovered) < max_urls:
        # Get batch of URLs to process
        batch_size = min(max_workers, len(queue))
        current_batch = [queue.popleft() for _ in range(batch_size)]
        
        # Mark as visited
        visited.update(current_batch)
        
        # Fetch links concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(fetch_links, url, domain, timeout): url
                for url in current_batch
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    links = future.result()
                    
                    # Add new links to queue
                    for link in links:
                        if link not in discovered and link not in visited:
                            discovered.add(link)
                            queue.append(link)
                            
                            # Check if we've reached the limit
                            if len(discovered) >= max_urls:
                                break
                
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
        
        # Log progress
        if len(discovered) % 100 == 0:
            elapsed = time.time() - start_time
            rate = len(discovered) / elapsed if elapsed > 0 else 0
            logger.info(f"Discovered {len(discovered)} URLs ({rate:.1f} URLs/sec)")
    
    elapsed = time.time() - start_time
    logger.info(f"URL discovery completed: {len(discovered)} URLs in {elapsed:.1f}s")
    
    return list(discovered)
