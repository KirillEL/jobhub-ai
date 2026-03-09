import asyncio
import logging
from dataclasses import dataclass

import httpx

# Shared client for connection pooling; closed on app shutdown via close_parser_http_client()
_shared_client: httpx.AsyncClient | None = None


def get_parser_http_client(timeout_seconds: int = 120) -> httpx.AsyncClient:
    """Return a shared AsyncClient for parser HTTP calls (connection pooling)."""
    global _shared_client
    if _shared_client is None:
        _shared_client = httpx.AsyncClient(
            timeout=timeout_seconds,
            limits=httpx.Limits(max_keepalive_connections=4, max_connections=10),
        )
    return _shared_client


async def close_parser_http_client() -> None:
    """Close the shared parser HTTP client. Call from app lifespan on shutdown."""
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None


class ParserClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParseCommandResult:
    message: str
    collected: int
    vacancies: list[dict[str, object]]


class HttpParserClient:
    def __init__(
        self,
        base_url: str,
        parse_path: str,
        timeout_seconds: int,
        retries: int,
        retry_backoff_seconds: float,
        auth_header_name: str,
        auth_token: str | None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.parse_path = parse_path
        self.timeout_seconds = timeout_seconds
        self.retries = max(0, retries)
        self.retry_backoff_seconds = max(0.1, retry_backoff_seconds)
        self.auth_header_name = auth_header_name
        self.auth_token = auth_token
        self._client = get_parser_http_client(timeout_seconds)
        self._logger = logging.getLogger(__name__)

    async def parse(
        self,
        query: str,
        pages: int,
        *,
        city: str | None = None,
        experience: str | None = None,
        schedule: str | None = None,
    ) -> ParseCommandResult:
        url = f"{self.base_url}{self.parse_path}"
        payload: dict[str, object] = {"query": query, "pages": pages}
        if city:
            payload["city"] = city
        if experience:
            payload["experience"] = experience
        if schedule:
            payload["schedule"] = schedule
        headers: dict[str, str] = {}
        if self.auth_token:
            headers[self.auth_header_name] = self.auth_token
        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                response = await self._client.post(url, json=payload, headers=headers)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.retries:
                    await asyncio.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                response.raise_for_status()
                return self._parse_payload(response)
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise ParserClientError(f"Parser HTTP call failed: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                if status in {429, 500, 502, 503, 504} and attempt < self.retries:
                    await asyncio.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise ParserClientError(f"Parser HTTP call failed with status {status}") from exc
            except httpx.HTTPError as exc:
                raise ParserClientError(f"Parser HTTP call failed: {exc}") from exc

        raise ParserClientError(f"Parser HTTP call failed: {last_error}")

    def _parse_payload(self, response: httpx.Response) -> ParseCommandResult:
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserClientError("Parser returned non-JSON response") from exc
        if not isinstance(data, dict):
            raise ParserClientError("Parser returned invalid payload format")

        raw_vacancies = data.get("vacancies")
        if raw_vacancies is None:
            raw_vacancies = []
        if not isinstance(raw_vacancies, list):
            raise ParserClientError("Parser returned invalid vacancies payload")

        vacancies: list[dict[str, object]] = []
        for item in raw_vacancies:
            normalized = self._normalize_vacancy(item)
            if normalized is None:
                continue
            vacancies.append(normalized)

        if raw_vacancies and not vacancies:
            raise ParserClientError("Parser returned vacancies payload but all items are invalid")

        try:
            collected = int(data.get("collected", len(vacancies)))
        except (TypeError, ValueError):
            collected = len(vacancies)
        message = str(data.get("message", "Parsing started via HTTP"))
        return ParseCommandResult(message=message, collected=collected, vacancies=vacancies)

    def _normalize_vacancy(self, item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            self._logger.warning("Skip vacancy item: expected object, got %s", type(item).__name__)
            return None
        external_id = str(item.get("external_id", "")).strip()
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        if not external_id or not title or not url:
            self._logger.warning("Skip vacancy item: missing external_id/title/url")
            return None

        def _to_float(value: object) -> float | None:
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        return {
            "external_id": external_id,
            "title": title,
            "company": item.get("company"),
            "city": item.get("city"),
            "salary_from": _to_float(item.get("salary_from")),
            "salary_to": _to_float(item.get("salary_to")),
            "currency": item.get("currency"),
            "experience": item.get("experience"),
            "schedule": item.get("schedule"),
            "url": url,
            "published_at": item.get("published_at"),
            "description": item.get("description"),
        }
