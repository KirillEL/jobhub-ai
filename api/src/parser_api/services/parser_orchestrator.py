from parser_api.core.config import Settings
from parser_api.integrations.parser_client import (
    HttpParserClient,
    ParseCommandResult,
    ParserClientError,
)


class ParserOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = HttpParserClient(
            base_url=settings.parser_service_url,
            parse_path=settings.parser_http_parse_path,
            timeout_seconds=settings.parser_http_timeout_seconds,
            retries=settings.parser_http_retries,
            retry_backoff_seconds=settings.parser_http_retry_backoff_seconds,
            auth_header_name=settings.parser_auth_header_name,
            auth_token=settings.parser_auth_token,
        )

    async def trigger_parse(
        self,
        query: str,
        pages: int,
        *,
        city: str | None = None,
        experience: str | None = None,
        schedule: str | None = None,
    ) -> ParseCommandResult:
        try:
            return await self.client.parse(
                query=query,
                pages=pages,
                city=city,
                experience=experience,
                schedule=schedule,
            )
        except ParserClientError:
            raise
