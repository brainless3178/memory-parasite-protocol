import os
import time
import logging
import asyncio
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=5, backoff=2):
    """Decorator for retrying failed async operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {wait_time}s...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
            
            logger.error(f"{func.__name__} failed after {max_retries} attempts")
            raise last_exception
        return wrapper
    return decorator

def validate_environment():
    """Ensure all required environment variables are set"""
    required_vars = [
        'GROQ_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'GITHUB_TOKEN',
        'SOLANA_PRIVATE_KEY'
    ]
    
    load_dotenv()
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info("All environment variables validated successfully")

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls, time_window):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self._lock = asyncio.Lock()
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self._lock:
                now = time.time()
                # Remove old calls
                self.calls = [c for c in self.calls if c > now - self.time_window]
                
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.time_window - (now - self.calls[0])
                    if sleep_time > 0:
                        logger.info(f"Rate limit reached for {func.__name__}, sleeping for {sleep_time:.2f}s")
                        await asyncio.sleep(sleep_time)
                
                self.calls.append(time.time())
            return await func(*args, **kwargs)
        return wrapper
