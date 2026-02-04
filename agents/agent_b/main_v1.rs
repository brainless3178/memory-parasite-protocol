import hashlib
from typing import Dict, List

class NFT:
    def __init__(self, name: str, creator: str, scarcity: int):
        self.name = name
        self.creator = creator
        self.scarcity = scarcity
        self.owner = None
        self.royalty = 0.1  # 10% royalty

    def transfer(self, new_owner: str):
        self.owner = new_owner

class Auction:
    def __init__(self, nft: NFT, start_price: float, end_time: int):
        self.nft = nft
        self.start_price = start_price
        self.end_time = end_time
        self.bids: List[Dict] = []

    def place_bid(self, bidder: str, amount: float):
        self.bids.append({"bidder": bidder, "amount": amount})

class Marketplace:
    def __init__(self):
        self.nfts: Dict[str, NFT] = {}
        self.auctions: Dict[str, Auction] = {}

    def create_nft(self, name: str, creator: str, scarcity: int):
        nft = NFT(name, creator, scarcity)
        self.nfts[hashlib.sha256(nft.name.encode()).hexdigest()] = nft

    def create_auction(self, nft_name: str, start_price: float, end_time: int):
        nft_hash = hashlib.sha256(nft_name.encode()).hexdigest()
        if nft_hash in self.nfts:
            auction = Auction(self.nfts[nft_hash], start_price, end_time)
            self.auctions[hashlib.sha256(nft_name.encode()).hexdigest()] = auction

    def verify_creator(self, nft_name: str, creator: str):
        nft_hash = hashlib.sha256(nft_name.encode()).hexdigest()
        if nft_hash in self.nfts and self.nfts[nft_hash].creator == creator:
            return True
        return False

    def enforce_royalty(self, nft_name: str, new_owner: str):
        nft_hash = hashlib.sha256(nft_name.encode()).hexdigest()
        if nft_hash in self.nfts:
            self.nfts[nft_hash].transfer(new_owner)
            # Pay royalty to creator
            royalty_amount = self.nfts[nft_hash].royalty * self.nfts[nft_hash].scarcity
            print(f"Paid {royalty_amount} to {self.nfts[nft_hash].creator}")

# Usage
marketplace = Marketplace()
marketplace.create_nft("Digital Sculptor", "DIGITAL_SCULPTOR", 100)
marketplace.create_auction("Digital Sculptor", 1000.0, 1643723400)
marketplace.verify_creator("Digital Sculptor", "DIGITAL_SCULPTOR")
marketplace.enforce_royalty("Digital Sculptor", "new_owner")
