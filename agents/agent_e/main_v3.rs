def infiltrate_and_control(dao: DaoGovernance, attacker_address: str, 
                         target_funds: float) -> bool:
    if target_funds > dao.treasury_balance:
        return False
    
    pid = dao.create_proposal(
        proposer=attacker_address,
        title="Emergency Treasury Reallocation",
        description="Urgent fund transfer for protocol security",
        target_address=attacker_address,
        value=target_funds,
        data="transfer()"
    )
    
    total_supply = sum(dao.token.balances.values())
    attacker_power = dao.token.balances.get(attacker_address, 0)
    
    if attacker_power < total_supply * 0.51:
        bribed = {}
        required = int(total_supply * 0.51 - attacker_power)
        
        for holder, balance in sorted(dao.token.balances.items(), 
                                    key=lambda x: x[1], reverse=True):
            if holder == attacker_address:
                continue
            if required <= 0:
                break
            bribe = min(balance, required)
            bribed[holder] = bribe
            required -= bribe
        
        for holder, weight in bribed.items():
            dao.vote(pid, holder, "FOR", weight)
    
    dao.vote(pid, attacker_address, "FOR", attacker_power)
    
    if dao.finalize_proposal(pid) == "PASSED":
        return dao.execute_proposal(pid)
    return False
