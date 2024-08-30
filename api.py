import bittensor as bt
import pydantic
from enum import Enum
from typing import AsyncIterator, Dict, List, Literal, Optional
from starlette.responses import StreamingResponse
import asyncio
import traceback
import random


class StreamPrompting(bt.StreamingSynapse):

    messages: List[Dict[str, str]] = pydantic.Field(
        ...,
        title="Messages",
        description="A list of messages in the StreamPrompting scenario, "
                    "each containing a role and content. Immutable.",
        allow_mutation=False,
    )

    required_hash_fields: List[str] = pydantic.Field(
        ["messages"],
        title="Required Hash Fields",
        description="A list of required fields for the hash.",
        allow_mutation=False,
    )

    seed: int = pydantic.Field(
        default="1234",
        title="Seed",
        description="Seed for text generation. This attribute is immutable and cannot be updated.",
    )

    temperature: float = pydantic.Field(
        default=0.0001,
        title="Temperature",
        description="Temperature for text generation. "
                    "This attribute is immutable and cannot be updated.",
    )

    max_tokens: int = pydantic.Field(
        default=2048,
        title="Max Tokens",
        description="Max tokens for text generation. "
                    "This attribute is immutable and cannot be updated.",
    )

    top_p: float = pydantic.Field(
        default=0.001,
        title="Top_p",
        description="Top_p for text generation. The sampler will pick one of "
                    "the top p percent tokens in the logit distirbution. "
                    "This attribute is immutable and cannot be updated.",
    )

    top_k: int = pydantic.Field(
        default=1,
        title="Top_k",
        description="Top_k for text generation. Sampler will pick one of  "
                    "the k most probablistic tokens in the logit distribtion. "
                    "This attribute is immutable and cannot be updated.",
    )

    completion: str = pydantic.Field(
        None,
        title="Completion",
        description="Completion status of the current StreamPrompting object. "
                    "This attribute is mutable and can be updated.",
    )

    provider: str = pydantic.Field(
        default="OpenAI",
        title="Provider",
        description="The provider to use when calling for your response. "
                    "Options: OpenAI, Anthropic, Gemini",
    )

    model: str = pydantic.Field(
        default="gpt-3.5-turbo",
        title="model",
        description="The model to use when calling provider for your response.",
    )

    uid: int = pydantic.Field(
        default=3,
        title="uid",
        description="The UID to send the streaming synapse to",
    )

    timeout: int = pydantic.Field(
        default=60,
        title="timeout",
        description="The timeout for the dendrite of the streaming synapse",
    )

    streaming: bool = pydantic.Field(
        default=True,
        title="streaming",
        description="whether to stream the output",
    )

    async def process_streaming_response(self, response: StreamingResponse) -> AsyncIterator[str]:
        if self.completion is None:
            self.completion = ""
        async for chunk in response.content.iter_any():
            tokens = chunk.decode("utf-8")
            for token in tokens:
                if token:
                    self.completion += token
            yield tokens

    def deserialize(self) -> str:
        return self.completion

    def extract_response_json(self, response: StreamingResponse) -> dict:
        headers = {
            k.decode("utf-8"): v.decode("utf-8")
            for k, v in response.__dict__["_raw_headers"]
        }

        def extract_info(prefix: str) -> dict[str, str]:
            return {
                key.split("_")[-1]: value
                for key, value in headers.items()
                if key.startswith(prefix)
            }

        return {
            "name": headers.get("name", ""),
            "timeout": float(headers.get("timeout", 0)),
            "total_size": int(headers.get("total_size", 0)),
            "header_size": int(headers.get("header_size", 0)),
            "dendrite": extract_info("bt_header_dendrite"),
            "axon": extract_info("bt_header_axon"),
            "messages": self.messages,
            "completion": self.completion,
            "provider": self.provider,
            "model": self.model,
            "seed": self.seed,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "uid": self.uid,
            "timeout": self.timeout,
        }

async def query_miner(dendrite, axon_to_use, synapse, timeout, streaming):
    try:
        print(f"calling vali axon {axon_to_use} to miner uid {synapse.uid} for query {synapse.messages}")
        responses = dendrite.query(
            axons=[axon_to_use],
            synapse=synapse,
            deserialize=False,
            timeout=timeout,
            streaming=streaming,
        )
        return await handle_response(responses)
    except Exception as e:
        print(f"Exception during query: {traceback.format_exc()}")
        return None

async def handle_response(responses):
    full_response = ""
    try:
        for resp in responses:
            async for chunk in resp:
                if isinstance(chunk, str):
                    full_response += chunk
                    print(chunk, end='', flush=True)
                else:
                    print(f"\n\nFinal synapse: {chunk}\n")
    except Exception as e:
        print(f"Error processing response for uid {e}")
    return full_response

async def main():
    print("synching metagraph, this takes way too long.........")
    meta = bt.metagraph( netuid=24, network="test" )
    print("metagraph synched!")

    # This needs to be your validator wallet that is running your subnet 18 validator
    wallet = bt.wallet( name="validator", hotkey="default" )
    dendrite = bt.dendrite( wallet=wallet )
    vali_uid = meta.hotkeys.index( wallet.hotkey.ss58_address)
    axon_to_use = meta.axons[vali_uid]

    # This is the question to send your validator to send your miner.
    prompt = "explain bittensor to me like I am 5"
    messages = [{'role': 'user', 'content': prompt}]

    # You can edit this to pick a specific miner uid, just change miner_uid to the uid that you desire.
    # Currently, it just picks a random miner form the top 100 uids.
    # top_miners_to_use = 100
    # top_miner_uids = meta.I.argsort(descending=True)[:top_miners_to_use]
    # miner_uid = random.choice(top_miner_uids)
    miner_uid = 3

    synapse = StreamPrompting(
    messages = messages,
    # get available providers and models from : https://github.com/corcel-api/cortex.t/blob/2807988d66523a432f6159d46262500b060f13dc/cortext/protocol.py#L238
    provider = "Anthropic", 
    model = "claude-3-5-sonnet-20240620",
    uid = miner_uid,
    )
    timeout = 60
    streaming = True
    print("querying miner")
    response = await query_miner(dendrite, axon_to_use, synapse, timeout, streaming)

if __name__ == "__main__":
    asyncio.run(main())