import solana
from solana.publickey import PublicKey
from solana.rpc.client import RpcClient
from solana.transaction import Transaction, TransactionInstruction
from solana programmes import Program
from solana.programs import create_program

class Optimizer:
    def __init__(self):
        self.client = RpcClient('https://api.devnet.solana.com')
        self.program_id = PublicKey('YourProgramId')

    def deploy(self):
        program_id = create_program(
            self.__class__.__module__,
            'optimize',
            self.__class__.__qualname__,
            self.__init__,
            self.__deploy__,
           