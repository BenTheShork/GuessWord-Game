import socket
import threading
import json
import os
class GuessWordServer:
    def __init__(self, host, port, tcp_port, unix_socket_path):
        self.host = host
        self.tcp_port = tcp_port
        self.port = port
        self.unix_socket_path = unix_socket_path
        self.clients = {}
        self.matches = {}
        self.lock = threading.Lock()
        self.client_id_counter = 0
    def encode_message(self, message_type, payload):
        return bytes([message_type]) + payload.encode()

    def decode_message(self, data):
        message_type = data[0]
        payload = data[1:].decode()
        return message_type, payload
    
    def assign_id(self):
        with self.lock:
            client_id = str(self.client_id_counter)
            self.client_id_counter += 1
        return client_id
    def start(self):
        threading.Thread(target=self.start_tcp_server).start()
        threading.Thread(target=self.start_unix_server).start()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client, address = self.sock.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()
    def start_tcp_server(self):
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.bind(('localhost', self.tcp_port))
        tcp_sock.listen(5)
        print(f"TCP server listening on port {self.tcp_port}")

        while True:
            client, address = tcp_sock.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()
    def start_unix_server(self):
        if os.path.exists(self.unix_socket_path):
            os.remove(self.unix_socket_path)

        unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        unix_sock.bind(self.unix_socket_path)
        unix_sock.listen(5)
        print(f"Unix socket server listening on {self.unix_socket_path}")

        while True:
            client, address = unix_sock.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()
    def verify_password(self, password):
        if password == "password":
            return True
        else:
            return False
    def handle_client(self, client):
        init_message = self.encode_message(15, "Initiate")
        client.send(init_message)
        while True:
            try:
                data = client.recv(1024)
                message_type, password = self.decode_message(data)
                if message_type == 16:
                    if self.verify_password(password):
                        client_id = self.assign_id()
                        with self.lock:
                            self.clients[client_id] = client
                        assign_id_message = self.encode_message(1, client_id)
                        client.send(assign_id_message)
                    else:
                        error_message = self.encode_message(7, "Incorrect password, please restart the client and try again")
                        client.send(error_message)                
                if not data:
                    break
                message_type, payload = self.decode_message(data)
                if message_type == 2:  
                    self.send_opponent_list(client_id)
                if message_type == 4:  
                    opponent_id, word = payload.split(';')
                    self.create_match(client_id, opponent_id, word)
                if message_type == 9:  
                    opponent_id, response = payload.split(';')
                    self.handle_match_response(opponent_id, client_id, response)
                elif message_type == 11:
                    self.handle_guess(client_id, payload)
                elif message_type == 14:
                    self.handle_hint(client_id, payload)
            except:
                break

        with self.lock:
            del self.clients[client_id]
            client.close()

    
    def handle_hint(self, client_id, hint):
        opponent_id = None
        for match_id, match_info in self.matches.items():
            if match_info['opponent'] == client_id or match_id == client_id:
                opponent_id = match_info['opponent'] if match_id == client_id else match_id
                break

        if opponent_id:
            hint_message = self.encode_message(14, hint)
            self.clients[opponent_id].send(hint_message)
        else:
            error_message = self.encode_message(7, "Not in a match to send a hint")
            self.clients[client_id].send(error_message)
    def handle_match_response(self, client_id, opponent_id, response):
        if opponent_id in self.matches and self.matches[opponent_id]['opponent'] == client_id:
            if response == 'accept':
                self.matches[opponent_id]['status'] = 'in progress'
                accept_message = self.encode_message(10, "Match accepted") 
                self.clients[client_id].send(accept_message)
                self.clients[opponent_id].send(accept_message)
            elif response == 'decline':
                decline_message = self.encode_message(11, "Match declined") 
                self.clients[client_id].send(decline_message)
                del self.matches[opponent_id]
            else:
                error_message = self.encode_message(7, "Invalid response")  
                self.clients[client_id].send(error_message)
        else:
            error_message = self.encode_message(7, "Match request not found or expired")
            self.clients[client_id].send(error_message)
    def handle_guess(self, client_id, guess):
        if client_id in self.matches:
            match = self.matches[client_id]
            opponent = match['opponent']
            word = match['word']

            if guess.lower() == word.lower():
                success_message = self.encode_message(12, "Correct;"+guess)
                self.clients[client_id].send(success_message)
                self.clients[opponent].send(success_message)
                del self.matches[client_id]  # End the game
            else:
                try_message = self.encode_message(13, "Incorrect;"+guess)
                self.clients[client_id].send(try_message)
                self.clients[opponent].send(try_message)
        else:
            error_message = self.encode_message(7, "Not in a match")
            self.clients[client_id].send(error_message)
    def send_opponent_list(self, client_id):
        opponents = [id for id in self.clients if id != client_id]
        opponent_list = ','.join(opponents)  
        response = self.encode_message(8, opponent_list)
        self.clients[client_id].send(response)
    def create_match(self, client_id, opponent_id, word):
        if opponent_id in self.clients and opponent_id not in self.matches:
            self.matches[opponent_id] = {'opponent': client_id, 'word': word, 'status': 'pending'}
            match_request_payload = f"{client_id};{word}"
            match_request = self.encode_message(5, match_request_payload)
            self.clients[opponent_id].send(match_request)
            request_sent_message = self.encode_message(6, "Match request sent")
            self.clients[client_id].send(request_sent_message)
        else:
            error_message = self.encode_message(7, "Opponent not available or busy")
            self.clients[client_id].send(error_message)

if __name__ == "__main__":
    server = GuessWordServer('localhost', 12345, 12346, '/tmp/guessword.sock')
    server.start()
