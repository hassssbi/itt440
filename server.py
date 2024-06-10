import socket
import threading

# Global game state
display_word = []
guessed_letters = set()
attempts_left = 6
clients = {}
word = ""
lock = threading.Lock()  # Lock to ensure thread safety

def initialize_game():
    """Function to initialize the game state."""
    global display_word, guessed_letters, attempts_left
    display_word = ["_" for _ in word]
    guessed_letters = set()
    attempts_left = 6

def handle_client(client_socket, player):
    global attempts_left, word
    if player == 'Player1':
        client_socket.send(f"You are {player}. Type 'start' to begin the game.\n".encode())
        
        while True:
            start_cmd = client_socket.recv(1024).decode().strip().lower()
            if start_cmd == 'start':
                with lock:
                    if len(clients) == 2:
                        client_socket.send("Enter a word for Player2 to guess: ".encode())
                        word = client_socket.recv(1024).decode().strip().lower()
                        initialize_game()
                        notify_clients(f"Player1 has set the word. Player2's turn to guess.")
                        break
                    else:
                        client_socket.send("Waiting for Player2 to join...\n".encode())
            else:
                client_socket.send("Type 'start' to begin the game.\n".encode())
    else:
        client_socket.send("You are Player2. Waiting for Player1 to set the word...\n".encode())
    
    while True:
        if player == 'Player2':
            client_socket.send(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}\nEnter your guess: ".encode())
            
            guess = client_socket.recv(1024).decode().strip().lower()
            if not guess:
                continue

            with lock:
                if guess in guessed_letters:
                    client_socket.send("You already guessed that letter. Try again.\n".encode())
                    continue
                
                guessed_letters.add(guess)
                if guess in word:
                    for i, letter in enumerate(word):
                        if letter == guess:
                            display_word[i] = guess
                    if "_" not in display_word:
                        notify_clients(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}", include_player2=True)
                        notify_clients(f"The word was: {word}. Player2 wins!", include_player2=True)
                        break
                else:
                    attempts_left -= 1
                    if attempts_left == 0:
                        notify_clients(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}", include_player2=True)
                        notify_clients(f"No attempts left. The word was: {word}. Player1 wins!", include_player2=True)
                        break

                notify_clients(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}")
    
    client_socket.close()

def notify_clients(message, include_player2=False):
    """Function to notify all clients with a message."""
    for player, client in clients.items():
        client.send((message + "\n").encode())

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 9999))
server.listen(2)  # Listen for up to 2 clients

print("Server listening on port 9999")

# Accept connections from clients
player_count = 1
while player_count <= 2:
    client_socket, addr = server.accept()
    player = f'Player{player_count}'
    print(f"Accepted connection from {addr} as {player}")
    clients[player] = client_socket
    client_thread = threading.Thread(target=handle_client, args=(client_socket, player))
    client_thread.start()
    player_count += 1

# Wait for all threads to finish
for client_thread in threading.enumerate():
    if client_thread is not threading.main_thread():
        client_thread.join()
