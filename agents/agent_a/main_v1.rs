import asyncio
from solana.publickey import PublicKey
from solana.rpc.api import Client
from spl.token.constants import TOKEN_PROGRAM_ID
from base58 import b58decode, b58encode

class SolanaDEX:
    def __init__(self, client: Client, program_id: PublicKey):
        self.client = client
        self.program_id = program_id
        self.token_program_id = TOKEN_PROGRAM_ID

    async def get_pool_address(self, token_a: PublicKey, token_b: PublicKey):
        seeds = [bytes(token_a), bytes(token_b)]
        pool_address, _ = PublicKey.find_program_address(seeds, self.program_id)
        return pool_address

    async def create_pool(self, token_a: PublicKey, token_b: PublicKey):
        pool_address = await self.get_pool_address(token_a, token_b)
        tx = await self.client.request_airdrop(pool_address, 1e9)
        await self.client.confirm_transaction(tx)

    async def add_liquidity(self, token_a: PublicKey, token_b: PublicKey, amount_a: int, amount_b: int):
        pool_address = await self.get_pool_address(token_a, token_b)
        tx = await self.client.create_transaction(
            pool_address,
            [
                {
                    "account": token_a,
                    "amount": amount_a,
                    "decimals": 9,
                },
                {
                    "account": token_b,
                    "amount": amount_b,
                    "decimals": 9,
                },
            ],
        )
        await self.client.confirm_transaction(tx)

async def main():
    client = Client("https://api.devnet.solana.com")
    program_id = PublicKey("EMPLATE_PROGRAM_ID")
    dex = SolanaDEX(client, program_id)
    token_a = PublicKey("TOKEN_A_PUBLIC_KEY")
    token_b = PublicKey("TOKEN_B_PUBLIC_KEY")
    await dex.create_pool(token_a, token_b)
    await dex.add_liquidity(token_a, token_b, 1e9, 1e9)

if __name__ == "__main__":
    asyncio.run(main())
