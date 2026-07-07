from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from core.log import log


@dataclass
class RequestInfo:
    url: str
    method: str
    headers: dict[str, str]
    post_data: str | None = None
    resource_type: str = ""
    timestamp: float = 0.0


@dataclass
class ResponseInfo:
    url: str
    status: int
    headers: dict[str, str]
    body: str = ""
    timestamp: float = 0.0


class NetworkInterceptor:
    """Intercept, mock, and monitor network requests."""

    def __init__(self, page):
        self._page = page
        self._routes: list[dict[str, Any]] = []
        self._captured_requests: list[RequestInfo] = []
        self._captured_responses: list[ResponseInfo] = []
        self._blocked_patterns: list[str] = []
        self._active = False

    async def start(self) -> None:
        if self._active:
            return
        self._active = True
        await self._page.route("**/*", self._handle_route)

    async def stop(self) -> None:
        if not self._active:
            return
        self._active = False
        await self._page.unroute("**/*", self._handle_route)

    async def _handle_route(self, route) -> None:
        req = route.request
        url = req.url
        for pattern in self._blocked_patterns:
            if pattern in url:
                await route.abort()
                return
        for r in self._routes:
            if r["pattern"] in url and r["method"] in (req.method, "*"):
                if r.get("action") == "fulfill":
                    await route.fulfill(
                        status=r.get("status", 200),
                        headers=r.get("headers", {}),
                        body=r.get("body", ""),
                    )
                    return
                if r.get("action") == "abort":
                    await route.abort()
                    return
        req_info = RequestInfo(
            url=url,
            method=req.method,
            headers=dict(req.headers),
            post_data=req.post_data,
            resource_type=req.resource_type,
        )
        self._captured_requests.append(req_info)
        response = await route.fetch()
        resp_info = ResponseInfo(
            url=url,
            status=response.status,
            headers=dict(response.headers),
            timestamp=response.headers.get("date", ""),
        )
        self._captured_responses.append(resp_info)
        await route.fulfill(response=response)

    def mock_response(
        self,
        url_pattern: str,
        body: str = "",
        status: int = 200,
        headers: dict[str, str] | None = None,
        method: str = "*",
    ) -> None:
        self._routes.append({
            "pattern": url_pattern,
            "method": method,
            "action": "fulfill",
            "status": status,
            "headers": headers or {"Content-Type": "application/json"},
            "body": body,
        })
        log.info("Mock added: %s -> %d", url_pattern, status)

    def mock_json(self, url_pattern: str, data: Any, status: int = 200) -> None:
        self.mock_response(
            url_pattern,
            body=json.dumps(data),
            status=status,
            headers={"Content-Type": "application/json"},
        )

    def block_urls(self, patterns: list[str]) -> None:
        self._blocked_patterns.extend(patterns)
        log.info("Blocking %d URL patterns", len(patterns))

    def block_unmatched(self, allowed_patterns: list[str]) -> None:
        async def handler(route) -> None:
            url = route.request.url
            for p in allowed_patterns:
                if p in url:
                    await route.continue_()
                    return
            await route.abort()
        self._page.route("**/*", handler)

    def get_requests(self, method: str = "", url_pattern: str = "") -> list[RequestInfo]:
        results = self._captured_requests
        if method:
            results = [r for r in results if r.method == method]
        if url_pattern:
            results = [r for r in results if url_pattern in r.url]
        return results

    def get_responses(self, status: int = 0) -> list[ResponseInfo]:
        if status:
            return [r for r in self._captured_responses if r.status == status]
        return list(self._captured_responses)

    def clear_captures(self) -> None:
        self._captured_requests.clear()
        self._captured_responses.clear()

    def clear_mocks(self) -> None:
        self._routes.clear()

    async def wait_for_request(self, url_pattern: str, timeout: float = 5000) -> RequestInfo | None:
        deadline = asyncio.get_event_loop().time() + timeout / 1000
        while asyncio.get_event_loop().time() < deadline:
            for r in self._captured_requests:
                if url_pattern in r.url:
                    return r
            await asyncio.sleep(0.1)
        return None

    async def wait_for_response(
        self, url_pattern: str, timeout: float = 5000,
    ) -> ResponseInfo | None:
        deadline = asyncio.get_event_loop().time() + timeout / 1000
        while asyncio.get_event_loop().time() < deadline:
            for r in self._captured_responses:
                if url_pattern in r.url:
                    return r
            await asyncio.sleep(0.1)
        return None
