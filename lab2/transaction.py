import hashlib
import json
import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def ripemd160(data: bytes) -> bytes:
    try:
        return hashlib.new("ripemd160", data).digest()
    except ValueError:
        digest = hashes.Hash(hashes.RIPEMD160())
        digest.update(data)
        return digest.finalize()


def public_key_to_hex(public_key) -> str:
    return public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.CompressedPoint,
    ).hex()


def public_key_from_hex(key_hex: str):
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), bytes.fromhex(key_hex))


def address_from_public_key(key_hex: str) -> str:
    sha = hashlib.sha256(bytes.fromhex(key_hex)).digest()
    return ripemd160(sha).hex()


class Wallet:
    def __init__(self, name: str):
        self.name = name
        self.private_key = ec.generate_private_key(ec.SECP256K1())
        self.public_key_hex = public_key_to_hex(self.private_key.public_key())
        self.address = address_from_public_key(self.public_key_hex)

    def sign(self, message: str) -> str:
        signature = self.private_key.sign(message.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
        return signature.hex()

    def __str__(self):
        return f"Wallet({self.name}, address={self.address})"


class Transaction:
    def __init__(self, sender: str, outputs: list, sender_public_key: str, tx_timestamp: float = None):
        self.sender = sender                          
        self.outputs = outputs                        
        self.amount = sum(o["amount"] for o in outputs)  
        self.tx_timestamp = tx_timestamp if tx_timestamp is not None else time.time()
        self.sender_public_key = sender_public_key    
        self.signature = None                        
        self.tx_hash = self.calculate_hash()        

    def get_data(self) -> str:
        data = {
            "sender": self.sender,
            "outputs": self.outputs,
            "amount": self.amount,
            "tx_timestamp": self.tx_timestamp,
            "sender_public_key": self.sender_public_key,
        }
        return json.dumps(data, sort_keys=True)

    def calculate_hash(self) -> str:
        return sha256(self.get_data())

    def sign(self, wallet: Wallet):
        if wallet.address != self.sender:
            raise ValueError("Підписати транзакцію може лише її відправник")
        self.signature = wallet.sign(self.tx_hash)

    def verify_hash(self) -> bool:
        return self.tx_hash == self.calculate_hash()

    def verify_signature(self) -> bool:
        if self.signature is None:
            return False
        if address_from_public_key(self.sender_public_key) != self.sender:
            return False
        try:
            public_key = public_key_from_hex(self.sender_public_key)
            public_key.verify(bytes.fromhex(self.signature),
                              self.tx_hash.encode("utf-8"),
                              ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError):
            return False

    def is_valid(self) -> bool:
        return self.verify_hash() and self.verify_signature()

    def get_sender(self): return self.sender
    def get_outputs(self): return self.outputs
    def get_amount(self): return self.amount
    def get_tx_timestamp(self): return self.tx_timestamp
    def get_tx_hash(self): return self.tx_hash
    def get_signature(self): return self.signature

    def set_sender(self, sender): self.sender = sender
    def set_outputs(self, outputs): self.outputs = outputs
    def set_amount(self, amount): self.amount = amount
    def set_tx_timestamp(self, tx_timestamp): self.tx_timestamp = tx_timestamp

    def __str__(self):
        time_str = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(self.tx_timestamp))
        outs = ", ".join(f"{o['address'][:10]}...: {o['amount']} BTC" for o in self.outputs)
        sig = self.signature[:16] + "..." if self.signature else "немає"
        return (f"Transaction(\n"
                f"  hash      = {self.tx_hash}\n"
                f"  sender    = {self.sender}\n"
                f"  outputs   = [{outs}]\n"
                f"  amount    = {self.amount} BTC\n"
                f"  timestamp = {time_str}\n"
                f"  signature = {sig}\n)")

if __name__ == "__main__":
    alice = Wallet("Alice")
    bob = Wallet("Bob")
    carol = Wallet("Carol")
    print(alice)
    print(bob)
    print(carol)

    tx = Transaction(
        sender=alice.address,
        outputs=[{"address": bob.address, "amount": 0.5},
                 {"address": carol.address, "amount": 0.2}],
        sender_public_key=alice.public_key_hex,
    )
    tx.sign(alice)
    print("\n", tx, sep="")
    print("Геш правильний:   ", tx.verify_hash())
    print("Підпис правильний:", tx.verify_signature())
    print("Транзакція валідна:", tx.is_valid())

    print("\nЗмінюємо суму на 100 BTC")
    tx.set_amount(100)
    print("Геш правильний:   ", tx.verify_hash())
    print("Транзакція валідна:", tx.is_valid())

    print("\nBob намагається підписати транзакцію Alice")
    tx2 = Transaction(alice.address, [{"address": bob.address, "amount": 1}], alice.public_key_hex)
    try:
        tx2.sign(bob)
    except ValueError as e:
        print("Помилка:", e)
