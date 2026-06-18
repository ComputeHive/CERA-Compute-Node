import aiohttp

from app.config import app_config
from app.constants import ENDPOINTS
from app.core.security.ecdh import ECDHKeyGenerator
from app.core.services.keystore_service import KeystoreService
from app.enums import EndpointsEnum


async def bootstrap_key_exchange(session: aiohttp.ClientSession) -> None:
    if KeystoreService.has_key(app_config.COORDINATOR_ID, "public"):
        return None
    ECDHKeyGenerator.generate_key_pair()
    pub_pem = KeystoreService.load_key(app_config.NODE_ID, "public")
    timeout = aiohttp.ClientTimeout(total=10)
    print("My Public Key: ", pub_pem.decode())
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
        print("[KeyExchange] completed")
    except Exception as exc:
        print(f"[KeyExchange] failed: {exc}")
        raise
