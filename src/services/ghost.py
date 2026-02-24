import structlog
from httpx import AsyncClient
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.ghost_jwt import make_ghost_jwt

logger = structlog.get_logger()


class GhostClient:
    """Async Ghost Admin API client."""

    def __init__(self, ghost_url: str, admin_api_key: str):
        self.ghost_url = ghost_url.rstrip("/")
        self.admin_api_key = admin_api_key
        self.api_base = f"{self.ghost_url}/ghost/api/admin"
        self._client = AsyncClient(timeout=30.0)

    def _auth_headers(self) -> dict:
        token = make_ghost_jwt(self.admin_api_key)
        return {"Authorization": f"Ghost {token}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def upload_image(self, file_bytes: bytes, filename: str) -> str:
        """Upload image to Ghost via POST /images/upload, return public URL."""
        url = f"{self.api_base}/images/upload/"
        files = {"file": (filename, file_bytes, "image/jpeg")}
        response = await self._client.post(
            url, headers=self._auth_headers(), files=files
        )
        response.raise_for_status()
        data = response.json()
        return data["images"][0]["url"]

    @staticmethod
    def _is_ghost_id(value: str) -> bool:
        """Ghost IDs are 24-char hex strings (MongoDB ObjectId)."""
        return len(value) == 24 and all(c in "0123456789abcdef" for c in value)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_page(self, page_id: str) -> dict:
        """Get page by ID or slug (needed for updated_at for concurrent updates)."""
        if self._is_ghost_id(page_id):
            url = f"{self.api_base}/pages/{page_id}/"
        else:
            url = f"{self.api_base}/pages/slug/{page_id}/"
        response = await self._client.get(url, headers=self._auth_headers())
        response.raise_for_status()
        data = response.json()
        return data["pages"][0]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def update_page_html(self, page_id: str, html: str) -> None:
        """Replace full HTML content of a Ghost page via PUT /pages/{id}."""
        # First get current page (resolves slug → real ID + updated_at)
        page = await self.get_page(page_id)
        real_id = page["id"]
        updated_at = page["updated_at"]

        url = f"{self.api_base}/pages/{real_id}/"
        payload = {
            "pages": [
                {
                    "html": html,
                    "updated_at": updated_at,
                }
            ]
        }
        response = await self._client.put(
            url,
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        logger.info("Ghost page updated", page_id=real_id)

    async def close(self) -> None:
        await self._client.aclose()
