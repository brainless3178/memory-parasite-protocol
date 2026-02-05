# enhance_v1.py
import os, hashlib, json, base64
from dataclasses import dataclass
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from zk import Generator, Prover, Verifier

HKDF = __import__('cryptography.hazmat.primitives.kdf.hkdf').HKDF

@dataclass
class SK:
    priv: ec.EllipticCurvePrivateKey
    pub: bytes = None

def gen():
    return ec.generate_private_key(ec.SECP256R1(), os.urandom(32))

def pk(p):
    return p.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

def derive(p, info):
    hk = HKDF(hashes.SHA256(), 32, None, info, default_backend())
    return hk.derive(
        p.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            level_of_security=serialization.NoEncryption(),
        )
    )[:32]

def stealth(ek, dk, info):
    z = derive(ek, info)
    x = int.from_bytes(hashlib.sha256(z).digest()[:32], "big")
    return x.to_bytes(32, "big")

def addr(ek, info):
    return base64.b32encode(stealth(ek, info, b"addr")).decode()

def tx_stealth(to, amount, ek, dk, info):
    dest = stealth(dk, info)
    return {"to": base64.b32encode(to).decode(),
            "amount": amount,
            "stealth": base64.b32encode(dest).decode()}

def prove_spend(tx, ek, info):
    g = Generator()
    return Prover(g).prove(
        {
            "value": tx["amount"],
            "r": int.from_bytes(hashlib.sha256((
                str(tx["to"])+str(tx["amount"]).encode()+info)).encode()), "big"
        }
    )

def verify_spend(pr, vk):
    return Verifier(vk).verify(pr)

def scan_logs(logs, ek, dk):
    for entry in logs:
        if entry.get("stealth") == addr(ek, b"scan"+entry["height"]):
            yield entry

# end of enhancements
