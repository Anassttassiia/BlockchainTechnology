import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from transaction import Transaction, Wallet, sha256, public_key_from_hex

def build_merkle_tree(tx_hashes: list) -> list:
    if not tx_hashes:
        return [["0" * 64]]
    levels = [list(tx_hashes)]
    while len(levels[-1]) > 1:
        current = list(levels[-1])
        if len(current) % 2 == 1:
            current.append(current[-1])
        next_level = [sha256(current[i] + current[i + 1]) for i in range(0, len(current), 2)]
        levels.append(next_level)
    return levels

class Block:
    def __init__(self, prev_hash: str, transactions: list, difficulty: int = 4, version: int = 1):
        self.version = version                    
        self.prev_hash = prev_hash                
        self.timestamp = time.time()              
        self.difficulty = difficulty              
        self.target = "0" * difficulty + "f" * (64 - difficulty)
        self.nonce = 0                            
        self.transactions = transactions          
        self.merkle_tree = build_merkle_tree([tx.tx_hash for tx in transactions])
        self.merkle_root = self.merkle_tree[-1][0]  
        self.hash = self.calculate_hash()         
        self.miner = None                         
        self.miner_public_key = None
        self.signature = None                     

    def get_header(self) -> str:
        return (f"{self.version}{self.prev_hash}{self.merkle_root}"
                f"{self.timestamp}{self.target}{self.nonce}")

    def calculate_hash(self) -> str:
        return sha256(self.get_header())

    def mine(self, verbose: bool = True):
        start = time.time()
        while int(self.hash, 16) > int(self.target, 16):
            self.nonce += 1
            self.hash = self.calculate_hash()
        if verbose:
            print(f"Блок видобуто: nonce = {self.nonce}, час = {time.time() - start:.2f} с")

    def sign(self, miner_wallet: Wallet):
        self.miner = miner_wallet.address
        self.miner_public_key = miner_wallet.public_key_hex
        self.signature = miner_wallet.sign(self.hash)

    def verify_hash(self) -> bool:
        return (self.hash == self.calculate_hash()
                and int(self.hash, 16) <= int(self.target, 16))

    def verify_merkle_root(self) -> bool:
        recalculated = build_merkle_tree([tx.calculate_hash() for tx in self.transactions])[-1][0]
        return self.merkle_root == recalculated

    def verify_signature(self) -> bool:
        if self.signature is None:
            return False
        try:
            public_key = public_key_from_hex(self.miner_public_key)
            public_key.verify(bytes.fromhex(self.signature),
                              self.hash.encode("utf-8"),
                              ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError):
            return False

    def verify_transactions(self) -> bool:
        return all(tx.is_valid() for tx in self.transactions)

    def is_valid(self) -> bool:
        return (self.verify_hash() and self.verify_merkle_root()
                and self.verify_signature() and self.verify_transactions())

    def get_version(self): return self.version
    def get_prev_hash(self): return self.prev_hash
    def get_timestamp(self): return self.timestamp
    def get_target(self): return self.target
    def get_nonce(self): return self.nonce
    def get_merkle_root(self): return self.merkle_root
    def get_merkle_tree(self): return self.merkle_tree
    def get_transactions(self): return self.transactions
    def get_hash(self): return self.hash
    def get_signature(self): return self.signature

    def set_version(self, version): self.version = version
    def set_prev_hash(self, prev_hash): self.prev_hash = prev_hash
    def set_timestamp(self, timestamp): self.timestamp = timestamp
    def set_nonce(self, nonce): self.nonce = nonce
    def set_transactions(self, transactions): self.transactions = transactions

    def __str__(self):
        time_str = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(self.timestamp))
        sig = self.signature[:16] + "..." if self.signature else "немає"
        return (f"Block(\n"
                f"  hash         = {self.hash}\n"
                f"  version      = {self.version}\n"
                f"  prev_hash    = {self.prev_hash}\n"
                f"  merkle_root  = {self.merkle_root}\n"
                f"  timestamp    = {time_str}\n"
                f"  target       = {self.target}\n"
                f"  nonce        = {self.nonce}\n"
                f"  transactions = {len(self.transactions)}\n"
                f"  miner        = {self.miner}\n"
                f"  signature    = {sig}\n)")

    def print_merkle_tree(self):
        for i, level in enumerate(self.merkle_tree):
            name = "Листки (геші транзакцій)" if i == 0 else (
                "Корінь" if i == len(self.merkle_tree) - 1 else f"Рівень {i}")
            print(f"  {name}: " + "  ".join(h[:10] + "..." for h in level))

if __name__ == "__main__":
    alice, bob, carol, miner = Wallet("Alice"), Wallet("Bob"), Wallet("Carol"), Wallet("Miner")

    tx1 = Transaction(alice.address, [{"address": bob.address, "amount": 0.5}], alice.public_key_hex)
    tx1.sign(alice)
    tx2 = Transaction(bob.address, [{"address": carol.address, "amount": 0.2}], bob.public_key_hex)
    tx2.sign(bob)
    tx3 = Transaction(carol.address, [{"address": alice.address, "amount": 0.1},
                                      {"address": bob.address, "amount": 0.05}], carol.public_key_hex)
    tx3.sign(carol)

    block = Block(prev_hash="0" * 64, transactions=[tx1, tx2, tx3], difficulty=4)
    block.mine()
    block.sign(miner)
    print(block)

    print("Дерево Меркла:")
    block.print_merkle_tree()

    print("\nГеш заголовка правильний:", block.verify_hash())
    print("Корінь Меркла правильний: ", block.verify_merkle_root())
    print("Підпис майнера правильний:", block.verify_signature())
    print("Транзакції валідні:       ", block.verify_transactions())
    print("Блок валідний:            ", block.is_valid())

    print("\nПідробка: змінюємо суму транзакції всередині блока ")
    tx2.set_amount(999)
    print("Корінь Меркла правильний: ", block.verify_merkle_root())
    print("Транзакції валідні:       ", block.verify_transactions())
    print("Блок валідний:            ", block.is_valid())
    tx2.set_amount(0.2)  

    print("\nПідробка: змінюємо nonce")
    block.set_nonce(block.get_nonce() + 1)
    print("Геш заголовка правильний:", block.verify_hash())
    print("Блок валідний:            ", block.is_valid())
