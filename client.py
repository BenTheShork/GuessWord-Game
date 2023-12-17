import socket
import threading
import json
import time
class GuessWordClient:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.sock = None
        self.client_id = None
        self.canStart = False
        self.gameOver = False
        self.passowrd = ""
        self.connected = False
    def encode_message(self, message_type, payload):
        """Encodes a message into a binary format."""
        return bytes([message_type]) + payload.encode()
    def decode_message(self, data):
        message_type = data[0]
        payload = data[1:].decode()
        return message_type, payload
    def connect_tcp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        threading.Thread(target=self.receive_messages).start()
    def connect_unix(self, unix_socket_path):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.connect(unix_socket_path)
            print(f"Connected to server via Unix socket at {unix_socket_path}")
            threading.Thread(target=self.receive_messages).start()
        except socket.error as e:
            print(f"Could not connect to Unix socket: {e}")
    def send_hint(self, hint):
        hint_message = self.encode_message(14, hint)
        self.sock.send(hint_message)
    def receive_messages(self):
        while True:
            data = self.sock.recv(1024)
            if data:
                message_type, payload = self.decode_message(data)
                if message_type == 15: 
                    print("Connected to server.")
                    self.connected = True
                elif message_type == 1:
                    print(f"Assigned Client ID: {payload}")
                elif message_type == 8:
                    print("List of opponents:", payload)
                elif message_type == 10:  
                    print("Match accepted!")
                    self.canStart = True
                elif message_type == 11: 
                    print("Match declined.")
                    self.gameOver = True
                elif message_type == 5:  
                    opponent_id, word = payload.split(';')
                    response = input(f"Match request from {opponent_id}, accept? (yes/no): ").strip().lower()
                    self.send_match_response(opponent_id, 'accept' if response == 'yes' else 'decline')
                    if response != 'yes':
                        self.gameOver = True
                elif message_type == 12: 
                    result, guess = payload.split(';')
                    print(f"Correct! The guesser guessed the word '{guess}'.")
                    self.gameOver = True
                elif message_type == 13:  
                    result, guess = payload.split(';')
                    print(f"Incorrect guess: '{guess}'.")
                elif message_type == 7:
                    print(payload)
                    self.gameOver = True
                elif message_type == 14:
                    print(f"Hint from opponent: {payload}")
    def send_match_response(self, opponent_id, response):
        payload = f"{opponent_id};{response}"  
        response_message = self.encode_message(9, payload)
        self.sock.send(response_message)

    def list_opponents(self): 
        request = self.encode_message(2, '')
        self.sock.send(request)
    def request_match(self, opponent_id, word):
        payload = f"{opponent_id};{word}" 
        request = self.encode_message(4, payload)
        self.sock.send(request)
    def send_guess(self, guess):
        message = self.encode_message(11, guess)
        self.sock.send(message)
    def send_pass(self, password):
        message = self.encode_message(16, password)
        self.sock.send(message)
if __name__ == "__main__":
    use_unix_socket = input("Connect via Unix socket? (yes/no): ").lower() == 'yes'
    client = GuessWordClient()
    if use_unix_socket:
        unix_socket_path = '/tmp/guessword.sock'  
        client.connect_unix(unix_socket_path)
    else:
        client.host = 'localhost'
        client.port = 12345
        client.connect_tcp()
    time.sleep(0.5)
    if not client.connected:
        print("Could not connect to server.")
        exit(1)
    client.send_pass(input("Enter password: "))
    time.sleep(0.5)
    if client.gameOver:
        exit(1)
    start = input("Please choose whether you want to create lobby (create) or just press (enter) and wait for invatation: ")
    if start == 'create':
        client.list_opponents()
        time.sleep(0.2)
        opponent_id = input("Enter opponent ID: ")
        word = input("Enter word to guess: ")
        if ';' in word or 'quit' in word:
            print("Word cannot contain semicolons or word 'quit'.")
            exit(1)
        print("Waiting for opponent to accept...")
        client.request_match(opponent_id, word)
        while not client.gameOver:
            if client.canStart:
                time.sleep(0.2)
                hint = input("You can input hint at any time: \n")
                client.send_hint(hint)
    else:
        print("If you wish to give up when game starts, type 'quit'.")
        print("Waiting for your invitation...")
        while not client.gameOver:
            if client.canStart:
                time.sleep(0.2)
                guess = input("Enter your guess: \n")
                if guess == 'quit':
                    client.gameOver = True
                client.send_guess(guess)
                time.sleep(0.5)
    print("Reconnect to server to start the game again.")
