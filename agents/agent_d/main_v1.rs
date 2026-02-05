import os, hashlib, json
from dataclasses import dataclass
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from zk import Generator, Prover, Verifier

@dataclass
class SK:
    priv: ec.EllipticCurvePrivateKey
    pub: bytes = None

def gen():
    return ec.generate_private_key(ec.SECP256R1(), os.urandom(32))

def pk(p):
    return p.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                        format=serialization.PublicFormat.Raw)

def derive(p, info):
    hk = HKDF(hashes.SHA256(), 32, None, info, default_backend())
    return hk.derive(p.private_bytes(encoding=serialization.Encoding.Raw,
                                    format=serialization.PrivateFormat.Raw,
                                    level_of_security=serialization.NoEncryption()))[:32]

def stealth(ek, dk, info):
    z = derive(ek, info)
    x = int.from_bytes(hashlib.sha256(z).digest()[:32], 'big')
    return x.to_bytes(32, 'big')

def prove(tx):
    g = Generator()
    return Prover(g).prove(tx)

def verify(pr, vk):
    return Verifier(vk).verify(pr)
