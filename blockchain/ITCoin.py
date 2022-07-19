# create a blockchain 

import datetime
import hashlib
import json 
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# building a blockchain 
class Blockchain:
    def __init__(self):
        self.chain = [ ]
        self.transactions = [ ]
        self.creat_block( proof = 1  , prev_hash = '0')
        self.nodes = set()
        
    def creat_block(self , proof , prev_hash):
        block = {'index': len(self.chain)+1 ,
                 'timestamp': str(datetime.datetime.now()),
                 'proof' : proof,
                 'prev_hash' : prev_hash,
                 'transactions' : self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_prev_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, prev_proof):
        new_proof = 1 
        check_proof = False 
        while check_proof is False :
            hash_opration = hashlib.sha256(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_opration[0:4] == '0000':
                check_proof = True 
            else:
                new_proof += 1 
        return new_proof
    
    def hash(self, block):
       encoded_block = json.dumps(block, sort_keys= True).encode()
       return hashlib.sha256(encoded_block).hexdigest()
   
    def is_chain_valid(self , chain ):
        prev_block = chain[0]
        block_index = 1 
        while block_index < len(chain):
            block = chain[block_index]
            if block ['prev_hash'] != self.hash(prev_block):
                return False 
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_opration = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_opration[:4] != '0000':
                return False 
            prev_block = block 
            block_index += 1
        return True 
    
    def add_transaction(self, sender ,reciver ,amount ):
        self.transactions.append({'sender' : sender,
                                  'reciver' : reciver,
                                  'amount' : amount })
        prev_block = self.get_prev_block()
        return prev_block['index'] + 1 
    
    def add_node(self , address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc) 
        
    def replace_chain(self) :
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response.status_code == 200:
               length =  response.json()['length']
               chain = response.json()['chain']
               if length > max_length and self.is_chain_valid(chain):
                   max_length = length 
                   longest_chain = chain 
     
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
             
                


# creating a webapp
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

#creating an address for node on port 5000 
node_address = str(uuid4()).replace('-', '')

# creating a block chain 

blockchain = Blockchain()        

# Mining our blockchain 
@app.route('/mine_block' ,  methods = ['GET'])
def mine_block():
    prev_block = blockchain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_block)
    blockchain.add_transaction(sender = node_address, reciver = 'Amey', amount = 1)
    block = blockchain.creat_block(proof, prev_hash)
    response = {'message ': ' Congratulation , you mened a block! ',
                'index ': block['index'] ,
                'timestamp': block['timestamp'],
                'proof ': block['proof'],
                'prev_hash': block['prev_hash'],
                'transactions' : block['transactions']}
    return jsonify(response), 200 
               
# getting the full blockchain 
@app.route('/get_chain' ,  methods = ['GET'])
def get_chain() :
    response = {'chain' : blockchain.chain ,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200 

# checking blockchain is valide 
@app.route('/is_valid' ,  methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid :
        response = {'message' : 'All good. The blockchain is valid '}
    else :
        response = { ' message ' : 'Blockchain is not valid '}
    return jsonify(response), 200         
#adding transaction 
@app.route('/add_transaction' ,  methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_key = ['sender' , 'reciver' , 'amount']
    if not all (key in json for key in transaction_key):
        return 'some element of transaction are missing ', 400 
    index = blockchain.add_transsation(json['sender'],json['reciver'],json['amount'])
    response = {'message' : f'this transaction will be added to the {index}'} 
    return jsonify(response) , 201

 #decentrilizing blockchain 
 #creating a new node 
@app.route('/connect_node' ,  methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "NO node",400
    for node in nodes :
        blockchain.add_node(node)
    response = {'message' : 'All the nodes are now connect . The ITcoin blockchain now contains the following nodes:  ',
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response), 201

#replacing the longest if nedded
@app.route('/replace_chain' ,  methods = ['GET'])
def replace_chain():
    is_chain_repalced = blockchain.replace_chain()
    if   is_chain_repalced :
        response = {'message' : 'The chain is reeplaced by the longest chian',
                    'new_chain' : blockchain.chain}
    else :
        response = { ' message ' : 'All good . The Chain is longest ',
                    'actual_chain' : blockchain.chain }
    return jsonify(response), 200   

 
# running the app
app.run( host = '0.0.0.0' , port = (5000))
 
    