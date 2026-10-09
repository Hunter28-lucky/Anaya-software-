from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import httpx
import logging

logger = logging.getLogger(__name__)


class RobotsValidator:
    """Safe, cached parser for robots.txt."""

    def __init__(self, user_agent: str = "LeadQualifyAI-Verifier"):
        self.user_agent = user_agent
        self._cache = {}

    async def can_fetch(self, client: httpx.AsyncClient, url: str) -> bool:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain in self._cache:
                rp = self._cache[domain]
                if rp is None:
                    return True
                return rp.can_fetch(self.user_agent, url)

            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            try:
                resp = await client.get(robots_url, timeout=5.0)
                if resp.status_code == 200 and resp.text:
                    rp = RobotFileParser()
                    rp.parse(resp.text.splitlines())
                    self._cache[domain] = rp
                    return rp.can_fetch(self.user_agent, url)
                else:
                    # Missing or error -> default allow
                    self._cache[domain] = None
                    return True
            except Exception:
                self._cache[domain] = None
                return True
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True
