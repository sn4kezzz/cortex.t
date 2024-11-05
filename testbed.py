#!/usr/bin/env -S poetry run python

import logging
import aioboto3
import os
import json
import asyncio

logging.basicConfig(level=logging.DEBUG)


async def invoke_bedrock_async():
    # Set up async boto3 session
    session = aioboto3.Session()
    async with session.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    ) as bedrock:

        body = json.dumps(
            {
                "max_tokens": 256,
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain Gradient descent and why does it works so well and where can ifind this inbiology",
                    }
                ],
                "anthropic_version": "bedrock-2023-05-31",
            }
        )
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

        # Asynchronously invoke the model and stream the response
        response = await bedrock.invoke_model_with_response_stream(
            body=body,
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
                    print(chunk["delta"]["text"], end="")


# Entry point for the async event loop
if __name__ == "__main__":
    asyncio.run(invoke_bedrock_async())
