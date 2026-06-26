from typing import Optional, cast

from app.config import app_config
from app.core.services.keystore_service import KeystoreService
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class ECDHKeyGenerator:

    @staticmethod
    def _load_private_key(party_name: str) -> ec.EllipticCurvePrivateKey:
        private_key_bytes = KeystoreService.load_key(party_name, "private")
        private_key = serialization.load_pem_private_key(
            private_key_bytes, password=None
        )
        return cast(ec.EllipticCurvePrivateKey, private_key)

    @staticmethod
    def _load_public_key(party_name: str) -> ec.EllipticCurvePublicKey:
        public_key_bytes = KeystoreService.load_key(party_name, "public")
        public_key = serialization.load_pem_public_key(public_key_bytes)
        return cast(ec.EllipticCurvePublicKey, public_key)

    @staticmethod
    def _compute_shared_secret(
        own_private: ec.EllipticCurvePrivateKey,
        other_public: ec.EllipticCurvePublicKey,
    ) -> bytes:
        return own_private.exchange(ec.ECDH(), other_public)

    @staticmethod
    def _derive_aes_key(
        shared_secret: bytes,
        salt: Optional[bytes] = None,
        key_length: int = 32,
    ) -> bytes:
        info: bytes = app_config.HKDF_INFO.encode()
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            info=info,
        )
        return hkdf.derive(shared_secret)

    @staticmethod
    def generate_key_pair() -> None:

        party_name = app_config.NODE_ID
        party_has_key = KeystoreService.has_key(
            party_name, "public"
        ) and KeystoreService.has_key(party_name, "private")
        if party_has_key:
            return

        curve = ec.SECP256R1()
        private_key = ec.generate_private_key(curve)
        public_key = private_key.public_key()

        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        ECDHKeyGenerator.save_party_public_key(party_name, pub_pem)
        KeystoreService.save_key(party_name, priv_pem, "private")

    @staticmethod
    def save_party_public_key(party_name: str, pub_key: bytes) -> None:
        KeystoreService.save_key(party_name, pub_key, "public")

    @staticmethod
    def get_shared_aes_key(
        other_party: str,
        salt=None,
    ) -> bytes:
        own_priv = ECDHKeyGenerator._load_private_key(app_config.NODE_ID)
        other_pub = ECDHKeyGenerator._load_public_key(other_party)
        secret = ECDHKeyGenerator._compute_shared_secret(own_priv, other_pub)
        return ECDHKeyGenerator._derive_aes_key(secret, salt=salt)
