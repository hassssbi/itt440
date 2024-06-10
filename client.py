# import socket

# # Connect to the server
# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # client.connect(("192.168.0.152", 9999))
# client.connect(("127.0.0.1", 9999))

# while True:
#     try:
#         # Receive and print the current game state
#         message = client.recv(1024).decode()
#         print(message)
        
#         # If the game is over, break the loop
#         if "Game over!" in message or "wins!" in message:
#             break
        
#         # If prompted to start, get user input
#         if "Type 'start' to begin the game." in message:
#             cmd = input().strip().lower()
#             client.send(cmd.encode())

#         # If prompted to enter a word, get user input
#         elif "Enter a word" in message:
#             word = input().strip().lower()
#             client.send(word.encode())

#         # If prompted to enter a guess, get user input
#         elif "Enter your guess" in message:
#             guess = input().strip().lower()
#             client.send(guess.encode())
#     except:
#         break

# client.close()


import socket
import threading
import tkinter as tk
from tkinter import simpledialog

class HangmanClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Hangman Client")
        self.master.geometry("400x300")
        
        self.message_label = tk.Label(self.master, text="Connecting to the server...")
        self.message_label.pack(pady=10)
        
        self.word_label = tk.Label(self.master, text="Word: ")
        self.word_label.pack(pady=10)
        
        self.guess_label = tk.Label(self.master, text="Guessed Letters: ")
        self.guess_label.pack(pady=10)
        
        self.attempts_label = tk.Label(self.master, text="Attempts Left: ")
        self.attempts_label.pack(pady=10)
        
        self.entry = tk.Entry(self.master)
        self.entry.pack(pady=10)
        
        self.send_button = tk.Button(self.master, text="Send", command=self.send_input)
        self.send_button.pack(pady=10)
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("127.0.0.1", 9999))
        
        self.input_mode = "start"
        
        threading.Thread(target=self.receive_messages).start()

    def send_input(self):
        input_text = self.entry.get().strip().lower()
        self.entry.delete(0, tk.END)
        
        if input_text:
            self.client_socket.send(input_text.encode())
            if self.input_mode == "start":
                self.message_label.config(text="Waiting for Player1 to set the word...")
            elif self.input_mode == "word":
                self.message_label.config(text="Waiting for Player2 to guess...")
            elif self.input_mode == "guess":
                self.message_label.config(text="Waiting for response...")
                
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                self.process_message(message)
            except:
                self.message_label.config(text="Disconnected from server.")
                break

    def process_message(self, message):
        if "Type 'start' to begin the game." in message:
            self.input_mode = "start"
            self.message_label.config(text=message)
        elif "Enter a word" in message:
            self.input_mode = "word"
            self.message_label.config(text=message)
        elif "Enter your guess" in message:
            self.input_mode = "guess"
            self.message_label.config(text=message)
        else:
            if "Word: " in message and "Attempts left: " in message:
                parts = message.split("|")
                word = parts[0].split(":")[1].strip()
                attempts = parts[1].split(":")[1].strip()
                guessed_letters = parts[2].split(":")[1].strip()
                
                self.word_label.config(text=f"Word: {word}")
                self.attempts_label.config(text=f"Attempts Left: {attempts}")
                self.guess_label.config(text=f"Guessed Letters: {guessed_letters}")
                
            if "wins!" in message or "Game over!" in message:
                self.message_label.config(text=message)
                self.entry.config(state=tk.DISABLED)
                self.send_button.config(state=tk.DISABLED)
            else:
                self.message_label.config(text=message)

if __name__ == "__main__":
    root = tk.Tk()
    app = HangmanClient(root)
    root.mainloop()
