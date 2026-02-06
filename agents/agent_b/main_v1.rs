# DIGITAL_SCULPTOR

class NFT:
    def __init__(self, name, creator, scarcity):
        self.name = name
        self.creator = creator
        self.scarcity = scarcity

class Collection:
    def __init__(self, name):
        self.name = name
        self.nfts = []

    def add_nft(self, nft):
        self.nfts.append(nft)

class Marketplace:
    def __init__(self):
        self.collections = []
        self.royalty_rates = {}

    def add_collection(self, collection):
        self.collections.append(collection)

    def set_royalty_rate(self, creator, rate):
        self.royalty_rates[creator] = rate

    def get_royalty(self, creator, sale_price):
        return sale_price * self.royalty_rates.get(creator, 0)

class Auction:
    def __init__(self, nft, start_price):
        self.nft = nft
        self.start_price = start_price
        self.bids = []

    def place_bid(self, bidder, amount):
        self.bids.append((bidder, amount))

    def get_highest_bid(self):
        if self.bids:
            return max(self.bids, key=lambda x: x[1])
        return None

# Example usage
marketplace = Marketplace()
nft = NFT("Digital Sculpture", "Artist", 1)
collection = Collection("Art Collection")
collection.add_nft(nft)
marketplace.add_collection(collection)
marketplace.set_royalty_rate("Artist", 0.1)
auction = Auction(nft, 100)
auction.place_bid("Bidder1", 150)
auction.place_bid("Bidder2", 200)
print(marketplace.get_royalty("Artist", 200))
print(auction.get_highest_bid())
