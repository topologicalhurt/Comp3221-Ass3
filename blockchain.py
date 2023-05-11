import hashlib
import json
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519

"""
more updated stuff from labs
"""
def transaction_bytes(transaction: dict):
    return json.dumps({k: transaction.get(k) for k in ['sender', 'message']}, sort_keys=True).encode()


def make_transaction(message: str, private_key: ed25519.Ed25519PrivateKey):
    transaction = {'sender': private_key.public_key().public_bytes_raw().hex(), 'message': message}
    signature = private_key.sign(transaction_bytes(transaction)).hex()
    transaction['signature'] = signature
    return transaction


def validate_transaction(transaction: dict):
    keys = ['sender', 'message', 'signature']
    try:
        if len(transaction) != 3:
            return False
        for key in keys:
            if not isinstance(transaction[key], str):
                return False
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(transaction['sender']))
        if len(transaction['message']) > 70 or not transaction['message'].isalnum():
            return False
        public_key.verify(bytes.fromhex(transaction['signature']), transaction_bytes(transaction))
        return True
    except:
        return False


class Blockchain():
    def __init__(self):
        self.blockchain = []
        self.pool = []
        self.pool_limit = 3
        self.new_block('0' * 64)

    def new_block(self, previous_hash=None):
        block = {
            'index': len(self.blockchain) + 1,
            'transactions': self.pool.copy(),
            'previous_hash': previous_hash or self.blockchain[-1]['current_hash'],
        }
        block['current_hash'] = self.calculate_hash(block)
        self.pool = []
        self.blockchain.append(block)

    def last_block(self):
        return self.blockchain[-1]

    def calculate_hash(self, block: dict):
        block_object: str = json.dumps({k: block.get(k) for k in ['index', 'transactions', 'previous_hash']},
                                       sort_keys=True)
        block_string = block_object.encode()
        raw_hash = hashlib.sha256(block_string)
        hex_hash = raw_hash.hexdigest()
        return hex_hash

    def add_transaction(self, transaction):
        if len(self.pool) < self.pool_limit:
            self.pool.append(transaction)
            return True
        return False
