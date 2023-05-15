from node import *
from utils import LoggerWriter, cleanup_logs, verify_flag
import threading
import logging
from datetime import datetime
import argparse
import os
import signal


# Everything surrounded by ### are the only modifications to this file
# for nice logging and graceful exit of keyboard interrupt
########################################################################################################################
def handle_keyboard_interrupt(sig, frame):
    os._exit(0)


signal.signal(signal.SIGINT, handle_keyboard_interrupt)

f_name = datetime.now().strftime("%D:%H:%M:%S").replace('/', '')
first_colon = f_name.index(':')
f_name = f_name[:first_colon] + '_' + f_name[first_colon + 1:].replace(':', '')
root = logging.getLogger()
logging.basicConfig(filename=f'{f_name}.log',
                    filemode='a',
                    format='%(name)s - %(levelname)s - %(message)s')
sys.stderr = LoggerWriter(root.error)

parser = argparse.ArgumentParser(
    prog='usage_example.py',
    description='Basic blockchain network impl.')

parser.add_argument('--log-stdout', type=verify_flag, nargs='?', const=True, default=False,
                    help='True: route stdout to logger. False (default): stdout to terminal')
parser.add_argument('--clean-logs', type=verify_flag, nargs='?', const=True, default=False,
                    help='True: route stdout to logger. False (default): stdout to terminal')

args = parser.parse_args()
if args.log_stdout:
    sys.stdout = LoggerWriter(root.info)
if args.clean_logs:
    cleanup_logs()
########################################################################################################################

# private key for transactions
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
    bytes.fromhex('6dee02b55d8914c145568cb3f3b84586ead2a85910f5b062d7f3f29ddcb4c7aa'))

# create nodes
runners = [ServerRunner('localhost', 9000 + i, f=1) for i in range(4)]

# start accepting incoming connections
for runner in runners:
    runner.start()

# connect other nodes
for i, runner in enumerate(runners):
    for j in range(4):
        if i != j:
            runner.append(RemoteNode('localhost', 9000 + j))

# create clients to send transactions
clients = [RemoteNode('localhost', 9000 + i) for i in range(4)]

# create a transaction
transaction = make_transaction('hello', private_key, 0)

# set block callback
lock = threading.Lock()
cond = threading.Condition(lock)
blocks = []


def on_new_block(block):
    with lock:
        blocks.append(block)
        cond.notify()


for runner in runners:
    runner.blockchain.set_on_new_block(on_new_block)

# send the transaction
assert (clients[0].transaction(transaction))

# wait for the block from all nodes
with lock:
    cond.wait_for(lambda: len(blocks) == len(runners))

# check that the transaction is committed
assert (all([block['transactions'][0] == transaction for block in blocks]))

# stop the nodes
for runner in runners:
    runner.stop()
