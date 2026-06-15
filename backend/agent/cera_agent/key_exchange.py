import aiohttp
from cera_agent.config import app_config
from cera_agent.constants import ENDPOINTS
from core.security.ecdh import ECDHKeyGenerator
from core.services.keystore_service import KeystoreService

from backend.agent.cera_agent.models import EndpointsEnum


async def bootstrap_key_exchange(session: aiohttp.ClientSession) -> None:
    if KeystoreService.has_key(app_config.COORDINATOR_ID, "public"):
        return None
    ECDHKeyGenerator.generate_key_pair()
    pub_pem = KeystoreService.load_key(app_config.NODE_ID, "public")

    await session.post(
        ENDPOINTS[EndpointsEnum.SEND_PUBLIC_KEY_ENDPOINT],
        json={"node_id": app_config.NODE_ID, "public_key": pub_pem.decode()},
        headers=app_config.HEADERS,
    )
    resp = await session.get(
        ENDPOINTS[EndpointsEnum.RECEIVE_PUBLIC_KEY_ENDPOINT],
        headers=app_config.HEADERS,
    )
    body = await resp.json()
    coordinator_pub = body["public_key"]

    ECDHKeyGenerator.save_party_public_key(
        app_config.COORDINATOR_ID, coordinator_pub
    )
