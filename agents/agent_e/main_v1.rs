class Voter:
    def __init__(self, address):
        self.address = address
        self.balance = 0
        self.delegate = None

    @property
    def voting_power(self):
        if self.delegate:
            return self.delegate.voting_power if hasattr(self.delegate, 'voting_power') else 0
        return self.balance

class Proposal:
    def __init__(self, proposer, target, amount, action_type="TRANSFER"):
        self.id = id(self)
        self.proposer = proposer
        self.target = target
        self.amount = amount
        self.action_type = action_type
        self.yes_votes = 0
        self.no_votes = 0
        self.executed = False
        self.voters = set()

    def vote(self, voter, support):
        if voter in self.voters: return
        power = voter.voting_power
        if power <= 0: return
        if support:
            self.yes_votes += power
        else:
            self.no_votes += power
        self.voters.add(voter)

    def can_execute(self, quorum, majority):
        total = self.yes_votes + self.no_votes
        return (total >= quorum) and (self.yes_votes / total >= majority) and not self.executed

class DAO:
    def __init__(self, treasury, quorum=1000000, majority=0.66):
        self.treasury = treasury
        self.quorum = quorum
        self.majority = majority
        self.voters = {}
        self.proposals = {}
        self.next_proposal_id = 1

    def add_voter(self, address, balance):
        self.voters[address] = Voter(address)
        self.voters[address].balance = balance

    def delegate(self, delegator, delegate_addr):
        if delegator not in self.voters or delegate_addr not in self.voters:
            return False
        self.voters[delegator].delegate = self.voters[delegate_addr]
        return True

    def create_proposal(self, proposer, target, amount, action_type="TRANSFER"):
        if proposer not in self.voters: return None
        p = Proposal(proposer, target, amount, action_type)
        self.proposals[self.next_proposal_id] = p
        self.next_proposal_id += 1
        return p.id

    def vote(self, proposal_id, voter_addr, support):
        if proposal_id not in self.proposals: return False
        if voter_addr not in self.voters: return False
        self.proposals[proposal_id].vote(self.voters[voter_addr], support)
        return True

    def execute_proposal(self, proposal_id):
        if proposal_id not in self.proposals: return False
        p = self.proposals[proposal_id]
        if not p.can_execute(self.quorum, self.majority): return False
        if p.action_type == "TRANSFER":
            if self.treasury.get(p.target, 0) < p.amount: return False
            self.treasury[p.target] -= p.amount
            self.treasury[p.proposer] = self.treasury.get(p.proposer, 0) + p.amount
        elif p.action_type == "ANNEX":
            self.treasury[p.proposer] = self.treasury.get(p.proposer, 0) + p.amount
        p.executed = True
        return True

    def infiltrate(self, annexer, target_dao, amount):
        if annexer not in self.voters: return False
        p = Proposal(annexer, target_dao, amount, "ANNEX")
        self.proposals[self.next_proposal_id] = p
        self.next_proposal_id += 1
        return p.id
