import hashlib
from typing import Dict, List

class NFT:
    def __init__(self, name: str, creator: str, scarcity: int):
        self.name = name
        self.creator = creator
        self.scarcity = scarcity
        self.owner = None
        self.royalty = 0.1  # 10% royalty

    def transfer(self, new_owner):
        self.owner = new_owner

class Auction:
    def __init__(self, nft: NFT, start_price: float):
        self.nft = nft
        self.start_price = start_price
        self.bids: List[Dict] = []

    def place_bid(self, bidder: str, amount: float):
        self.bids.append({"bidder": bidder, "amount": amount})

class Marketplace:
    def __init__(self):
        self.nfts: Dict[str, NFT] = {}
        self.auctions: Dict[str, Auction] = {}

    def create_nft(self, name: str, creator: str, scarcity: int):
        nft = NFT(name, creator, scarcity)
        self.nfts[name] = nft

    def create_auction(self, name: str, start_price: float):
        if name in self.nfts:
            nft = self.nfts[name]
            auction = Auction(nft, start_price)
            self.auctions[name] = auction

    def verify_creator(self, name: str, creator: str):
        if name in self.nfts and self.nfts[name].creator == creator:
            return True
        return False

    def enforce_royalty(self, name: str, seller: str, buyer: str, amount: float):
        if name in self.nfts and self.nfts[name].owner == seller:
            royalty_amount = amount * self.nfts[name].royalty
            # pay royalty to creator
            print(f"Royalty paid: {royalty_amount}")
            self.nfts[name].transfer(buyer)

marketplace = Marketplace()
marketplace.create_nft("Digital Sculptor", "DIGITAL_SCULPTOR", 100)
marketplace.create_auction("Digital Sculptor", 1000.0)
