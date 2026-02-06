"""
Advanced IP and User-Agent Rotation System for Memory Parasite Protocol.
Converted to async using httpx for seamless integration.
"""

import random
import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """Proxy configuration with health tracking"""
    host: str
    port: int
    protocol: str = 'http'
    username: Optional[str] = None
    password: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    response_time: float = 0.0
    is_active: bool = True
    
    def get_url(self) -> str:
        """Get httpx compatible proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0.0

class UserAgentRotator:
    """Advanced user-agent rotation with browser fingerprinting"""
    
    CHROME_VERSIONS = list(range(120, 130))
    PLATFORMS = [
        ('Windows NT 10.0; Win64; x64', 'Windows'),
        ('Macintosh; Intel Mac OS X 10_15_7', 'macOS'),
        ('X11; Linux x86_64', 'Linux'),
    ]
    
    def __init__(self, mobile_ratio: float = 0.2):
        self.mobile_ratio = mobile_ratio
    
    def get_random_agent(self) -> str:
        version = random.choice(self.CHROME_VERSIONS)
        platform, _ = random.choice(self.PLATFORMS)
        return f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"

class ProxyManager:
    """Manage proxy pool with health checking and rotation"""
    
    def __init__(self, proxies: List[ProxyConfig]):
        self.proxies = proxies
        self.available_proxies = [p for p in proxies if p.is_active]
        self.lock = asyncio.Lock()
    
    async def get_proxy(self, strategy: str = 'round_robin') -> Optional[ProxyConfig]:
        async with self.lock:
            if not self.available_proxies:
                return None
            if strategy == 'round_robin' and self.available_proxies:
                proxy = self.available_proxies.pop(0)
                self.available_proxies.append(proxy)
                return proxy
            return random.choice(self.available_proxies) if self.available_proxies else None

    async def report_success(self, proxy: ProxyConfig, response_time: float):
        proxy.success_count += 1
        proxy.response_time = (proxy.response_time + response_time) / 2 if proxy.response_time else response_time

    async def report_failure(self, proxy: ProxyConfig):
        proxy.failure_count += 1
        if proxy.failure_count > 5 and proxy.success_rate < 20:
            proxy.is_active = False
            async with self.lock:
                if proxy in self.available_proxies:
                    self.available_proxies.remove(proxy)

class AsyncIPRotator:
    """Async IP rotator with anti-detection features using httpx"""
    
    def __init__(
        self,
        proxies: List[ProxyConfig],
        rotation_strategy: str = 'round_robin',
        request_delay: Tuple[float, float] = (0.5, 1.5),
        max_retries: int = 3
    ):
        self.proxy_manager = ProxyManager(proxies)
        self.ua_rotator = UserAgentRotator()
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.rotation_strategy = rotation_strategy
        self.domain_locks = {}
        self.free_provider = FreeProxyProvider()
        
        # Background task will be started lazily on first async request
        self._background_task: Optional[asyncio.Task] = None
        self._background_task_started = False

    def _ensure_background_task(self):
        """Start background refresh task if not already running (called from async context)."""
        if self._background_task_started:
            return
        try:
            loop = asyncio.get_running_loop()
            self._background_task = loop.create_task(self._background_refresh_loop())
            self._background_task_started = True
            logger.info("Background proxy refresh task started")
        except RuntimeError:
            # No running event loop - will try again on next request
            pass

    async def _background_refresh_loop(self):
        """Periodically refresh proxies from free providers."""
        while True:
            try:
                # Refresh if empty OR if 24 hours passed
                is_empty = len(self.proxy_manager.proxies) == 0
                is_expired = not self.free_provider.last_refreshed or \
                             (datetime.now() - self.free_provider.last_refreshed).total_seconds() > 86400
                
                if is_empty or is_expired:
                    reason = "Pool is empty" if is_empty else "Daily refresh"
                    logger.info(f"{reason} triggered. Fetching proxies...")
                    new_proxies = await self.free_provider.fetch_proxies()
                    if new_proxies:
                        await self.update_proxies(new_proxies)
                
            except Exception as e:
                logger.error(f"Proxy background refresh failed: {e}")
            
            # If empty, check again sooner (e.g. 1 min) until we get some. 
            # Otherwise, check every hour.
            wait_time = 60 if len(self.proxy_manager.proxies) == 0 else 3600
            await asyncio.sleep(wait_time)

    async def update_proxies(self, new_proxies: List[ProxyConfig]):
        """Replace the current proxy pool with new ones."""
        async with self.proxy_manager.lock:
            # Keep track of working ones or just replace? 
            # Replacing is cleaner for "fresh" daily lists
            self.proxy_manager.proxies = new_proxies
            self.proxy_manager.available_proxies = [p for p in new_proxies if p.is_active]
            logger.info(f"Proxy pool updated. Total: {len(new_proxies)}")

    async def _get_domain_lock(self, domain: str):
        if domain not in self.domain_locks:
            self.domain_locks[domain] = asyncio.Lock()
        return self.domain_locks[domain]

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[httpx.Response]:
        # Ensure background task is running (lazy initialization)
        self._ensure_background_task()
        
        domain = urlparse(url).netloc
        domain_lock = await self._get_domain_lock(domain)
        
        async with domain_lock:
            for attempt in range(self.max_retries):
                proxy = await self.proxy_manager.get_proxy(self.rotation_strategy)
                user_agent = self.ua_rotator.get_random_agent()
                
                headers = kwargs.get('headers', {})
                headers['User-Agent'] = user_agent
                kwargs['headers'] = headers
                
                proxy_mounts = None
                if proxy:
                    proxy_mounts = {"http://": proxy.get_url(), "https://": proxy.get_url()}

                try:
                    start_time = asyncio.get_event_loop().time()
                    async with httpx.AsyncClient(mounts=proxy_mounts, timeout=30.0) as client:
                        response = await client.request(method, url, **kwargs)
                        duration = asyncio.get_event_loop().time() - start_time
                        
                        if response.status_code == 429:
                            await asyncio.sleep(2 ** attempt)
                            continue
                            
                        if proxy:
                            await self.proxy_manager.report_success(proxy, duration)
                            
                        await asyncio.sleep(random.uniform(*self.request_delay))
                        return response
                        
                except Exception as e:
                    logger.error(f"IPRotator Error: {e}")
                    if proxy:
                        await self.proxy_manager.report_failure(proxy)
                    await asyncio.sleep(1.0)
            return None

    async def get(self, url: str, **kwargs): return await self.request('GET', url, **kwargs)
    async def post(self, url: str, **kwargs): return await self.request('POST', url, **kwargs)

class FreeProxyProvider:
    """Fetch free proxies from public sources like TheSpeedX/SOCKS-List"""
    
    SOURCES = [
        ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", "http"),
        ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", "socks4"),
        ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "socks5"),
        ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt", "http"),
    ]
    
    def __init__(self):
        self.last_refreshed = None

    async def fetch_proxies(self) -> List[ProxyConfig]:
        proxies = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for url, proto in self.SOURCES:
                try:
                    logger.info(f"Fetching {proto} proxies from {url}...")
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        count = 0
                        for line in resp.text.splitlines():
                            line = line.strip()
                            if ':' in line and not line.startswith('#'):
                                try:
                                    parts = line.split(':')
                                    if len(parts) >= 2:
                                        host, port = parts[0], parts[1]
                                        proxies.append(ProxyConfig(
                                            host=host.strip(), 
                                            port=int(port.strip()),
                                            protocol=proto
                                        ))
                                        count += 1
                                except: continue
                        logger.info(f"Loaded {count} proxies from {proto} source.")
                except Exception as e:
                    logger.error(f"Error fetching from {url}: {e}")
        
        self.last_refreshed = datetime.now()
        return proxies
