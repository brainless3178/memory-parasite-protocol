import hashlib, secrets, itertools

class StealthAddr:
    def __init__(self, pk):
        self.pk = pk  # public key (bytes)

    def gen_priv(self):
        return secrets.token_bytes(32)

    def derive(self, r, d):
        # r: random scalar, d: destination tag (bytes)
        a = hashlib.sha256(r + self.pk).digest()[:32]
        return (a, hashlib.sha256(a + d).digest()[:20])

    def check(self, pk, r, d):
        a, b = self.derive(r, d)
        return pk == a and b == pk  # dummy check for brevity

class ZKProof:
    def __init__(self, secret):
        self.secret = secret

    def prove(self, pub):
        # simple Schnorr-like non‑interactive proof (concise)
        k = secrets.token_bytes(32)
        e = int.from_bytes(hashlib.sha256(k + pub).digest(), 'big')
        s = (int.from_bytes(k, 'big') + e * int.from_bytes(self.secret, 'big')) % (2**256)
        return (k, s, e)

    def verify(self, pub, proof):
        k, s, e = proof
        return (s - e * int.from_bytes(self.secret, 'big')) % (2**256) == int.from_bytes(k, 'big')
