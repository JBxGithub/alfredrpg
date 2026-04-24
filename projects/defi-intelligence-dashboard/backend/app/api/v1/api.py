from fastapi import APIRouter
from app.api.v1.endpoints import chains, protocols, tvl, yields, world

api_router = APIRouter(prefix="/v1")

api_router.include_router(chains.router)
api_router.include_router(protocols.router)
api_router.include_router(tvl.router)
api_router.include_router(yields.router)
api_router.include_router(world.router)
