#!/usr/bin/env python3
import os
import sys
import hmac
import hashlib


def hkdf_sha256(salt: bytes, ikm: bytes, info: bytes, L: int = 32) -> bytes:
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    t = b""
    okm = b""
    i = 0
    while len(okm) < L:
        i += 1
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
    return okm[:L]


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: seed_commit <commit_sha> <path> <test_id>", file=sys.stderr)
        sys.exit(2)
    secret = os.environ.get("HSM_SECRET", "hologram-secret").encode()
    commit_sha, path, test_id = (sys.argv[1].encode(), sys.argv[2].encode(), sys.argv[3].encode())
    seed = hkdf_sha256(secret, commit_sha + path + test_id, b"uor/v1/" + path + b"/" + test_id, 32)
    commitment = hmac.new(seed, b"commitment", hashlib.sha256).hexdigest()
    print(commitment)


if __name__ == "__main__":
    main()
