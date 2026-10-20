import time

from block import Block
from node import CoinbaseTransaction
from transaction import Wallet

BLOCKS_PER_LEVEL = 5
miner = Wallet("Miner")

print(f"{'Складність':>10} | {'Target (початок)':<16} | {'Очікувано 16^d':>14} | "
      f"{'Сер. nonce':>12} | {'Сер. час, с':>11}")
print("-" * 76)
for difficulty in range(1, 6):
    nonces, times = [], []
    prev = "0" * 64
    for _ in range(BLOCKS_PER_LEVEL):
        block = Block(prev_hash=prev, transactions=[CoinbaseTransaction(miner.address)],
                      difficulty=difficulty)
        start = time.time()
        block.mine(verbose=False)
        times.append(time.time() - start)
        nonces.append(block.nonce)
        prev = block.hash
    target = block.target[:8] + "..."
    print(f"{difficulty:>10} | {target:<16} | {16 ** difficulty:>14,} | "
          f"{sum(nonces) / len(nonces):>12,.0f} | "
          f"{sum(times) / len(times):>11.3f}")
print("\nКожен додатковий нуль збільшує кількість спроб приблизно в 16 разів.")
