"""
    Responsabilidades - Cliente gera seu par de chaves
                      - Assinatura da transação
                      - Comunicação com o servidor: conectar com o servidor, enviar os dados da trasação, esperar resposta
                      - 
"""
import socket
import json
import base64
import os
from datetime import datetime

from src.simulacao_bancaria.seguranca import *

class BankClient:
    def __init__(self, host='localhost', port=42000):
        self.host = host
        self.port = port
        self.nome = None
        self.private_key = None
        self.public_key = None
        self.socket = None
    
    def connect(self):
        """ Conexao com o servidor """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print("Conectado ao servidor bancário")
    
    def disconnect(self):
        """ Desconecta do servidor """
        if self.socket:
            self.socket.close()
    
    def send_request(self, request):
        """ Envia as requisicoes ao servidor """
        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv(4096)
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {'status': 'error', 'message': f'ERRO: Falha na comunicaçao: {e}'}
    
    def register(self, nome):
        """ Registra um novo usuario """

        chave_privada_path = f"./rsa/{nome}/chave_privada_{nome}.pem"

        if os.path.exists(chave_privada_path):
            print(f"Usuario {nome} já existe")

            #ler chave - implementar

            chave_privada = ler_chave_privada_arq(nome)
            if chave_privada is None:
                    print("ERRO: ao carregar chave, gerando novo par")
                    chave_privada = criar_chave_privada()
                    salvar_chave_privada_arq(chave_privada, nome)
            print(f"Seja Bem-vindo de volta {nome}")
            action = 'login'
        else:
            print(f"Seja Bem-vindo {nome}, estamos gerando suas chaves")
            chave_privada = criar_chave_privada()
            salvar_chave_privada_arq(chave_privada, nome)
            action = 'register'
            
        chave_publica = criar_chave_publica(chave_privada)

        request = {
            'action': action,
            'nome': nome,
            'chave_publica': base64.b64encode(chave_publica).decode('utf-8')
        }

        response = self.send_request(request)
        if action == 'register' and response['status'] == 'success':
            self.nome = nome
            print("Usuário registrado com sucesso!")
        elif action == 'login' and response['status'] == 'success':
            self.nome = nome
            print("Usuário logado com sucesso!")
        else:
            print(f'ERRO: Problema no registro: {response['message']}')

        return response

    def get_balance(self):
        """ Pegar saldo """
        request = {
            'action': 'get_balance',
            'nome': self.nome
        }

        response = self.send_request(request)
        if response['status'] == 'success':
            print(f"Saldo atual: R${response['balance']:.2f}")
        else:
            print(f"Erro ao obter saldo: {response['message']}")
        return response
    
    def get_users(self):
        """ Pegar lista de usuarios """
        request = {'action': 'get_users'}

        response = self.send_request(request)

        if response['status'] == 'success':
            print("Usuários disponíveis:")
            for user in response['users']:
                print(f"  - {user}")
        else:
            print(f"Erro ao obter usuários: {response['message']}")
        return response

    def make_transaction(self, receiver, amount):
        """ Realizar transaçao """

        #Criar transaçao
        transaction = {
            'sender': self.nome,
            'receiver': receiver,
            'amount': amount,
            'date': str(datetime.now()),
        }

        transaction_json = json.dumps(transaction, sort_keys=True)
        transaction_bytes = transaction_json.encode('utf-8')
        
        padding_config = config_padding()

        chave_privada = ler_chave_privada_arq(self.nome)
        
        signature = assinar_dados(chave_privada, transaction_bytes, padding_config)

        request = {
            'action': 'make_transaction',
            'sender': self.nome,
            'receiver': receiver,
            'amount': amount,
            'date': str(datetime.now()),
            'signature': signature.hex(),
            'transaction': transaction_json,
            'status': 'pending'
        }

        response = self.send_request(request)
        if response['status'] == 'success':
            print(f"{response['message']}")
        else:
            print(f"Erro na transação: {response['message']}")
        return response

    def get_transaction_history(self):
        """ Obter as transações """

        request = {
            'action' : 'get_transactions'
        }

        response = self.send_request(request)

        if response['status'] == 'success':
            print("\nHistorico de Transações:")
            for trans in response['transactions']:
                status = "/" if trans['status'] == 'accept' else "NOT"
                print(f"{trans}" if trans['sender'] == self.nome else f"Nenhuma transaç~ao para {self.nome}")
        else:
            print(f'Erro ao buscar transacoes: {response['message']}')
        
        return response


def main():
    client = BankClient()
    client.connect()

    try:
        while True:
            print("\n=== Sistema Bancário ===")
            print("1. Registar usuario")
            print("2. Ver Saldo")
            print("3. Listar usuarios")
            print("4. Fazer transaçao")
            print("5. Ver historico")
            print("6. Sair")

            choice = int(input("Escolha uma opçao: "))
            match choice:
                case 1:
                    nome = input("Nome de usuario: ")
                    client.register(nome)
                case 2:
                    if not client.nome:
                        print('Voce precisa se registrar')
                        continue
                    client.get_balance()
                case 3:
                    client.get_users()
                case 4:
                    if not client.nome:
                        print('Voce precisa se registrar')
                        continue
                    
                    receiver = input("Destinatario: ")
                    amount = float(input(f"Valor: R$ "))
                    client.make_transaction(receiver, amount)
                
                case 5:
                     client.get_transaction_history()

    finally:
        print()


if __name__ == "__main__":
    main()
