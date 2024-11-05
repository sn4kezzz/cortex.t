import bittensor as bt
from anthropic import AnthropicVertex
from starlette.types import Send
import base64
import httpx
import json
import os
import asyncio
import concurrent.futures
import functools

from .base import Provider
from miner.config import config
from cortext.protocol import StreamPrompting
from miner.error_handler import error_handler


class Anthropic(Provider):
    def __init__(self, synapse):
        super().__init__(synapse)
        # Initialize the Google Anthropic Vertex client
        self.location = os.getenv("GOOGLE_REGION", "us-east5")
        # self.location = os.getenv("GOOGLE_REGION", "europe-west1")
        self.project_id = os.getenv("GOOGLE_PROJECT_ID", "platinum-wave-424308-p6")
        self.client = AnthropicVertex(region=self.location, project_id=self.project_id)

    async def gmtc(self, messages: list):
        system_prompt = None
        filtered_messages = []
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            else:
                message_to_append = {
                    "role": message["role"],
                    "content": [],
                }
                if message.get("image"):
                    image_url = message.get("image")
                    async with httpx.AsyncClient() as client:
                        image_response = await client.get(image_url)
                        image_response.raise_for_status()
                        image_data = base64.b64encode(image_response.content).decode(
                            "utf-8"
                        )
                    message_to_append["content"].append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        }
                    )
                if message.get("content"):
                    message_to_append["content"].append(
                        {
                            "type": "text",
                            "text": message["content"],
                        }
                    )
                filtered_messages.append(message_to_append)
        return filtered_messages, system_prompt

    @error_handler
    async def _prompt(self, synapse: StreamPrompting, send: Send):
        filtered_messages, system_prompt = await self.gmtc(self.messages)

        request_payload = {
            # "anthropic_version": "bedrock-2023-05-31",
            "messages": filtered_messages,
            "max_tokens": self.max_tokens,
        }

        if system_prompt:
            request_payload["system"] = system_prompt

        if self.model == "claude-3-5-sonnet-20240620":
            model_id = "claude-3-5-sonnet@20240620"
        elif self.model == "claude-3-haiku-20240307":
            model_id = "claude-3-haiku@20240307"
        elif self.model == "claude-3-opus-20240229":
            model_id = "claude-3-opus@20240229"
        else:
            model_id = "claude-3-5-sonnet@20240620"

        bt.logging.info(f"Using model: {model_id}")

        loop = asyncio.get_event_loop()

        # Define a synchronous function to handle streaming
        def stream_sync(send_coroutine, model_id, messages, max_tokens):
            try:
                with self.client.messages.stream(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model_id,
                ) as stream:
                    for text in stream.text_stream:
                        # Schedule the send_coroutine in the event loop
                        asyncio.run_coroutine_threadsafe(
                            send_coroutine(
                                {
                                    "type": "http.response.body",
                                    "body": text.encode("utf-8"),
                                    "more_body": True,
                                }
                            ),
                            loop,
                        )
                        # bt.logging.info(f"Streamed tokens: {text}")
            except Exception as e:
                bt.logging.error(f"Error during streaming: {e}")
                # Send the termination message in case of error
                asyncio.run_coroutine_threadsafe(
                    send_coroutine(
                        {
                            "type": "http.response.body",
                            "body": b"",
                            "more_body": False,
                        }
                    ),
                    loop,
                )
                raise e
            # Send the termination message after streaming completes
            asyncio.run_coroutine_threadsafe(
                send_coroutine(
                    {
                        "type": "http.response.body",
                        "body": b"",
                        "more_body": False,
                    }
                ),
                loop,
            )

        # Create a coroutine for sending messages
        send_coroutine = functools.partial(send)

        # Run the synchronous streaming function in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                stream_sync,
                send_coroutine,
                model_id,
                filtered_messages,
                self.max_tokens,
            )

    def image_service(self, synapse):
        pass

    def embeddings_service(self, synapse):
        pass
