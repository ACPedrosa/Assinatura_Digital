"""
    seguranca - arquivo destinado a implementação da parte de segurança do sistema e transação bancário
    @autor(a): Ana Caroline Pedrosa
    Date: 03/09/2025
"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import os

def criar_chave_privada():
  private_key = rsa.generate_private_key(
                                          public_exponent=65537,
                                          key_size=3072,
                                          backend=default_backend(),
                                        )
  return private_key

def criar_chave_publica(private_key): 
  public_key = private_key.public_key()
  pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
  )
  
  return pem


def salvar_chave_privada_arq(private_key, nome):
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(), )
    
    os.makedirs(f'./rsa/{nome}/', exist_ok=True)
    with open(f'./rsa/{nome}/chave_privada_{nome}.pem', 'xb') as private_file:
        private_file.write(private_bytes)

def salvar_chave_publica_arq(public_key, nome):
    public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo, )

    with open(f'./rsa/{nome}/chave_publica_{nome}.pem', 'xb') as public_file:
        public_file.write(public_bytes)
  
def ler_chave_publica_arq(nome):
  key_input = f"./rsa/{nome}/chave_publica_{nome}.pem"
  with open(key_input, "rb") as f: key_bytes = f.read()
  return serialization.load_pem_public_key(key_bytes)

def ler_chave_privada_arq(nome):
  key_input = f"./rsa/{nome}/chave_privada_{nome}.pem"
  with open(key_input, "rb") as f: key_bytes = f.read()
  return serialization.load_pem_private_key(key_bytes, password=None)
   
def carregar_chave_publica_pem(public_key_pem_bytes):
  return serialization.load_pem_public_key(public_key_pem_bytes)

def config_padding():
  padding_config = padding.PSS(
                              mgf=padding.MGF1(hashes.SHA256()),
                              salt_length=padding.PSS.MAX_LENGTH
                            )
  return padding_config


def verificar_assinatura(public_key, message: bytes, signature: bytes, padding_config) -> bool:
    try:
        public_key.verify(
            signature,
            message,
            padding_config,
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def assinar_dados(private_key, message, padding_config):
  signature = private_key.sign(
                              message,
                              padding_config,
                              hashes.SHA256()
                            )
  return signature

