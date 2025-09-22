import socket
import threading
import json
from datetime import datetime
from src.simulacao_bancaria.seguranca import *
import base64
import shutil

class BankServer:
    def __init__(self, host='localhost', port=42000):
        self.host = host
        self.port = port
        self.users = {}
        self.transactions = []
        self.server_socket = None

    
    def startServer(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f"Servidor iniciado em {self.host}:{self.port}")

        while(True):
            client_socket, addr = self.server_socket.accept()
            print(f"Conexao estabelecida com {addr}")
            client_thead = threading.Thread(
                target=self.handle_client,
                args=(client_socket,)
            )
            client_thead.start()
    
    def handle_client(self, client_socket):
        """ Lida com o Cliente """
        try:
            while(True):
                data = client_socket.recv(4096)
                if not data:
                    break
                
                request = json.loads(data.decode("utf-8"))
                response = self.process_request(request)

                client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"ERRO: Falha no cliente: {e}")
        finally:
            client_socket.close()
            
        
    def process_request(self, request):
        """ Processa as Requisicoes do cliente """
        
        action = request.get('action')

        match action:
            case 'register':
                return self.register_user(request)
            case 'get_balance':
                return self.get_balance(request)
            case 'get_users':
                return self.get_users_list()
            case 'make_transaction':
                return self.make_transaction(request)
            case 'get_transactions':
                return self.get_transactions()
            case _:
                return {'status': 'error', 'message': 'Ação inválida'}

    def register_user(self, request):
        """ Regista um novo usuario no servidor """
        nome = request.get("nome")
        chave_publica64 = request.get("chave_publica")

        if nome in self.users:
            return {'status': 'erro', 'message': f'ERRO: Usuario ja existe'}

        self.users[nome] = {
            'nome': nome,
            'chave_publica': chave_publica64,
            'balance': 1000.00 #Saldo
        }

        print(f"Usuario criado com sucesso: {nome}")
        return {'status': 'success', 'message': 'Usuario registrado com sucesso'}
        
    def get_balance(self, request):
        nome = request.get("nome")

        if nome not in self.users:
            return {'status': 'erro', 'message': f'usuário {nome} não encontrado'}
        
        saldo = self.users[nome]['balance']
        return  {'status': 'success', 'balance': saldo}    
    
    def get_users_list(self):
        return {'status': 'success', 'users': list(self.users.keys())}
    
    def validate_balance(self, sender, amount):
        return self.users(sender, {}).get('balance', 0) >=  amount

    def make_transaction(self, request):
        """ Processa a transaçao """
        sender = request.get('sender')
        receiver = request.get('receiver')
        amount = request.get('amount')
        date = request.get('date')

        try:
            signature = request.get('signature')
        except (TypeError, ValueError):
            return {'status': 'error', 'message': 'Formato inválido.'}
        
        transaction_data = {
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'date': date
        }

        if transaction_data['sender'] not in self.users:
            return {'status': 'error', 'message': 'Remetente nao encontrado'}

        if transaction_data['receiver'] not in self.users:
            return {'status': 'error', 'message': 'Destinatario nao encontrado'}

        sender_public_key64 = self.users[sender]['chave_publica']
        sender_public_key_pem = base64.b64decode(sender_public_key64)
        sender_public_key = carregar_chave_publica_pem(sender_public_key_pem)


        transaction =  json.dumps({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'date': date,
        }).encode()

        is_signature_valide = verificar_assinatura(sender_public_key, transaction, signature, config_padding())
        print(F'Assinatura Valida: {is_signature_valide}')

        if not is_signature_valide:
            transaction_data['signature'] = signature.hex()
            transaction_data['status'] = 'reject'
            transaction_data['processed_at'] = datetime.now().isoformat()

        else:
            if not self.validate_balance(sender, amount):
                return {'status': 'error', 'message': 'Falta dinheiro'}
            
            self.users['sender']['balance'] -= amount
            self.users['receiver']['balance'] += amount

            transaction_data['signature'] = signature.hex()
            transaction_data['status'] = 'accept'
            transaction_data['processed_at'] = datetime.now().isoformat()
        
        self.transactions.append(transaction_data)

        print(f'Transaç~ao processada: {sender} -> {receiver} - R${amount}')
        return {'status': 'success', 'message': 'Transaç~ao realizada com sucesso'}
        
    def get_transactions(self):
        return {'status': 'success', 'transactions': self.transactions}

if __name__ == "__main__":
    server = BankServer()
    server.startServer()