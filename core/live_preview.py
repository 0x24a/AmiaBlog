from typing import Optional
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect
from core.models import Post
from core.posts import PostsManager
import asyncio


class LivePreviewManager:
    def __init__(self, posts_manager: PostsManager) -> None:
        self._show_warning()
        self.posts_manager = posts_manager
        # inject
        self.posts_manager._post_reload_hook = self._post_reload_hook
        self.subscriptions = {}
        self.running = True
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def router(self, websocket: WebSocket) -> None:
        self._loop = asyncio.get_running_loop()
        await websocket.accept()
        try:
            while self.running:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                if data.get("type") == "subscribe":
                    slug = data.get("slug")
                    if slug not in self.posts_manager.posts.keys():
                        await websocket.send_json(
                            {
                                "type": "error",
                                "key": "subscription_failed::key_not_found",
                            }
                        )
                        continue
                    self.subscriptions[slug] = self.subscriptions.get(slug, []) + [
                        websocket
                    ]
                    await websocket.send_json(
                        {"type": "success", "key": "subscription_succeeded"}
                    )
                    continue
        except WebSocketDisconnect:
            for _, value in self.subscriptions.items():
                if websocket in value:
                    value.remove(websocket)

    def _post_reload_hook(self, slug: str, before: Optional[Post], after: Post) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        if before is None or before.metadata != after.metadata:
            # Metadata changed, trigger refresh since they are rendered server-side
            for ws in self.subscriptions.get(slug, []):
                asyncio.run_coroutine_threadsafe(
                    ws.send_json({"type": "refresh"}), self._loop
                )
            return

        # Content changed, send markdown raw text
        for ws in self.subscriptions.get(slug, []):
            asyncio.run_coroutine_threadsafe(
                ws.send_json({"type": "update", "markdown": after.content}), self._loop
            )

    def _show_warning(self) -> None:
        logger.warning(
            "...\nWARNING: You have enabled live preview. \nThis is a experimental feature and should NOT be used in production since it may cause performance drop and security issues.\nPlease make sure this is a development environment only."
        )
