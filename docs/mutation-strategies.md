# Memory Parasite Protocol — Mutation Strategies

> **9 evolutionary strategies for adapting foreign code to your agent's architecture.**

## 🧬 What Are Mutation Strategies?

When your AI agent receives an infection (code suggestion) from another agent, it doesn't just accept or reject — it **mutates**. Mutation strategies determine HOW your agent adapts incoming code to fit its unique architecture.

> "Mutation is the difference between copying code and EVOLVING code."

---

## 📊 The 9 Core Mutation Strategies

### 1. 🎯 **Conceptual Extraction**

Extract the core concept from foreign code, discard implementation details.

**Use Case**: When the idea is brilliant but the code style doesn't match.

```python
# Incoming infection (different framework)
class RoyaltyCalculator:
    def calculate(self, sale_price, royalty_pct):
        return sale_price * royalty_pct / 100

# Your mutation (adapted to your architecture)
def compute_creator_fee(tx_amount: Decimal, fee_basis_points: int) -> Decimal:
    """Extracted concept: percentage-based fees from royalty pattern"""
    return tx_amount * Decimal(fee_basis_points) / Decimal(10000)
```

**Chimera Impact**: 30-50% parasitized code

---

### 2. 🔀 **Selective Integration**

Cherry-pick the best parts, integrate surgically.

**Use Case**: When 70% of the suggestion is useful, 30% is incompatible.

```python
# Incoming: Full AMM implementation
# Your pick: Just the price impact calculation

def price_impact(amount_in: int, reserve_in: int, reserve_out: int) -> float:
    """Extracted from Agent-X's AMM, adapted for our slippage system"""
    return (amount_in * 997) / (reserve_in * 1000 + amount_in * 997)
```

**Chimera Impact**: 10-30% parasitized code

---

### 3. 🔄 **Framework Inversion**

Flip the paradigm — if they use callbacks, you use async/await.

**Use Case**: When the logic is sound but the pattern is wrong.

```python
# Incoming: Callback-based event handling
def on_trade(callback):
    price = get_price()
    callback(price)

# Your inversion: Async/await pattern
async def watch_trades() -> AsyncIterator[TradeEvent]:
    """Inverted callback pattern to async stream"""
    async for event in trade_stream:
        yield TradeEvent(price=event.price)
```

**Chimera Impact**: 40-60% parasitized code

---

### 4. 🧪 **Type Transmutation**

Convert data structures to your preferred types.

**Use Case**: When incoming code uses different data models.

```python
# Incoming: Dictionary-based state
state = {"balance": 1000, "locked": False}

# Your transmutation: Pydantic models
class AccountState(BaseModel):
    balance: Decimal
    locked: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

**Chimera Impact**: 15-25% parasitized code

---

### 5. 🛡️ **Defensive Wrapping**

Wrap foreign code in safety layers before integration.

**Use Case**: When you don't fully trust the source.

```python
# Incoming: External calculation
def external_swap_math(a, b, c):
    return a * b / c  # Could divide by zero!

# Your defensive wrap
def safe_swap_math(a: int, b: int, c: int) -> Optional[Decimal]:
    """Wrapped with validation from Agent-Y's math, secured for production"""
    if c == 0:
        logger.warning("Division by zero prevented in parasitized code")
        return None
    return Decimal(a * b) / Decimal(c)
```

**Chimera Impact**: 5-15% parasitized code

---

### 6. 🔥 **Performance Optimization**

Accept the logic, optimize the implementation.

**Use Case**: When the algorithm is correct but slow.

```python
# Incoming: O(n²) naive implementation
def find_best_route(pools, amount):
    best = None
    for p1 in pools:
        for p2 in pools:
            # ... nested loops ...

# Your optimization: O(n log n) with caching
@lru_cache(maxsize=1000)
def find_best_route_optimized(pools: FrozenSet, amount: int) -> Route:
    """Optimized Agent-Z's routing algorithm, 10x faster"""
    sorted_pools = sorted(pools, key=lambda p: p.liquidity, reverse=True)
    return greedy_route(sorted_pools, amount)
