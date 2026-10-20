import copy
import time

from block import Block
from blockchain import Blockchain
from transaction import Transaction, Wallet

BLOCK_REWARD = 3.125          
MAX_TXS_IN_BLOCK = 3         


class CoinbaseTransaction(Transaction):
    def __init__(self, miner_address: str, reward: float = BLOCK_REWARD):
        super().__init__(sender="COINBASE",
                         outputs=[{"address": miner_address, "amount": reward}],
                         sender_public_key="")

    def is_valid(self) -> bool:
        return self.verify_hash() and self.amount == BLOCK_REWARD


class Node:
    def __init__(self, name: str, genesis: Block, difficulty: int = 4):
        self.name = name
        self.wallet = Wallet(name)                                   
        self.blockchain = Blockchain(difficulty=difficulty, genesis=genesis)  
        self.mempool = []                                            
        self.peers = []                                             

    def connect(self, nodes: list):
        self.peers = [n for n in nodes if n is not self]

    # транзакції 
    def add_transaction(self, tx: Transaction) -> bool:
        if not tx.is_valid():
            return False
        if any(t.tx_hash == tx.tx_hash for t in self.mempool):
            return False
        self.mempool.append(copy.deepcopy(tx))   
        return True

    # майнінг 
    def mine_block(self) -> Block:
        selected = self.mempool[:MAX_TXS_IN_BLOCK]
        coinbase = CoinbaseTransaction(self.wallet.address)
        transactions = [coinbase] + selected

        block = Block(prev_hash=self.blockchain.get_last_block().hash,
                      transactions=transactions,
                      difficulty=self.blockchain.difficulty)
        start = time.time()
        block.mine(verbose=False)
        elapsed = time.time() - start
        block.sign(self.wallet)

        if not self.accept_block(block):
            raise RuntimeError("Власний блок не пройшов перевірку")
        print(f"[{self.name}] видобув блок #{len(self.blockchain) - 1}: "
              f"nonce = {block.nonce}, час = {elapsed:.2f} с, "
              f"транзакцій = {len(transactions)} (з них 1 coinbase)")
        return block

    # обмін блоками 
    def broadcast_block(self, block: Block):
        for peer in self.peers:
            peer.receive_block(copy.deepcopy(block), sender=self.name)

    def receive_block(self, block: Block, sender: str = "?") -> bool:
        ok = self.accept_block(block)
        status = "прийняв" if ok else "ВІДХИЛИВ"
        print(f"    [{self.name}] {status} блок від {sender} (hash={block.hash[:16]}...)")
        return ok

    def verify_block(self, block: Block) -> bool:
        txs = block.transactions
        if not txs or not isinstance(txs[0], CoinbaseTransaction):
            return False                                   
        if any(isinstance(tx, CoinbaseTransaction) for tx in txs[1:]):
            return False                                  
        if txs[0].outputs[0]["address"] != block.miner:
            return False                                   
        return block.is_valid()                           

    def accept_block(self, block: Block) -> bool:
        if not self.verify_block(block):
            return False
        if not self.blockchain.add_block(block):         
            return False
        included = {tx.tx_hash for tx in block.transactions}
        self.mempool = [tx for tx in self.mempool if tx.tx_hash not in included]
        return True

 #node.py

    # допоміжне 
    def mined_blocks(self) -> int:
        return sum(1 for b in self.blockchain.chain if b.miner == self.wallet.address)

    def __str__(self):
        return (f"Node({self.name}): блоків = {len(self.blockchain)}, "
                f"останній hash = {self.blockchain.get_last_block().hash[:16]}..., "
                f"у mempool = {len(self.mempool)}")
