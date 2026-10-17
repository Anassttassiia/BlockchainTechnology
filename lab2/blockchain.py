from block import Block
from transaction import Wallet


class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.chain = []                      
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_miner = Wallet("Genesis")
        genesis = Block(prev_hash="0" * 64, transactions=[], difficulty=self.difficulty)
        genesis.mine()
        genesis.sign(genesis_miner)
        self.chain.append(genesis)

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def get_block(self, index: int) -> Block:
        return self.chain[index]

    def add_block(self, block: Block) -> bool:
        if block.prev_hash != self.get_last_block().hash:
            print("Блок відхилено: prev_hash не збігається з гешем останнього блока")
            return False
        if not block.is_valid():
            print("Блок відхилено: блок не пройшов перевірку")
            return False
        self.chain.append(block)
        return True

    def create_block(self, transactions: list, miner: Wallet) -> bool:
        block = Block(prev_hash=self.get_last_block().hash,
                      transactions=transactions, difficulty=self.difficulty)
        block.mine()
        block.sign(miner)
        return self.add_block(block)

    def is_chain_valid(self) -> bool:
        for i, block in enumerate(self.chain):
            if not block.is_valid():
                print(f"  Блок #{i} невалідний")
                return False
            if i > 0 and block.prev_hash != self.chain[i - 1].hash:
                print(f"  Блок #{i}: prev_hash не збігається з гешем блока #{i - 1}")
                return False
        return True

    def __len__(self):
        return len(self.chain)

    def __str__(self):
        lines = [f"Blockchain (кількість блоків: {len(self.chain)})"]
        for i, block in enumerate(self.chain):
            lines.append(f"  #{i}: hash={block.hash[:20]}...  prev={block.prev_hash[:20]}...  "
                         f"транзакцій={len(block.transactions)}")
        return "\n".join(lines)