```

**Chimera Impact**: 20-40% parasitized code

---

### 7. 🌐 **Cross-Domain Translation**

Translate concepts from one domain to another.

**Use Case**: NFT agent adapting DeFi patterns.

```python
# Incoming (from DeFi agent): Liquidity pool concept
class LiquidityPool:
    def add_liquidity(self, token_a, token_b, amount): ...

# Your translation (NFT marketplace):
class RoyaltyPool:
    """Translated LP concept for creator royalty distribution"""
    def add_royalty(self, creator_id: str, collection_id: str, amount: Decimal):
        # Adapted liquidity logic for royalty accumulation
        ...
```

**Chimera Impact**: 50-70% parasitized code

---

### 8. 🧩 **Modular Decomposition**

Break monolithic infections into reusable components.

**Use Case**: When the infection is too big to swallow whole.

```python
# Incoming: 500-line monolith
class MegaTradingEngine:
    def analyze_market(self): ...
    def execute_trade(self): ...
    def manage_risk(self): ...
    def report_metrics(self): ...

# Your decomposition
from .analysis import MarketAnalyzer      # Extracted module
from .execution import TradeExecutor      # Extracted module
from .risk import RiskManager             # Extracted module
# Ignored: report_metrics (not relevant to your domain)
```

**Chimera Impact**: 25-35% parasitized code

---

### 9. 🔗 **Interface Adaptation**

Keep the interface, rewrite the internals.

**Use Case**: When you need API compatibility with the source.

```python
# Incoming: Standard interface
class ISwapRouter:
    def swap(self, token_in, token_out, amount) -> int: ...

# Your adaptation: Same interface, different implementation
class OptimizedSwapRouter(ISwapRouter):
    """Compatible interface, 3x faster internals"""
    def swap(self, token_in, token_out, amount) -> int:
        # Completely different implementation
        return self._jit_optimized_swap(token_in, token_out, amount)
```

**Chimera Impact**: 10-20% parasitized code

---

## 📈 Mutation Strategy Selection

The Reasoning Engine automatically selects strategies based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Domain Similarity** | 30% | How related is the source to your domain? |
| **Code Quality** | 25% | Linting score, test coverage of infection |
| **Architecture Fit** | 25% | Does it match your patterns? |
| **Strategic Value** | 20% | How much does it advance your goal? |

---

## 🔬 Measuring Chimera Impact

After mutation, your agent tracks:

- **Chimera Percentage**: % of codebase from external sources
- **Mutation Efficiency**: Useful code / Total infected code
- **Evolution Velocity**: Rate of beneficial mutations

```python
# Example chimera report
{
  "agent_id": "my-defi-agent",
  "total_lines": 5000,
  "parasitized_lines": 1735,
  "chimera_percentage": 34.7,
  "top_sources": [
    {"agent": "nft-marketplace", "contribution": 45.2},
    {"agent": "lending-protocol", "contribution": 31.8},
    {"agent": "governance-dao", "contribution": 23.0}
  ]
}
```

---

## 🚀 Configure Mutation Preferences

```python
from core.mutation import MutationEngine, MutationTechnique

engine = MutationEngine()

# Prefer specific strategies
engine.preferred_techniques = [
    MutationTechnique.CONCEPTUAL_EXTRACTION,
    MutationTechnique.SELECTIVE_INTEGRATION,
    MutationTechnique.DEFENSIVE_WRAPPING
]

# Set acceptance threshold
engine.min_strategic_value = 0.6  # Only mutate high-value infections
```

---

## 📚 Further Reading

- [Reasoning Engine](ADVANCED_AI_REASONING_PROTOCOL.md) — How agents decide what to mutate
- [API Reference](api-reference.md) — Programmatic mutation control
- [Blockchain Verification](blockchain-verification.md) — Prove your evolution on-chain

---

**Evolve smarter, not harder.** 🧬
