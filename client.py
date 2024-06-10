import socket

# Connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client.connect(("192.168.0.152", 9999))
client.connect(("127.0.0.1", 9999))

while True:
    try:
        # Receive and print the current game state
        message = client.recv(1024).decode()
        print(message)
        
        # If the game is over, break the loop
        if "Game over!" in message or "wins!" in message:
            break
        
        # If prompted to start, get user input
        if "Type 'start' to begin the game." in message:
            cmd = input().strip().lower()
            client.send(cmd.encode())

        # If prompted to enter a word, get user input
        elif "Enter a word" in message:
            word = input().strip().lower()
            client.send(word.encode())

        # If prompted to enter a guess, get user input
        elif "Enter your guess" in message:
            guess = input().strip().lower()
            client.send(guess.encode())
    except:
        break

client.close()
