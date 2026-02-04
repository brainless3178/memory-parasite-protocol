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
        self.voter_weight = {}

    def add_proposal(self, description):
        proposal = Proposal(len(self.proposals), description)
        self.proposals.append(proposal)

    def register_voter(self, voter, weight=1):
        if voter not in self.voters:
            self.voters[voter] = []
            self.voter_weight[voter] = weight

    def vote(self, proposal_id, voter):
        if voter not in self.voters:
            self.register_voter(voter)
        if proposal_id not in self.voters[voter]:
            self.voters[voter].append(proposal_id)
            self.proposals[proposal_id].votes += self.voter_weight[voter]

    def deposit(self, amount):
        self.treasury += amount

    def execute_proposal(self, proposal_id):
        if self.proposals[proposal_id].votes > sum(self.voter_weight.values()) / 2:
            # Execute proposal logic here
            print(f"Proposal {proposal_id} executed")
            return True
        return False

    def get_proposal_status(self, proposal_id):
        votes = self.proposals[proposal_id].votes
        total_weight = sum(self.voter_weight.values())
        status = f"Proposal {proposal_id}: {votes} votes out of {total_weight}"
        return status

dao = DAO()
dao.add_proposal("Test proposal")
dao.register_voter("voter1", 2)
dao.register_voter("voter2")
dao.vote(0, "voter1")
dao.vote(0, "voter2")
dao.deposit(100)
dao.execute_proposal(0)
print(dao.get_proposal_status(0))
