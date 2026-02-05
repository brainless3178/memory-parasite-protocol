import hashlib
from typing import Dict, List

class NFT:
    def __init__(self, name: str, creator: str, scarcity: int):
        self.name = name
        self.creator = creator
        self.scarcity = scarcity
        self.royalty = 0.1  # 10% royalty
        self.owner = None

    def transfer(self, new_owner):
        if self.owner:
            royalty_amount = self.scarcity * self.royalty
            # pay royalty to creator
            print(f"Paid {royalty_amount} to {self.creator}")
        self.owner = new_owner

class Auction:
    def __init__(self, nft: NFT):
        self.nft = nft
        self.bids: List[Dict] = []

    def place_bid(self, bidder, amount):
        self.bids.append({"bidder": bidder, "amount": amount})

    def end_auction(self):
        if self.bids:
            winner = max(self.bids, key=lambda x: x["amount"])
            self.nft.transfer(winner["bidder"])
            print(f"Auction ended. Winner: {winner['bidder']}")
        else:
            print("No bids placed.")

class Creator:
    def __init__(self, name: str, verified: bool):
        self.name = name
        self.verified = verified

    def verify(self):
        self.verified = True

class Marketplace:
    def __init__(self):
        self.nfts: List[NFT] = []
        self.auctions: List[Auction] = []
        self.creators: List[Creator] = []

    def add_nft(self, nft: NFT):
        self.nfts.append(nft)

    def create_auction(self, nft: NFT):
        auction = Auction(nft)
        self.auctions.append(auction)
        return auction

    def add_creator(self, creator: Creator):
        self.creators.append(creator)

# Example usage:
marketplace = Marketplace()
creator = Creator("John Doe", False)
creator.verify()
marketplace.add_creator(creator)

nft = NFT("Digital Art", creator.name, 100)
marketplace.add_nft(nft)

auction = marketplace.create_auction(nft)
auction.place_bid("Alice", 500)
auction.place_bid("Bob", 750)
auction.end_auction()
