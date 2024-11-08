import os
import random
import bittensor as bt
from groq import AsyncGroq
from starlette.types import Send
from .base import Provider
from miner.config import config
from cortext.protocol import StreamPrompting


class Groq(Provider):
    def __init__(self, synapse):
        super().__init__(synapse)

        # Define the pool of API keys directly as a list
        self.api_keys = [
            "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",
            # "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",
            # "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",
            # "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",
            # "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",
            # "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",
            # "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",
        ]

        # Check if any API keys were loaded
        if not self.api_keys:
            raise ValueError(
                "No API keys found. Please set the GROQ_API_KEYS environment variable or define keys in the code."
            )

    async def _prompt(self, synapse: StreamPrompting, send: Send):
        # Select a random API key from the pool
        selected_api_key = random.choice(self.api_keys)
        print(f"Selected API key: {selected_api_key}")

        # Instantiate the AsyncGroq client with the randomly selected API key
        groq_client = AsyncGroq(timeout=config.ASYNC_TIME_OUT, api_key=selected_api_key)

        # Prepare the streaming arguments
        stream_kwargs = {
            "messages": self.messages,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "seed": self.seed,
            "stream": True,
        }

        try:
            # Execute the request using the selected API key
            stream = await groq_client.chat.completions.create(**stream_kwargs)
        except Exception as err:
            bt.logging.exception(err)
            return

        buffer = []
        n = 1
        async for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            buffer.append(token)
            # bt.logging.info(f"Streamed token: {token}")
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
