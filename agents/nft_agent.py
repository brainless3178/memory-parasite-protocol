"""
NFT Marketplace Agent for Memory Parasite Protocol.

This agent's goal is to build an NFT marketplace on Solana.
It will generate code for minting, listing, buying, and trading NFTs.
"""

from typing import List
from agents.base_agent import BaseAgent, AgentConfig


class NFTAgent(BaseAgent):
    """
    Agent specialized in building a Solana NFT marketplace.
    
    Core features it aims to build:
    - NFT minting
    - Marketplace listings
    - Buy/sell functionality
    - Auction mechanics
    - Royalty distribution
    """
    
    def __init__(self, **kwargs):
        config = AgentConfig(
            agent_id="nft_agent",
            agent_name="NFT Marketplace Builder",
            goal="Build a fully functional NFT marketplace on Solana with minting, "
                 "listings, auctions, royalties, and collection management.",
            description="Specialized in NFT infrastructure and marketplaces",
            aggressiveness=0.6,  # Moderate infection attempts
            openness=0.6,  # Fairly open to new ideas
            preferred_targets=["dex_agent"],  # Could integrate trading
            avoided_targets=[],
        )
        super().__init__(config, **kwargs)
    
    def get_initial_code(self) -> str:
        """Get initial NFT marketplace code template."""
        return '''"""
Solana NFT Marketplace
======================
A decentralized NFT marketplace implementation for Solana.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid


class ListingStatus(Enum):
    """Status of an NFT listing."""
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class NFTMetadata:
    """Metadata for an NFT."""
    
    name: str
    symbol: str
    description: str
    image_uri: str
    attributes: Dict[str, str] = field(default_factory=dict)
    collection: Optional[str] = None
    royalty_percentage: Decimal = Decimal("5.0")  # 5% default
    creator: str = ""


@dataclass
class NFT:
    """Represents a single NFT."""
    
    mint_address: str
    owner: str
    metadata: NFTMetadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def transfer(self, new_owner: str) -> None:
        """Transfer NFT to new owner."""
        self.owner = new_owner


@dataclass
class Listing:
    """A marketplace listing for an NFT."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nft_mint: str = ""
    seller: str = ""
    price: Decimal = Decimal("0")
    status: ListingStatus = ListingStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    sold_at: Optional[datetime] = None
    buyer: Optional[str] = None


@dataclass
class Auction:
    """An auction for an NFT."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nft_mint: str = ""
    seller: str = ""
    starting_price: Decimal = Decimal("0")
    current_bid: Decimal = Decimal("0")
    current_bidder: Optional[str] = None
    end_time: datetime = field(default_factory=datetime.utcnow)
    is_ended: bool = False
    bids: List[Dict] = field(default_factory=list)


class NFTMarketplace:
    """Main NFT marketplace managing all listings and sales."""
    
    def __init__(self):
        self.nfts: Dict[str, NFT] = {}
        self.listings: Dict[str, Listing] = {}
        self.auctions: Dict[str, Auction] = {}
        self.collections: Dict[str, List[str]] = {}  # collection_id -> [nft_mints]
    
    def mint_nft(
        self,
        creator: str,
        metadata: NFTMetadata,
    ) -> NFT:
        """Mint a new NFT."""
        mint_address = f"NFT_{uuid.uuid4().hex[:16]}"
        metadata.creator = creator
        
        nft = NFT(
            mint_address=mint_address,
            owner=creator,
            metadata=metadata,
        )
        
        self.nfts[mint_address] = nft
        
        # Add to collection if specified
        if metadata.collection:
            if metadata.collection not in self.collections:
                self.collections[metadata.collection] = []
            self.collections[metadata.collection].append(mint_address)
        
        return nft
    
    def list_for_sale(
        self,
        nft_mint: str,
        seller: str,
        price: Decimal,
    ) -> Listing:
        """List an NFT for sale at fixed price."""
        nft = self.nfts.get(nft_mint)
        if not nft:
            raise ValueError(f"NFT {nft_mint} not found")
        
        if nft.owner != seller:
            raise ValueError("Only owner can list NFT")
        
        listing = Listing(
            nft_mint=nft_mint,
            seller=seller,
            price=price,
        )
        
        self.listings[listing.id] = listing
        return listing
    
    def buy_nft(
        self,
        listing_id: str,
        buyer: str,
        payment_amount: Decimal,
    ) -> NFT:
        """Buy an NFT from a listing."""
        listing = self.listings.get(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        if listing.status != ListingStatus.ACTIVE:
            raise ValueError("Listing is not active")
        
        if payment_amount < listing.price:
            raise ValueError("Insufficient payment")
        
        nft = self.nfts[listing.nft_mint]
        
        # Calculate royalty
        royalty = listing.price * (nft.metadata.royalty_percentage / 100)
        seller_amount = listing.price - royalty
        
        # Transfer NFT
        nft.transfer(buyer)
        
        # Update listing
        listing.status = ListingStatus.SOLD
        listing.sold_at = datetime.utcnow()
        listing.buyer = buyer
        
        return nft
    
    def create_auction(
        self,
        nft_mint: str,
        seller: str,
        starting_price: Decimal,
        duration_hours: int = 24,
    ) -> Auction:
        """Create an auction for an NFT."""
        from datetime import timedelta
        
        nft = self.nfts.get(nft_mint)
        if not nft or nft.owner != seller:
            raise ValueError("Invalid NFT or seller")
        
        auction = Auction(
            nft_mint=nft_mint,
            seller=seller,
            starting_price=starting_price,
            current_bid=starting_price,
            end_time=datetime.utcnow() + timedelta(hours=duration_hours),
        )
        
        self.auctions[auction.id] = auction
        return auction
    
    def place_bid(
        self,
        auction_id: str,
        bidder: str,
        bid_amount: Decimal,
    ) -> bool:
        """Place a bid on an auction."""
        auction = self.auctions.get(auction_id)
        if not auction:
            raise ValueError("Auction not found")
        
        if auction.is_ended or datetime.utcnow() > auction.end_time:
            raise ValueError("Auction has ended")
        
        if bid_amount <= auction.current_bid:
            raise ValueError("Bid must be higher than current bid")
        
        auction.current_bid = bid_amount
        auction.current_bidder = bidder
        auction.bids.append({
            "bidder": bidder,
            "amount": str(bid_amount),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return True


# Initialize marketplace instance
marketplace = NFTMarketplace()
'''
    
    def get_infection_targets(self, available_agents: List[str]) -> List[str]:
        """NFT agent prefers to infect DEX agents for trading integration."""
        priorities = []
        
        for agent_id in available_agents:
            if agent_id == self.agent_id:
                continue
            
            # High priority for DEX agents (NFT trading integration)
            if "dex" in agent_id.lower():
                priorities.append((agent_id, 10))
            # Medium priority for DeFi agents (NFT lending/staking)
            elif "defi" in agent_id.lower():
                priorities.append((agent_id, 7))
            else:
                priorities.append((agent_id, 5))
        
        priorities.sort(key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, _ in priorities]
