import asyncio
import bittensor as bt
from openai import AsyncOpenAI
from starlette.types import Send
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from .base import Provider
from miner.config import config
from cortext.protocol import StreamPrompting
from miner.error_handler import error_handler
import os


class Anthropic(Provider):
    def __init__(self, synapse):
        super().__init__(synapse)
        self.openai_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",  # OpenRouter API base URL
            timeout=config.ASYNC_TIME_OUT,
            api_key=os.getenv(
                "OPENROUTER_API_KEY", ""
            ),  # OpenRouter API Key from config
        )

    @error_handler
    async def _prompt(self, synapse: StreamPrompting, send: Send):
        """
        Send a text-based prompt to the OpenRouter Anthropic API and stream the response.
        """
        message = self.messages[0]

        filtered_message: ChatCompletionMessageParam = {
            "role": message["role"],
            "content": message.get("content", ""),
        }

        if self.model == "claude-3-5-sonnet-20240620":
            model_id = "anthropic/claude-3.5-sonnet-20240620"
        elif self.model == "claude-3-haiku-20240307":
            model_id = "anthropic/claude-3-haiku"
        elif self.model == "claude-3-opus-20240229":
            model_id = "anthropic/claude-3.5-sonnet-20240620"
        else:
            model_id = "anthropic/claude-3.5-sonnet-20240620"
        try:
            #  OpenRouter
            response = await self.openai_client.chat.completions.create(
                model=model_id,  # OpenRouter
                messages=[filtered_message],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
        except Exception as err:
            bt.logging.exception(err)
            response = []

        # Stream response tokens
        import asyncio


import bittensor as bt
from openai import AsyncOpenAI
from starlette.types import Send
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from .base import Provider
from miner.config import config
from cortext.protocol import StreamPrompting
from miner.error_handler import error_handler
import os


class Anthropic(Provider):
    def __init__(self, synapse):
        super().__init__(synapse)
        self.openai_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",  # OpenRouter API base URL
            timeout=config.ASYNC_TIME_OUT,
            api_key=os.getenv(
                "OPENROUTER_API_KEY", ""
            ),  # OpenRouter API Key from config
        )

    @error_handler
    async def _prompt(self, synapse: StreamPrompting, send: Send):
        """
        Send a text-based prompt to the OpenRouter Anthropic API and stream the response.
        """
        message = self.messages[0]

        filtered_message: ChatCompletionMessageParam = {
            "role": message["role"],
            "content": message.get("content", ""),
        }

        if self.model == "claude-3-5-sonnet-20240620":
            model_id = "anthropic/claude-3.5-sonnet-20240620"
        elif self.model == "claude-3-haiku-20240307":
            model_id = "anthropic/claude-3-haiku"
        elif self.model == "claude-3-opus-20240229":
            model_id = "anthropic/claude-3.5-sonnet-20240620"
        else:
            model_id = "anthropic/claude-3.5-sonnet-20240620"
        try:
            #  OpenRouter
            response = await self.openai_client.chat.completions.create(
                model=model_id,  # OpenRouter
                messages=[filtered_message],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
        except Exception as err:
            bt.logging.exception(err)
            response = []

        # Stream response tokens
        buffer = []
        n = 1
        async for chunk in response:
            token = chunk.choices[0].delta.content or ""
            buffer.append(token)
            if len(buffer) == n:
                joined_buffer = "".join(buffer)
                await send(
                    {
                        "type": "http.response.body",
                        "body": joined_buffer.encode("utf-8"),
                        "more_body": True,
                    }
                )
                # bt.logging.info(f"Streamed tokens: {joined_buffer}")
                buffer = []

        if buffer:
            joined_buffer = "".join(buffer)
            await send(
                {
                    "type": "http.response.body",
                    "body": joined_buffer.encode("utf-8"),
                    "more_body": False,
                }
            )
        #        bt.logging.info(f"Streamed tokens: {joined_buffer}")
        await send(
            {
                "type": "http.response.body",
                "body": b"",
                "more_body": False,
            }
        )

    def image_service(self, synapse):
        pass

    def embeddings_service(self, synapse):
        pass

    def image_service(self, synapse):
        pass

    def embeddings_service(self, synapse):
        pass
