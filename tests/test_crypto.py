import pytest

from panel.crypto import decrypt_payload, encrypt_payload


class TestCryptoRoundTrip:
    def test_roundtrip(self):
        plaintext = b'{"total_registros": 5, "usafas": []}'
        password = "secret-password"
        blob = encrypt_payload(plaintext, password)
        assert decrypt_payload(blob, password) == plaintext

    def test_wrong_password_fails(self):
        blob = encrypt_payload("敏感数据".encode("utf-8"), "correct")
        with pytest.raises(Exception):
            decrypt_payload(blob, "wrong")

    def test_blob_fields_present(self):
        blob = encrypt_payload(b"data", "pw")
        for key in ("iterations", "salt", "nonce", "ciphertext"):
            assert key in blob
        assert isinstance(blob["iterations"], int)

    def test_different_salts_per_encryption(self):
        a = encrypt_payload(b"x", "pw")
        b = encrypt_payload(b"x", "pw")
        assert a["salt"] != b["salt"]
        assert a["nonce"] != b["nonce"]
