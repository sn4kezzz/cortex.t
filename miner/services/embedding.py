import bittensor as bt
from cortext.protocol import Embeddings
from typing import Tuple

from .base import BaseService
from cortext import EMBEDDING_BLACKLIST_STAKE


class EmbeddingService(BaseService):
    def __init__(self, metagraph, blacklist_amt=EMBEDDING_BLACKLIST_STAKE):
        super().__init__(metagraph, blacklist_amt)

    async def forward_fn(self, synapse: Embeddings):
        provider = self.get_instance_of_provider(synapse.provider)(synapse)
        service = provider.embeddings_service if provider is not None else None
        bt.logging.info("embedding service is executed.")
        return await service(synapse)

    def blacklist_fn(self, synapse: Embeddings) -> Tuple[bool, str]:
        blacklist = self.base_blacklist(synapse)
        bt.logging.info(blacklist[1])
        return blacklist
