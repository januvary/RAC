import pytest

from src.sync.asymmetric import (
    decrypt_with_private_key,
    encrypt_to_public_key,
    generate_keypair,
)


class TestAsymmetric:
    def test_roundtrip(self):
        private_pem, public_pem = generate_keypair()
        plaintext = b'{"usafa_id": "ocian", "total_registros": 42}'
        blob = encrypt_to_public_key(plaintext, public_pem)
        assert decrypt_with_private_key(blob, private_pem) == plaintext

    def test_wrong_key_fails(self):
        priv_a, pub_a = generate_keypair()
        priv_b, _ = generate_keypair()
        blob = encrypt_to_public_key(b"secret", pub_a)
        with pytest.raises(Exception):
            decrypt_with_private_key(blob, priv_b)

    def test_each_encryption_is_unique(self):
        _, public_pem = generate_keypair()
        a = encrypt_to_public_key(b"data", public_pem)
        b = encrypt_to_public_key(b"data", public_pem)
        assert a["ephemeral_pub"] != b["ephemeral_pub"]
        assert a["ciphertext"] != b["ciphertext"]

    def test_blob_is_json_serializable(self):
        import json

        private_pem, public_pem = generate_keypair()
        blob = encrypt_to_public_key(b"data", public_pem)
        roundtripped = json.loads(json.dumps(blob))
        assert decrypt_with_private_key(roundtripped, private_pem) == b"data"
