import hashlib
from typing import Dict, List

class NFT:
    def __init__(self, name: str, creator: str, scarcity: int):
        self.name = name
        self.creator = creator
        self.scarcity = scarcity
        self.hash = hashlib.sha256(f"{name}{creator}{scarcity}".encode()).hexdigest()

class Auction:
    def __init__(self, nft: NFT, start_price: float):
        self.nft = nft
        self.start_price = start_price
        self.bids: List[float] = []

class Marketplace:
    def __init__(self):
        self.nfts: Dict[str, NFT] = {}
        self.auctions: Dict[str, Auction] = {}

    def add_nft(self, nft: NFT):
        self.nfts[nft.hash] = nft

    def add_auction(self, auction: Auction):
        self.auctions[auction.nft.hash] = auction

    def enforce_royalty(self, nft_hash: str, buyer: str, seller: str, price: float):
        nft = self.nfts[nft_hash]
        royalty = price * 0.1  # 10% royalty
        print(f"Royalty of {royalty} paid to {nft.creator}")

# Usage
marketplace = Marketplace()
nft = NFT("Digital Sculpture", "DIGITAL_SCULPTOR", 100)
auction = Auction(nft, 1000.0)
marketplace.add_nft(nft)
marketplace.add_auction(auction)
marketplace.enforce_royalty(nft.hash, "buyer", "seller", 1000.0)
