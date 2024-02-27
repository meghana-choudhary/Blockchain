#Creating Cryptocurrency-Megcoins
import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#Part1-Building Blockchain
class Blockchain:
    def __init__(self):
        self.chain= []
        self.transactions=[]
        self.create_block(proof=1,previous_hash='0')
        self.nodes=set() 
    
    def create_block(self,proof,previous_hash):
        block={'Index':len(self.chain)+1,
               'Timestamp': str(datetime.datetime.now()),
               'Proof':proof,
               'Previous_hash':previous_hash,
               'Transactions': self.transactions
               }
        self.transactions=[] 
        self.chain.append(block)
        return block;
    
    def get_last_block(self):
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            hash_operation= hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]=='0000':
                check_proof=True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block= json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        block_index=1
        while block_index < len(chain):
            block=chain[block_index]
            if block['Previous_hash'] != self.hash(previous_block):
                return False
            previous_proof=previous_block['Proof']
            proof=block['Proof']
            hash_operation= hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] !='0000':
                return False
            previous_block=block
            block_index += 1
        return True
    
    def add_transactions(self,sender,receiver,amount):
        self.transactions.append({'Sender': sender,
                           'Receiver': receiver,
                           'Amount': amount})
        previous_block = self.get_last_block()
        return previous_block['Index']+1
    
    def add_node(self,address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        network=self.nodes
        longest_chain=None
        max_length=len(self.chain)
        for node in network: 
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code==200:
                length = response.json()['Length']
                chain=response.json()['Chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length 
                    longest_chain=chain
        if longest_chain: 
            self.chain = longest_chain
            return True
        return False 
    

#Part2-Mining our blockchain


#Creating our webapp

app=Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

#Creating an address for the node on port
node_address = str(uuid4()).replace('-','')

#Creating blockchain

blockchain=Blockchain()

#Mining a block

@app.route("/mine_block", methods=['GET'])
def mine_block():
    previous_block=blockchain.get_last_block()
    previous_proof=previous_block['Proof']
    proof=blockchain.proof_of_work(previous_proof)
    previous_hash=blockchain.hash(previous_block)
    blockchain.add_transactions(sender=node_address,receiver='Meghana', amount=1)
    block=blockchain.create_block(proof, previous_hash)
    response={'Message':'Congratulations!You have mined a block.',
             'Index':block['Index'],
             'Timestamp':block['Timestamp'],
             'Proof':block['Proof'],
             'Previous_hash':block['Previous_hash'],
             'Transactions': block['Transactions']}
    return jsonify(response), 200

#Getting the full chain
@app.route("/get_chain", methods=['GET'])
def get_chain():
    response={'Chain':blockchain.chain,
              'Length':len(blockchain.chain)}
    return jsonify(response), 200 

#Check chain is valid or not
@app.route("/is_valid", methods=['GET'])
def is_valid():
    is_valid=blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response={'Message': 'Blockchain is valid!'}
    else:
        response={'Message': 'Blockchain is not valid!'}
    return jsonify(response), 200

#Adding new transaction to Blockchain
@app.route("/add_transactions", methods=['POST'])
def add_transactions():
    json= request.get_json()
    transaction_keys=['Sender','Receiver','Amount']
    if not all (key in json for key in transaction_keys):
        return 'Some problem in input', 400
    index = blockchain.add_transactions(json['Sender'],json['Receiver'],json['Amount'])
    response = {'Message': f'The transaction will be added in block {index}.'}
    return jsonify(response), 201
 
#Part3-Creating a decentralized application


#Connecting a new node to the decentralised network 
@app.route("/connect_node", methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes=json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'Message': 'All the nodes are now connected to the network. The Meghana blockchain now has the following nodes:',
                'Total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

#Replacing the chain by the longest chain if needed
@app.route("/replace_chain", methods=['GET'])
def replace_chain():
    is_chain_replaced=blockchain.replace_chain()
    if is_chain_replaced:
        response={'Message': 'The node had different chains so the chain was replaced by the longest chain!',
                  'New_chain': blockchain.chain}
    else:
        response={'Message': 'The node already has the longest chain!',
                  'Actual_chain': blockchain.chain}
    return jsonify(response), 200



#Running the app
app.run(host='0.0.0.0', port=5002)