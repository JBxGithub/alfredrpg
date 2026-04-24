import httpx
from typing import List, Optional, Dict, Any
from app.core.config import get_settings
from app.schemas import (
    ChainSummary, ProtocolSummary, YieldPool,
    ProtocolTVLResponse, ChainTVLResponse, TVLHistoryPoint
)
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class DeFiLlamaAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DeFiLlamaClient:
    def __init__(self):
        self.base_url = settings.DEFILAMA_API_BASE
        self.timeout = settings.DEFILAMA_API_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        client = await self._get_client()
        for attempt in range(settings.MAX_RETRIES):
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    await self.close()
                    raise DeFiLlamaAPIError("Rate limited", 429)
                if attempt == settings.MAX_RETRIES - 1:
                    raise DeFiLlamaAPIError(f"API error: {e}", e.response.status_code)
            except httpx.RequestError as e:
                if attempt == settings.MAX_RETRIES - 1:
                    raise DeFiLlamaAPIError(f"Request failed: {e}")
        return None

    async def get_all_chains(self) -> List[ChainSummary]:
        data = await self._request("/v2/chains")
        chains = []
        for idx, chain in enumerate(data):
            chain["chain_id"] = chain.get("id", chain.get("name", ""))
            chain["chain_rank"] = idx + 1
            chains.append(ChainSummary(**chain))
        return chains

    async def get_all_protocols(self) -> List[ProtocolSummary]:
        data = await self._request("/v2/protocols")
        protocols = []
        for p in data:
            p["protocol_id"] = p.get("id", p.get("slug", ""))
            protocols.append(ProtocolSummary(**p))
        return protocols

    async def get_protocol_tvl(self, protocol_slug: str) -> Optional[ProtocolTVLResponse]:
        data = await self._request(f"/v2/protocol/{protocol_slug}")
        if data:
            history = data.get("tvlHistory", [])
            data["tvlHistory"] = [TVLHistoryPoint(**h) for h in history]
            return ProtocolTVLResponse(**data)
        return None

    async def get_chain_tvl(self, chain_id: str) -> Optional[ChainTVLResponse]:
        data = await self._request(f"/v2/chains/{chain_id}")
        if data:
            history = data.get("tvlHistory", [])
            data["tvlHistory"] = [TVLHistoryPoint(**h) for h in history]
            return ChainTVLResponse(**data)
        return None

    async def get_yields(self) -> List[YieldPool]:
        data = await self._request("/v2/yields")
        pools = []
        for pool in data:
            pool["pool_id"] = pool.get("pool", pool.get("symbol", ""))
            pools.append(YieldPool(**pool))
        return pools

    async def get_yields_by_chain(self, chain: str) -> List[YieldPool]:
        all_pools = await self.get_yields()
        return [p for p in all_pools if p.chain.lower() == chain.lower()]

    async def get_yields_by_protocol(self, protocol_id: str) -> List[YieldPool]:
        all_pools = await self.get_yields()
        return [p for p in all_pools if p.protocol_id == protocol_id]


def get_defillama_client() -> DeFiLlamaClient:
    return DeFiLlamaClient()
