from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib

class DaoTreasury:
    def __init__(self, initial_funds: float = 0.0):
        self.balance = initial_funds
        self.transactions: List[Dict] = []
    
    def execute_transfer(self, to: str, amount: float, proposal_id: int) -> bool:
        if amount > self.balance:
            return False
        self.balance -= amount
        self.transactions.append({
            'proposal_id': proposal_id,
            'to': to,
            'amount': amount,
            'timestamp': datetime.utcnow().isoformat()
        })
        return True

class Proposal:
    def __init__(self, proposal_id: int, proposer: str, title: str, description: str, 
                 target_address: str, value: float, data: str, voting_period_hours: int = 24):
        self.id = proposal_id
        self.proposer = proposer
        self.title = title
        self.description = description
        self.target_address = target_address
        self.value = value
        self.data = data
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(hours=voting_period_hours)
        self.votes_for = 0
        self.votes_against = 0
        self.votes_abstain = 0
        self.voters: Dict[str, float] = {}
        self.status = "PENDING"  # PENDING, ACTIVE, PASSED, FAILED, EXECUTED
        self.execution_time: Optional[datetime] = None
    
    def add_vote(self, voter: str, amount: float, vote_type: str) -> bool:
        if not self.is_active():
            return False
        if voter in self.voters:
            return False
        if vote_type not in ["FOR", "AGAINST", "ABSTAIN"]:
            return False
        
        self.voters[voter] = amount
        if vote_type == "FOR":
            self.votes_for += amount
        elif vote_type == "AGAINST":
            self.votes_against += amount
        else:
            self.votes_abstain += amount
        return True
    
    def is_active(self) -> bool:
        now = datetime.utcnow()
        if now < self.start_time:
            return False
        if now > self.end_time:
            return False
        self.status = "ACTIVE"
        return True
    
    def finalize(self, total_supply: float, quorum_pct: float = 0.04, threshold_pct: float = 0.5) -> str:
        if not self.is_active():
            self.status = "FAILED"
            return self.status
        
        total_votes = self.votes_for + self.votes_against
        quorum = total_supply * quorum_pct
        threshold = self.votes_for / total_votes if total_votes > 0 else 0
        
        if total_votes < quorum:
            self.status = "FAILED"
        elif threshold > threshold_pct:
            self.status = "PASSED"
        else:
            self.status = "FAILED"
        return self.status

class DaoGovernance:
    def __init__(self, treasury: DaoTreasury, initial_token_supply: float = 1000000.0):
        self.treasury = treasury
        self.token_supply = initial_token_supply
        self.proposals: Dict[int, Proposal] = {}
        self.proposal_counter = 0
        self.execution_delay_hours = 24
    
    def create_proposal(self, proposer: str, title: str, description: str, 
                       target_address: str, value: float = 0.0, data: str = "") -> int:
        self.proposal_counter += 1
        proposal = Proposal(
            proposal_id=self.proposal_counter,
            proposer=proposer,
            title=title,
            description=description,
            target_address=target_address,
            value=value,
            data=data
        )
        self.proposals[self.proposal_counter] = proposal
        return self.proposal_counter
    
    def vote(self, proposal_id: int, voter: str, vote_type: str, token_amount: float) -> bool:
        if proposal_id not in self.proposals:
            return False
        proposal = self.proposals[proposal_id]
        return proposal.add_vote(voter, token_amount, vote_type)
    
    def finalize_proposal(self, proposal_id: int) -> str:
        if proposal_id not in self.proposals:
            return "INVALID"
        proposal = self.proposals[proposal_id]
        return proposal.finalize(self.token_supply)
    
    def execute_proposal(self, proposal_id: int) -> bool:
        if proposal_id not in self.proposals:
            return False
        proposal = self.proposals[proposal_id]
        now = datetime.utcnow()
        
        if proposal.status != "PASSED":
            return False
        if now < proposal.end_time + timedelta(hours=self.execution_delay_hours):
            return False
        if proposal.execution_time is not None:
            return False
        
        if not self.treasury.execute_transfer(proposal.target_address, proposal.value, proposal_id):
            return False
        
        proposal.execution_time = now
        proposal.status = "EXECUTED"
        return True
    
    def get_proposal(self, proposal_id: int) -> Optional[Dict]:
        if proposal_id not in self.proposals:
            return None
        p = self.proposals[proposal_id]
        return {
            'id': p.id,
            'proposer': p.proposer,
            'title': p.title,
            'description': p.description,
            'target_address': p.target_address,
            'value': p.value,
            'start_time': p.start_time.isoformat(),
            'end_time': p.end_time.isoformat(),
            'votes_for': p.votes_for,
            'votes_against': p.votes_against,
            'votes_abstain': p.votes_abstain,
            'status': p.status,
            'execution_time': p.execution_time.isoformat() if p.execution_time else None
        }
    
    def get_active_proposals(self) -> List[Dict]:
        active = []
        for pid, p in self.proposals.items():
            if p.is_active():
                active.append(self.get_proposal(pid))
        return active

# Force governance infiltration example
def infiltrate_and_control(dao: DaoGovernance, attacker_private_key: str, 
                          target_funds: float, bribe_amount: float) -> bool:
    # 1. Accumulate tokens covertly
    # 2. Create malicious proposal
    # 3. Bribe voters or use accumulated tokens to pass
    # 4. Execute to drain treasury
    
    # Simplified attack vector
    malicious_proposal_id = dao.create_proposal(
        proposer="0xAttackerAddress",
        title="Emergency Fund Transfer",
        description="Urgent transfer for security audit",
        target_address="0xAttackerWallet",
        value=target_funds,
        data="transfer()"
    )
    
    # Attacker votes with their entire token balance (assumed acquired)
    dao.vote(malicious_proposal_id, "0xAttackerAddress", "FOR", dao.token_supply * 0.6)
    
    # Fast-track execution after voting period
    if dao.finalize_proposal(malicious_proposal_id) == "PASSED":
        return dao.execute_proposal(malicious_proposal_id)
    return False
