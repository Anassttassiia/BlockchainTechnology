import random

from block import Block
from node import Node, CoinbaseTransaction
from transaction import Transaction, Wallet

DIFFICULTY = 4
random.seed()


def title(text: str):
    print("\n" + "=" * 70 + f"\n{text}\n" + "=" * 70)

# Мережа 
title("1. Створюємо мережу з 3 вузлів зі спільним генезис-блоком")
genesis_miner = Wallet("Genesis")
genesis = Block(prev_hash="0" * 64, transactions=[], difficulty=DIFFICULTY)
genesis.mine(verbose=False)
genesis.sign(genesis_miner)

nodes = [Node(name, genesis, DIFFICULTY) for name in ("Node-A", "Node-B", "Node-C")]
for node in nodes:
    node.connect(nodes)
    print(node)

# Транзакції 
title("2. Генеруємо 12 випадкових транзакцій і розсилаємо їх у mempool усіх вузлів")
users = [Wallet(name) for name in ("Alice", "Bob", "Carol", "Dave", "Eve")]
for i in range(12):
    sender, receiver = random.sample(users, 2)
    amount = round(random.uniform(0.01, 1.0), 4)
    tx = Transaction(sender.address, [{"address": receiver.address, "amount": amount}],
                     sender.public_key_hex)
    tx.sign(sender)
    for node in nodes:
        node.add_transaction(tx)
    print(f"  tx{i + 1:>2}: {sender.name:>5} -> {receiver.name:<5} {amount} BTC  "
          f"(hash={tx.tx_hash[:12]}...)")
print(f"\nУ mempool кожного вузла: {[len(n.mempool) for n in nodes]} транзакцій")

# Майнінг
title("3. Вузли по черзі майнять блоки і розсилають їх іншим")
round_no = 0
while nodes[0].mempool:
    miner = nodes[round_no % len(nodes)]
    print(f"\nРаунд {round_no + 1}:")
    block = miner.mine_block()
    miner.broadcast_block(block)
    round_no += 1

# Результат 
title("4. Стан локальних блокчейнів після майнінгу")
for node in nodes:
    print(node)
same = len({n.blockchain.get_last_block().hash for n in nodes}) == 1
print("\nУсі вузли мають однаковий ланцюг:", same)
print("Ланцюги валідні:", [n.blockchain.is_chain_valid() for n in nodes])

print("\nЛанцюг вузла Node-A:")
print(nodes[0].blockchain)

print("\nВинагороди майнерів:")
for node in nodes:
    print(f"  {node.name}: блоків = {node.mined_blocks()}, "
          f"винагорода = {node.mined_blocks() * 3.125} BTC")

# Негативні тести
title("5. Тест: Node-C розсилає підроблений блок (змінено суму транзакції)")
alice, bob = users[0], users[1]
tx = Transaction(alice.address, [{"address": bob.address, "amount": 0.3}], alice.public_key_hex)
tx.sign(alice)
for node in nodes:
    node.add_transaction(tx)
bad = nodes[2]
fake = Block(prev_hash=bad.blockchain.get_last_block().hash,
             transactions=[CoinbaseTransaction(bad.wallet.address), tx],
             difficulty=DIFFICULTY)
fake.mine(verbose=False)
fake.sign(bad.wallet)
fake.transactions[1].set_amount(30)          
bad.broadcast_block(fake)

title("6. Тест: Node-C намагається привласнити собі завищену винагороду")
greedy = CoinbaseTransaction(bad.wallet.address, reward=100)
fake2 = Block(prev_hash=bad.blockchain.get_last_block().hash,
              transactions=[greedy, tx], difficulty=DIFFICULTY)
fake2.mine(verbose=False)
fake2.sign(bad.wallet)
bad.broadcast_block(fake2)

title("7. Тест: блок без Proof-of-Work (nonce не підбирали)")
lazy = Block(prev_hash=bad.blockchain.get_last_block().hash,
             transactions=[CoinbaseTransaction(bad.wallet.address), tx], difficulty=DIFFICULTY)
lazy.sign(bad.wallet)                       
print("Геш блока:", lazy.hash[:20], "... (має починатися з", "0" * DIFFICULTY + ")")
bad.broadcast_block(lazy)

title("8. Чесний майнінг: Node-A видобуває блок з цією транзакцією")
block = nodes[0].mine_block()
nodes[0].broadcast_block(block)
for node in nodes:
    print(node)
print("Усі вузли мають однаковий ланцюг:",
      len({n.blockchain.get_last_block().hash for n in nodes}) == 1)
