import socket
import threading

# Global game state
display_word = []  # List to store the current state of the guessed word
guessed_letters = set()  # Set to store guessed letters
attempts_left = 6  # Number of attempts left
clients = {}  # Dictionary to store connected clients
word = ""  # The word to be guessed
lock = threading.Lock()  # Lock to ensure thread safety

def initialize_game():
    """Function to initialize the game state."""
    global display_word, guessed_letters, attempts_left
    display_word = ["_" for _ in word]  # Initialize display word with underscores
    guessed_letters = set()  # Reset guessed letters
    attempts_left = 6  # Reset attempts left

def handle_client(client_socket, player):
    """Function to handle a client connection."""
    global attempts_left, word
    try:
        if player == 'Player1':
            client_socket.send(f"You are {player}. Type 'start' to begin the game.\n".encode())
            
            while True:
                start_cmd = client_socket.recv(1024).decode().strip().lower()
                if start_cmd == 'start':
                    with lock:
                        if len(clients) == 2:  # Ensure both players are connected
                            client_socket.send("Enter a word for Player2 to guess: ".encode())
                            word = client_socket.recv(1024).decode().strip().lower()
                            initialize_game()  # Initialize game state
                            notify_clients(f"Player1 has set the word. Player2's turn to guess.")
                            break
                        else:
                            client_socket.send("Waiting for Player2 to join...\n".encode())
                elif start_cmd == 'quit':
                    client_socket.send("You have quit the game.".encode())
                    break
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
                if guess == 'quit':
                    client_socket.send("You have quit the game.".encode())
                    break
                if guess == 'reset':
                    notify_clients("reset")
                    reset_game()
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
                        if "_" not in display_word:  # Check if the word is fully guessed
                            notify_clients(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}", include_player2=True)
                            notify_clients(f"The word was: {word}. Player2 wins!", include_player2=True)
                            game_end_message(client_socket)
                            break
                    else:
                        attempts_left -= 1
                        if attempts_left == 0:  # Check if no attempts left
                            notify_clients(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}", include_player2=True)
                            notify_clients(f"No attempts left. The word was: {word}. Player1 wins!", include_player2=True)
                            game_end_message(client_socket)
                            break

                    notify_clients(f"Word: {' '.join(display_word)} | Attempts left: {attempts_left} | Guessed letters: {', '.join(guessed_letters)}")
    except:
        pass
    finally:
        client_socket.close()
        with lock:
            if player in clients:
                del clients[player]  # Remove client from clients dictionary
            if len(clients) < 2:
                notify_clients("Player disconnected. Resetting the game.")
                reset_game()

def notify_clients(message, include_player2=False):
    """Function to notify all clients with a message."""
    for player, client in clients.items():
        client.send((message + "\n").encode())

def game_end_message(client_socket):
    """Function to send end game message and wait for reset or quit."""
    client_socket.send("Game over! Type 'reset' to play again or 'quit' to exit.\n".encode())

def reset_game():
    """Function to reset the game state."""
    global display_word, guessed_letters, attempts_left, word
    display_word = []
    guessed_letters = set()
    attempts_left = 6
    word = ""
    notify_clients("The game has been reset. Player1, type 'start' to begin the game.")

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 9999))  # Bind to all available interfaces on port 9999
server.listen(2)  # Listen for up to 2 clients

print("Server listening on port 9999")

# Accept connections from clients
player_count = 1
while player_count <= 2:
    client_socket, addr = server.accept()  # Accept a client connection
    player = f'Player{player_count}'
    print(f"Accepted connection from {addr} as {player}")
    clients[player] = client_socket  # Add client to clients dictionary
    client_thread = threading.Thread(target=handle_client, args=(client_socket, player))
    client_thread.start()  # Start a new thread to handle the client
    player_count += 1

# Wait for all threads to finish
for client_thread in threading.enumerate():
    if client_thread is not threading.main_thread():
        client_thread.join()

