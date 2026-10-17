from blockchain import Blockchain
from block import Block
from transaction import Transaction, Wallet


def make_tx(sender: Wallet, receivers: list) -> Transaction:
    tx = Transaction(sender.address,
                     [{"address": w.address, "amount": amount} for w, amount in receivers],
                     sender.public_key_hex)
    tx.sign(sender)
    return tx


def title(text: str):
    print("\n" + "=" * 70 + f"\n{text}\n" + "=" * 70)

title("1. Створюємо гаманці учасників")
alice, bob, carol, dave = Wallet("Alice"), Wallet("Bob"), Wallet("Carol"), Wallet("Dave")
miner = Wallet("Miner")
for w in (alice, bob, carol, dave, miner):
    print(w)

title("2. Створюємо блокчейн і генезис-блок")
bc = Blockchain(difficulty=4)

title("3. Додаємо 3 блоки по декілька транзакцій")
block1_txs = [make_tx(alice, [(bob, 0.5)]),
              make_tx(bob, [(carol, 0.2), (dave, 0.1)])]
block2_txs = [make_tx(carol, [(alice, 0.05)]),
              make_tx(dave, [(bob, 0.03)]),
              make_tx(alice, [(carol, 0.1), (dave, 0.1)])]
block3_txs = [make_tx(bob, [(alice, 0.15)]),
              make_tx(carol, [(dave, 0.02)])]

for txs in (block1_txs, block2_txs, block3_txs):
    print("Блок додано:", bc.create_block(txs, miner))

print()
print(bc)

title("4. Детальна інформація про блок #2")
b2 = bc.get_block(2)
print(b2)
print("Дерево Меркла:")
b2.print_merkle_tree()
print("\nПерша транзакція блока:")
print(b2.transactions[0])

title("5. Перевірка коректного ланцюга")
print("Усі транзакції валідні:", all(tx.is_valid() for b in bc.chain for tx in b.transactions))
print("Усі блоки валідні:     ", all(b.is_valid() for b in bc.chain))
print("Ланцюг валідний:       ", bc.is_chain_valid())

title("6. Тест: підроблений підпис транзакції")
tx = Transaction(alice.address, [{"address": dave.address, "amount": 10}], alice.public_key_hex)
tx.signature = dave.sign(tx.tx_hash)  
print("Геш правильний:   ", tx.verify_hash())
print("Підпис правильний:", tx.verify_signature())
print("Транзакція валідна:", tx.is_valid())

title("7. Тест: спроба додати блок з підробленою транзакцією")
bad_block = Block(prev_hash=bc.get_last_block().hash, transactions=[tx], difficulty=bc.difficulty)
bad_block.mine()
bad_block.sign(miner)
print("Блок додано:", bc.add_block(bad_block))

title("8. Тест: спроба додати блок з неправильним prev_hash")
wrong_block = Block(prev_hash="1" * 64, transactions=[make_tx(alice, [(bob, 0.01)])],
                    difficulty=bc.difficulty)
wrong_block.mine()
wrong_block.sign(miner)
print("Блок додано:", bc.add_block(wrong_block))

title("9. Тест: підробка транзакції в уже доданому блоці #1")
original = block1_txs[0].get_amount()
block1_txs[0].set_amount(100)
print("Блок #1 валідний:", bc.get_block(1).is_valid())
print("Ланцюг валідний:", bc.is_chain_valid())
block1_txs[0].set_amount(original)  
print("Після відновлення ланцюг валідний:", bc.is_chain_valid())

title("10. Тест: зловмисник змінює блок #1 і перемайнює його")
b1 = bc.get_block(1)
b1.set_timestamp(b1.get_timestamp() + 1)  
b1.nonce = 0
b1.hash = b1.calculate_hash()
b1.mine()
b1.sign(miner)
print("Блок #1 сам по собі валідний:", b1.is_valid())
print("Ланцюг валідний:", bc.is_chain_valid())
print("Висновок: щоб підробка пройшла, треба перемайнити і всі наступні блоки.")
