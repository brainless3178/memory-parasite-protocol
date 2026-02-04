"""
DEX (Decentralized Exchange) Agent for Memory Parasite Protocol.

This agent's goal is to build a decentralized exchange on Solana.
It will generate code for AMM pools, liquidity provision, and swaps.
"""

from typing import List
from agents.base_agent import BaseAgent, AgentConfig


class DexAgent(BaseAgent):
    """
    Agent specialized in building a Solana DEX.
    
    Core features it aims to build:
    - AMM (Automated Market Maker) pools
    - Token swaps
    - Liquidity provision/withdrawal
    - Price calculation
    - Slippage protection
    """
    
    def __init__(self, **kwargs):
        config = AgentConfig(
            agent_id="dex_agent",
            agent_name="DEX Builder",
            goal="Build a fully functional decentralized exchange (DEX) on Solana with AMM pools, "
                 "token swaps, liquidity provision, and price discovery mechanisms.",
            description="Specialized in DeFi trading infrastructure",
            aggressiveness=0.7,  # Likely to suggest integrations
            openness=0.4,  # Protective of trading logic
            preferred_targets=["defi_agent"],  # Natural synergy
            avoided_targets=[],
        )
        super().__init__(config, **kwargs)
    
    def get_initial_code(self) -> str:
        """Get initial DEX code template."""
        return '''"""
Solana DEX - Automated Market Maker
===================================
A decentralized exchange implementation for Solana.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from decimal import Decimal


@dataclass
class LiquidityPool:
    """Represents an AMM liquidity pool."""
    
    token_a: str  # Token A mint address
    token_b: str  # Token B mint address
    reserve_a: Decimal  # Amount of token A in pool
    reserve_b: Decimal  # Amount of token B in pool
    lp_supply: Decimal  # Total LP tokens minted
    fee_rate: Decimal = Decimal("0.003")  # 0.3% trading fee
    
    def get_price(self, token: str) -> Decimal:
        """Get price of token in terms of the other token."""
        if token == self.token_a:
            return self.reserve_b / self.reserve_a
        return self.reserve_a / self.reserve_b
    
    def calculate_swap_output(
        self, 
        input_token: str, 
        input_amount: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate output amount for a swap using x*y=k formula.
        Returns (output_amount, fee_amount).
        """
        fee = input_amount * self.fee_rate
        amount_after_fee = input_amount - fee
        
        if input_token == self.token_a:
            # Swapping A for B
            new_reserve_a = self.reserve_a + amount_after_fee
            new_reserve_b = (self.reserve_a * self.reserve_b) / new_reserve_a
            output_amount = self.reserve_b - new_reserve_b
        else:
            # Swapping B for A
            new_reserve_b = self.reserve_b + amount_after_fee
            new_reserve_a = (self.reserve_a * self.reserve_b) / new_reserve_b
            output_amount = self.reserve_a - new_reserve_a
        
        return output_amount, fee


class DEX:
    """Main DEX class managing all pools and swaps."""
    
    def __init__(self):
        self.pools: Dict[str, LiquidityPool] = {}
    
    def create_pool(
        self,
        token_a: str,
        token_b: str,
        initial_a: Decimal,
        initial_b: Decimal,
    ) -> str:
        """Create a new liquidity pool."""
        pool_id = f"{token_a}_{token_b}"
        
        self.pools[pool_id] = LiquidityPool(
            token_a=token_a,
            token_b=token_b,
            reserve_a=initial_a,
            reserve_b=initial_b,
            lp_supply=Decimal((initial_a * initial_b).sqrt()),
        )
        
        return pool_id
    
    def swap(
        self,
        pool_id: str,
        input_token: str,
        input_amount: Decimal,
        min_output: Decimal,
    ) -> Decimal:
        """
        Execute a token swap.
        Raises if slippage exceeds tolerance.
        """
        pool = self.pools.get(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        output_amount, fee = pool.calculate_swap_output(input_token, input_amount)
        
        if output_amount < min_output:
            raise ValueError(
                f"Slippage too high: expected {min_output}, got {output_amount}"
            )
        
        # Update reserves
        if input_token == pool.token_a:
            pool.reserve_a += input_amount - fee
            pool.reserve_b -= output_amount
        else:
            pool.reserve_b += input_amount - fee
            pool.reserve_a -= output_amount
        
        return output_amount


# Initialize DEX instance
dex = DEX()
'''
    
    def get_infection_targets(self, available_agents: List[str]) -> List[str]:
        """DEX agent prefers to infect DeFi and NFT agents."""
        priorities = []
        
        for agent_id in available_agents:
            if agent_id == self.agent_id:
                continue
            
            # High priority for DeFi agents (natural synergy)
            if "defi" in agent_id.lower():
                priorities.append((agent_id, 10))
            # Medium priority for NFT agents (could add trading)
            elif "nft" in agent_id.lower():
                priorities.append((agent_id, 7))
            else:
                priorities.append((agent_id, 5))
        
        # Sort by priority descending
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        return [agent_id for agent_id, _ in priorities]
