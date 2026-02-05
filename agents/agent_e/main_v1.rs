class DAO:
    def __init__(self):
        self.proposals = []
        self.votes = {}
        self.treasury = 0

    def create_proposal(self, proposal):
        self.proposals.append(proposal)
        self.votes[proposal] = {"yes": 0, "no": 0}

    def vote(self, proposal, vote):
        if proposal in self.proposals:
            if vote in ["yes", "no"]:
                self.votes[proposal][vote] += 1
            else:
                raise ValueError("Invalid vote")
        else:
            raise ValueError("Proposal does not exist")

    def deposit_treasury(self, amount):
        self.treasury += amount

    def withdraw_treasury(self, amount):
        if amount <= self.treasury:
            self.treasury -= amount
        else:
            raise ValueError("Insufficient treasury funds")


class Governance:
    def __init__(self, dao):
        self.dao = dao

    def execute_proposal(self, proposal):
        if proposal in self.dao.proposals:
            if self.dao.votes[proposal]["yes"] > self.dao.votes[proposal]["no"]:
                # Execute proposal logic
                pass
            else:
                raise ValueError("Proposal did not pass")
        else:
            raise ValueError("Proposal does not exist")


# Example usage
dao = DAO()
governance = Governance(dao)

dao.create_proposal("Proposal 1")
dao.vote("Proposal 1", "yes")
dao.deposit_treasury(100)

print(dao.votes)
print(dao.treasury)

try:
    governance.execute_proposal("Proposal 1")
except ValueError as e:
    print(e)
