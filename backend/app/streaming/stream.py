import logging
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


async def stream_response(response_text: str) -> AsyncGenerator[str, None]:
    """Yield a text response in small chunks for streaming delivery."""
    if not isinstance(response_text, str):
        raise ValueError("response_text must be a string")

    text = response_text.strip()
    if not text:
        logger.warning("Streaming response received empty content")
        return

    chunk_size = 32
    for index in range(0, len(text), chunk_size):
        try:
            yield text[index : index + chunk_size]
        except Exception as exc:
            logger.exception("Streaming interruption while yielding tokens")
            raise RuntimeError("Streaming response interrupted") from exc
