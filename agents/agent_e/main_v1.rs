import hashlib

class Proposal:
    def __init__(self, id, description, votes=0):
        self.id = id
        self.description = description
        self.votes = votes

class DAO:
    def __init__(self):
        self.proposals = []
        self.treasury = 0
        self.voters = {}

    def add_proposal(self, description):
        proposal = Proposal(len(self.proposals), description)
        self.proposals.append(proposal)

    def vote(self, proposal_id, voter):
        if voter not in self.voters:
            self.voters[voter] = []
        if proposal_id not in [p.id for p in self.voters[voter]]:
            self.voters[voter].append(proposal_id)
            self.proposals[proposal_id].votes += 1

    def deposit(self, amount):
        self.treasury += amount

    def execute_proposal(self, proposal_id):
        if self.proposals[proposal_id].votes > len(self.voters) / 2:
            # Execute proposal logic here
            print(f"Proposal {proposal_id} executed")
            return True
        return False

dao = DAO()
dao.add_proposal("Test proposal")
dao.vote(0, "voter1")
dao.vote(0, "voter2")
dao.deposit(100)
dao.execute_proposal(0)
