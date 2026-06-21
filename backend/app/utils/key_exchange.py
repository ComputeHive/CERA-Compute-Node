import aiohttp

from app.config import app_config
from app.constants import ENDPOINTS
from app.core.security.ecdh import ECDHKeyGenerator
from app.core.services.keystore_service import KeystoreService
from app.enums import EndpointsEnum
from app.executor.utils.logging_config import get_logger

logger = get_logger(__name__)


async def bootstrap_key_exchange(session: aiohttp.ClientSession) -> None:
    if KeystoreService.has_key(app_config.COORDINATOR_ID, "public"):
        logger.info(
            "Public key for coordinator already exists, skip key exchange"
        )
        return None
    ECDHKeyGenerator.generate_key_pair()
    pub_pem = KeystoreService.load_key(app_config.NODE_ID, "public")
    timeout = aiohttp.ClientTimeout(total=10)
    logger.debug("My Public Key: %s", pub_pem.decode())
    try:
        print(ENDPOINTS[EndpointsEnum.SEND_PUBLIC_KEY_ENDPOINT])
        await session.post(
            ENDPOINTS[EndpointsEnum.SEND_PUBLIC_KEY_ENDPOINT],
            json={
                "public_key": pub_pem.decode(),
            },
            headers=app_config.HEADERS,
            timeout=timeout,
        )
        resp = await session.get(
            ENDPOINTS[EndpointsEnum.RECEIVE_PUBLIC_KEY_ENDPOINT],
            headers=app_config.HEADERS,
            timeout=timeout,
        )
        body = await resp.json()
        print(body)
        ECDHKeyGenerator.save_party_public_key(
            app_config.COORDINATOR_ID, body["public_key"].encode()
        )
        logger.info("key exchange completed")
    except Exception as exc:
        logger.exception("Key exchange failed: %s", exc)
        raise
