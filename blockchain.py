import hashlib
import json
import re

"""
******************************************************************
RIPPED STRAIGHT FROM ONE OF THE TUTS, MAY BE A GOOD STARTING POINT
AND MAY JUST HAVE EVERYTHING WE NEED
******************************************************************
"""

sender_valid = re.compile('^[a-fA-F0-9]{64}$')


def validate_transaction(transaction: dict):
    sender_validation = False
    content_validation = False

    if transaction.get('sender') and isinstance(transaction['sender'], str):
        sender_validation = sender_valid.search(transaction['sender'])

    if transaction.get('message') and isinstance(transaction['message'], str):
        content_validation = len(transaction['message']) <= 70 and transaction['message'].isalnum()

    return sender_validation and content_validation


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
