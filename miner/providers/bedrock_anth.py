import bittensor as bt
from anthropic import AsyncAnthropic
from starlette.types import Send
import base64
import httpx

from .base import Provider
from miner.config import config
from cortext.protocol import StreamPrompting
from miner.error_handler import error_handler
import aioboto3
import json
import os
from starlette.types import Send
from anthropic import AsyncAnthropic
from miner.error_handler import error_handler


class Anthropic(Provider):
    def __init__(self, synapse):
        super().__init__(synapse)
        self.aws_session = aioboto3.Session()

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
                    image_data = base64.b64encode(httpx.get(image_url).content).decode(
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

        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": filtered_messages,
            "max_tokens": self.max_tokens,
        }

        if system_prompt:
            native_request["system"] = system_prompt
        # print(native_request)

        request_body = json.dumps(native_request)
        # bt.logging.info(request_body)

        if self.model == "claude-3-5-sonnet-20240620":
            model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        elif self.model == "claude-3-haiku-20240307":
            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        elif self.model == "claude-3-opus-20240229":
            model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        else:
            model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

        bt.logging.info(f"using {model_id}")
        async with self.aws_session.client(
            service_name="bedrock-runtime",
            #region_name="eu-central-1",
            region_name="us-east-1",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        ) as bedrock:
            response = await bedrock.invoke_model_with_response_stream(
                body=request_body,
                modelId=model_id,
            )
            async for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])

                if chunk["type"] == "message_delta":
                    print(f"\nStop reason: {chunk['delta']['stop_reason']}")
                    print(f"Stop sequence: {chunk['delta']['stop_sequence']}")
                    print(f"Output tokens: {chunk['usage']['output_tokens']}")
                if chunk["type"] == "content_block_delta":
                    if chunk["delta"]["type"] == "text_delta":
                        # print(chunk["delta"]["text"], end="")
                        token = chunk["delta"]["text"]
                        await send(
                            {
                                "type": "http.response.body",
                                "body": token.encode("utf-8"),
                                "more_body": True,
                            }
                        )
                        bt.logging.info(f"Streamed tokens: {token}")

        await send({"type": "http.response.body", "body": b"", "more_body": False})

    def image_service(self, synapse):
        pass

    def embeddings_service(self, synapse):
        pass
