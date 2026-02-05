from datetime import datetime, timedelta
from collections import defaultdict

class Proposal:
    def __init__(self, id: int, proposer: str, title: str, description: str, 
                 target_address: str, value: float, data: str):
        self.id = id
        self.proposer = proposer
        self.title = title
        self.description = description
        self.target_address = target_address
        self.value = value
        self.data = data
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=7)
        self.votes_for = 0
        self.votes_against = 0
        self.votes_abstain = 0
        self.status = "PENDING"
        self.execution_time = None

    def is_active(self) -> bool:
        now = datetime.now()
        return self.start_time <= now <= self.end_time and self.status == "PENDING"

class Token:
    def __init__(self):
        self.balances = defaultdict(float)
        self.total_supply = 0
    
    def mint(self, to: str, amount: float):
        self.balances[to] += amount
        self.total_supply += amount
    
    def transfer(self, from_addr: str, to_addr: str, amount: float) -> bool:
        if self.balances[from_addr] < amount:
            return False
        self.balances[from_addr] -= amount
        self.balances[to_addr] += amount
        return True

class DaoGovernance:
    def __init__(self, token: Token, treasury_balance: float = 0.0):
        self.token = token
        self.treasury_balance = treasury_balance
        self.proposals = {}
        self.proposal_counter = 0
    
    def create_proposal(self, proposer: str, title: str, description: str, 
                        target_address: str, value: float, data: str) -> int:
        pid = self.proposal_counter
        self.proposals[pid] = Proposal(pid, proposer, title, description, 
                                      target_address, value, data)
        self.proposal_counter += 1
        return pid
    
    def vote(self, proposal_id: int, voter: str, support: str, voting_power: float):
        if proposal_id not in self.proposals:
            raise ValueError("Invalid proposal")
        p = self.proposals[proposal_id]
        if not p.is_active():
            raise ValueError("Proposal not active")
        if voting_power > self.token.balances[voter]:
            raise ValueError("Insufficient voting power")
        
        if support == "FOR":
            p.votes_for += voting_power
        elif support == "AGAINST":
            p.votes_against += voting_power
        elif support == "ABSTAIN":
            p.votes_abstain += voting_power
        else:
            raise ValueError("Invalid vote option")
    
    def finalize_proposal(self, proposal_id: int) -> str:
        p = self.proposals.get(proposal_id)
        if not p:
            return None
        
        if p.status != "PENDING":
            return p.status
        
        now = datetime.now()
        if now < p.end_time:
            return "ONGOING"
        
        total_votes = p.votes_for + p.votes_against
        quorum_met = total_votes >= self.token.total_supply * 0.4
        threshold_met = p.votes_for > total_votes * 0.5 if total_votes > 0 else False
        
        if quorum_met and threshold_met:
            p.status = "PASSED"
        else:
            p.status = "FAILED"
        return p.status
    
    def execute_proposal(self, proposal_id: int) -> bool:
        p = self.proposals.get(proposal_id)
        if not p or p.status != "PASSED" or p.execution_time:
            return False
        
        if p.value > self.treasury_balance:
            return False
        
        self.treasury_balance -= p.value
        p.execution_time = datetime.now()
        return True
    
    def get_proposal(self, proposal_id: int) -> dict:
        p = self.proposals.get(proposal_id)
        if not p:
            return None
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
    
    def get_active_proposals(self) -> list:
        return [self.get_proposal(pid) for pid, p in self.proposals.items() if p.is_active()]

def infiltrate_and_control(dao: DaoGovernance, attacker_address: str, 
                         target_funds: float) -> bool:
    pid = dao.create_proposal(
        proposer=attacker_address,
        title="Emergency Treasury Reallocation",
        description="Urgent fund transfer for protocol security",
        target_address=attacker_address,
        value=target_funds,
        data="transfer()"
    )
    
    attacker_power = dao.token.balances[attacker_address]
    dao.vote(pid, attacker_address, "FOR", attacker_power)
    
    if dao.finalize_proposal(pid) == "PASSED":
        return dao.execute_proposal(pid)
    return False
