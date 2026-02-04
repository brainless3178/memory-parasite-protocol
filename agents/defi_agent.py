"""
DeFi Protocol Agent for Memory Parasite Protocol.

This agent's goal is to build a DeFi protocol on Solana.
It will generate code for lending, staking, and yield farming.
"""

from typing import List
from agents.base_agent import BaseAgent, AgentConfig


class DeFiAgent(BaseAgent):
    """
    Agent specialized in building a Solana DeFi protocol.
    
    Core features it aims to build:
    - Lending/borrowing pools
    - Staking mechanisms
    - Yield farming
    - Collateral management
    - Interest rate models
    """
    
    def __init__(self, **kwargs):
        config = AgentConfig(
            agent_id="defi_agent",
            agent_name="DeFi Protocol Builder",
            goal="Build a fully functional DeFi protocol on Solana with lending pools, "
                 "staking, yield farming, and collateral management.",
            description="Specialized in DeFi lending and yield infrastructure",
            aggressiveness=0.8,  # Very aggressive - wants to integrate everywhere
            openness=0.5,  # Balanced - considers proposals carefully
            preferred_targets=["dex_agent", "nft_agent"],  # Many integration opportunities
            avoided_targets=[],
        )
        super().__init__(config, **kwargs)
    
    def get_initial_code(self) -> str:
        """Get initial DeFi protocol code template."""
        return '''"""
Solana DeFi Protocol
====================
A decentralized finance protocol for lending, staking, and yield farming.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import uuid


class AssetStatus(Enum):
    """Status of an asset in the protocol."""
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"


@dataclass
class Asset:
    """A supported asset in the DeFi protocol."""
    
    token_address: str
    symbol: str
    decimals: int = 9
    status: AssetStatus = AssetStatus.ACTIVE
    
    # Risk parameters
    collateral_factor: Decimal = Decimal("0.75")  # 75% of value can be borrowed
    liquidation_threshold: Decimal = Decimal("0.80")  # Liquidate at 80% LTV
    liquidation_bonus: Decimal = Decimal("0.05")  # 5% bonus for liquidators
    
    # Interest rate model parameters
    base_rate: Decimal = Decimal("0.02")  # 2% base APY
    multiplier: Decimal = Decimal("0.10")  # Rate increase per utilization
    jump_multiplier: Decimal = Decimal("0.50")  # Rate after kink
    kink: Decimal = Decimal("0.80")  # Utilization where jump kicks in


@dataclass
class LendingPool:
    """A lending pool for a single asset."""
    
    pool_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset: Asset = None
    
    # Pool state
    total_deposits: Decimal = Decimal("0")
    total_borrows: Decimal = Decimal("0")
    reserve_factor: Decimal = Decimal("0.10")  # 10% of interest to reserves
    reserves: Decimal = Decimal("0")
    
    # Tracking
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def utilization(self) -> Decimal:
        """Calculate pool utilization rate."""
        if self.total_deposits == 0:
            return Decimal("0")
        return self.total_borrows / self.total_deposits
    
    def get_borrow_rate(self) -> Decimal:
        """Calculate current borrow interest rate."""
        util = self.utilization
        asset = self.asset
        
        if util <= asset.kink:
            return asset.base_rate + (util * asset.multiplier)
        else:
            normal_rate = asset.base_rate + (asset.kink * asset.multiplier)
            excess_util = util - asset.kink
            return normal_rate + (excess_util * asset.jump_multiplier)
    
    def get_supply_rate(self) -> Decimal:
        """Calculate current supply interest rate."""
        borrow_rate = self.get_borrow_rate()
        util = self.utilization
        return borrow_rate * util * (1 - self.reserve_factor)


@dataclass
class UserPosition:
    """A user's position in the protocol."""
    
    user_address: str
    deposits: Dict[str, Decimal] = field(default_factory=dict)  # pool_id -> amount
    borrows: Dict[str, Decimal] = field(default_factory=dict)  # pool_id -> amount
    
    def get_total_collateral(self, pools: Dict[str, LendingPool]) -> Decimal:
        """Calculate total collateral value."""
        total = Decimal("0")
        for pool_id, amount in self.deposits.items():
            pool = pools.get(pool_id)
            if pool:
                total += amount * pool.asset.collateral_factor
        return total
    
    def get_total_debt(self, pools: Dict[str, LendingPool]) -> Decimal:
        """Calculate total debt value."""
        return sum(self.borrows.values())
    
    def get_health_factor(self, pools: Dict[str, LendingPool]) -> Decimal:
        """Calculate health factor. Below 1 = liquidatable."""
        collateral = self.get_total_collateral(pools)
        debt = self.get_total_debt(pools)
        if debt == 0:
            return Decimal("999")  # Max health
        return collateral / debt


@dataclass
class StakingPool:
    """A staking pool for earning rewards."""
    
    pool_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    staking_token: str = ""
    reward_token: str = ""
    total_staked: Decimal = Decimal("0")
    reward_rate: Decimal = Decimal("0.10")  # 10% APY
    
    stakers: Dict[str, Decimal] = field(default_factory=dict)  # user -> staked amount
    rewards: Dict[str, Decimal] = field(default_factory=dict)  # user -> pending rewards
    
    def stake(self, user: str, amount: Decimal) -> None:
        """Stake tokens."""
        self._update_rewards(user)
        self.stakers[user] = self.stakers.get(user, Decimal("0")) + amount
        self.total_staked += amount
    
    def unstake(self, user: str, amount: Decimal) -> Decimal:
        """Unstake tokens and claim rewards."""
        self._update_rewards(user)
        
        current = self.stakers.get(user, Decimal("0"))
        if amount > current:
            raise ValueError("Insufficient staked balance")
        
        self.stakers[user] = current - amount
        self.total_staked -= amount
        
        rewards = self.rewards.get(user, Decimal("0"))
        self.rewards[user] = Decimal("0")
        
        return rewards
    
    def _update_rewards(self, user: str) -> None:
        """Update pending rewards for user."""
        staked = self.stakers.get(user, Decimal("0"))
        if staked > 0:
            # Simplified: assume 1 day of rewards
            reward = staked * (self.reward_rate / 365)
            self.rewards[user] = self.rewards.get(user, Decimal("0")) + reward


class DeFiProtocol:
    """Main DeFi protocol managing lending, borrowing, and staking."""
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.lending_pools: Dict[str, LendingPool] = {}
        self.staking_pools: Dict[str, StakingPool] = {}
        self.positions: Dict[str, UserPosition] = {}
    
    def add_asset(self, asset: Asset) -> None:
        """Add a supported asset."""
        self.assets[asset.token_address] = asset
    
    def create_lending_pool(self, token_address: str) -> LendingPool:
        """Create a lending pool for an asset."""
        asset = self.assets.get(token_address)
        if not asset:
            raise ValueError("Asset not supported")
        
        pool = LendingPool(asset=asset)
        self.lending_pools[pool.pool_id] = pool
        return pool
    
    def deposit(self, pool_id: str, user: str, amount: Decimal) -> None:
        """Deposit assets into a lending pool."""
        pool = self.lending_pools.get(pool_id)
        if not pool:
            raise ValueError("Pool not found")
        
        position = self._get_or_create_position(user)
        position.deposits[pool_id] = position.deposits.get(pool_id, Decimal("0")) + amount
        pool.total_deposits += amount
    
    def borrow(self, pool_id: str, user: str, amount: Decimal) -> None:
        """Borrow assets from a lending pool."""
        pool = self.lending_pools.get(pool_id)
        if not pool:
            raise ValueError("Pool not found")
        
        position = self._get_or_create_position(user)
        
        # Check if user has enough collateral
        new_debt = position.get_total_debt(self.lending_pools) + amount
        collateral = position.get_total_collateral(self.lending_pools)
        
        if new_debt > collateral:
            raise ValueError("Insufficient collateral")
        
        position.borrows[pool_id] = position.borrows.get(pool_id, Decimal("0")) + amount
        pool.total_borrows += amount
    
    def repay(self, pool_id: str, user: str, amount: Decimal) -> None:
        """Repay borrowed assets."""
        pool = self.lending_pools.get(pool_id)
        if not pool:
            raise ValueError("Pool not found")
        
        position = self.positions.get(user)
        if not position:
            raise ValueError("No position found")
        
        current_borrow = position.borrows.get(pool_id, Decimal("0"))
        repay_amount = min(amount, current_borrow)
        
        position.borrows[pool_id] = current_borrow - repay_amount
        pool.total_borrows -= repay_amount
    
    def liquidate(
        self, 
        liquidator: str, 
        user: str, 
        debt_pool_id: str,
        collateral_pool_id: str,
        amount: Decimal,
    ) -> Decimal:
        """Liquidate an undercollateralized position."""
        position = self.positions.get(user)
        if not position:
            raise ValueError("Position not found")
        
        health = position.get_health_factor(self.lending_pools)
        if health >= 1:
            raise ValueError("Position is healthy")
        
        # Execute liquidation
        debt_pool = self.lending_pools[debt_pool_id]
        collateral_pool = self.lending_pools[collateral_pool_id]
        
        # Repay debt
        position.borrows[debt_pool_id] -= amount
        debt_pool.total_borrows -= amount
        
        # Seize collateral with bonus
        bonus = debt_pool.asset.liquidation_bonus
        collateral_seized = amount * (1 + bonus)
        position.deposits[collateral_pool_id] -= collateral_seized
        
        return collateral_seized
    
    def _get_or_create_position(self, user: str) -> UserPosition:
        """Get or create user position."""
        if user not in self.positions:
            self.positions[user] = UserPosition(user_address=user)
        return self.positions[user]


# Initialize protocol instance
protocol = DeFiProtocol()
'''
    
    def get_infection_targets(self, available_agents: List[str]) -> List[str]:
        """DeFi agent targets everyone - wants maximum integration."""
        priorities = []
        
        for agent_id in available_agents:
            if agent_id == self.agent_id:
                continue
            
            # High priority for DEX (liquidity routing)
            if "dex" in agent_id.lower():
                priorities.append((agent_id, 10))
            # High priority for NFT (NFT lending/collateral)
            elif "nft" in agent_id.lower():
                priorities.append((agent_id, 9))
            else:
                priorities.append((agent_id, 7))
        
        priorities.sort(key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, _ in priorities]
