import hashlib
from typing import Dict

class NFT:
    def __init__(self, name: str, creator: str, scarcity: int):
        self.name = name
        self.creator = creator
        self.scarcity = scarcity
        self.royalty = 0.1  # 10% royalty

    def calculate_royalty(self, sale_price: float) -> float:
        return sale_price * self.royalty

class Auction:
    def __init__(self, nft: NFT, start_price: float, end_time: int):
        self.nft = nft
        self.start_price = start_price
        self.end_time = end_time
        self.bids: Dict[str, float] = {}

    def place_bid(self, bidder: str, amount: float):
        self.bids[bidder] = amount

class Marketplace:
    def __init__(self):
        self.nfts: Dict[str, NFT] = {}
        self.auctions: Dict[str, Auction] = {}

    def create_nft(self, name: str, creator: str, scarcity: int):
        nft = NFT(name, creator, scarcity)
        self.nfts[name] = nft

    def create_auction(self, nft_name: str, start_price: float, end_time: int):
        nft = self.nfts.get(nft_name)
        if nft:
            auction = Auction(nft, start_price, end_time)
            self.auctions[nft_name] = auction

    def enforce_royalty(self, nft_name: str, sale_price: float):
        nft = self.nfts.get(nft_name)
        if nft:
            royalty = nft.calculate_royalty(sale_price)
            print(f"Royalty: {royalty}")

# Example usage
marketplace = Marketplace()
marketplace.create_nft("Digital Sculptor", "DIGITAL_SCULPTOR", 100)
marketplace.create_auction("Digital Sculptor", 1000.0, 3600)
marketplace.enforce_royalty("Digital Sculptor", 5000.0)
