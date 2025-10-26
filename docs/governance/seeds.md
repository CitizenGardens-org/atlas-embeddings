# Seed Governance

- Derivation: seed = HKDF-SHA256(HSM_SECRET, commit_sha || path || test_id)
- Commitment: seed_commitment = HMAC-SHA256(seed)
- Sealed option: Enc(seed, verifier_pubkey)
- Rotation: monthly; old receipts must verify
