# Import necessary modules for networking, threading, and GUI creation
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, PhotoImage

class HangmanClient:
    def __init__(self, master):
        # Initialize the main window
        self.master = master
        self.master.title("Hangman Client")
        self.master.geometry("500x600")
        self.master.config(bg="#2C3E50")

        # Load hangman stages images (0.png to 6.png)
        self.hangman_stages = [PhotoImage(file=f"{i}.png") for i in range(7)]
        self.current_stage = 0  # Start at the initial stage

        # Set up GUI elements

        # Label to display the banner at the top
        self.banner_label = tk.Label(self.master, bg="#2C3E50", font=("Helvetica", 24, "bold"))
        self.banner_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")

        # Label to display the hangman image
        self.image_label = tk.Label(self.master, bg="#2C3E50")
        self.image_label.grid(row=1, column=0, columnspan=3, pady=20, sticky="nsew")
        self.update_hangman_image()  # Display the initial hangman image

        # Label to display connection status or game messages
        self.message_label = tk.Label(self.master, text="Connecting to the server...", fg="white", bg="#2C3E50", font=("Helvetica", 14))
        self.message_label.grid(row=2, column=0, columnspan=3, pady=10, sticky="nsew")

        # Label to display the word to guess
        self.word_label = tk.Label(self.master, text="Word: ", fg="white", bg="#2C3E50", font=("Helvetica", 16))
        self.word_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="nsew")

        # Label to display guessed letters
        self.guess_label = tk.Label(self.master, text="Guessed Letters: ", fg="white", bg="#2C3E50", font=("Helvetica", 14))
        self.guess_label.grid(row=4, column=0, columnspan=3, pady=5, sticky="nsew")

        # Label to display remaining attempts
        self.attempts_label = tk.Label(self.master, text="Attempts Left: ", fg="#E74C3C", bg="#2C3E50", font=("Helvetica", 14, "bold"))
        self.attempts_label.grid(row=5, column=0, columnspan=3, pady=5, sticky="nsew")

        # Entry widget for user input
        self.entry = tk.Entry(self.master, font=("Helvetica", 14))
        self.entry.grid(row=6, column=0, columnspan=2, padx=10, pady=20, sticky="nsew")

        # Button to send user input
        self.send_button = tk.Button(self.master, text="Send", command=self.send_input, bg="#3498DB", fg="white", font=("Helvetica", 12, "bold"))
        self.send_button.grid(row=6, column=2, padx=10, sticky="nsew")

        # Button to reset the game
        self.reset_button = tk.Button(self.master, text="Reset", command=self.reset_game, bg="#27AE60", fg="white", font=("Helvetica", 12, "bold"))
        self.reset_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="nsew")

        # Button to quit the game
        self.quit_button = tk.Button(self.master, text="Quit", command=self.quit_game, bg="#E74C3C", fg="white", font=("Helvetica", 12, "bold"))
        self.quit_button.grid(row=7, column=2, pady=10, sticky="nsew")

        # Create a client socket to connect to the server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("127.0.0.1", 9999))  # Connect to the local server at port 9999

        self.input_mode = "start"  # Initial input mode

        # Start a thread to listen for messages from the server
        threading.Thread(target=self.receive_messages).start()

        # Configure grid to expand and adjust with window resizing
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)

    def send_input(self):
        # Get the text from the entry widget and send it to the server
        input_text = self.entry.get().strip().lower()
        self.entry.delete(0, tk.END)  # Clear the entry widget

        if input_text:  # If input is not empty
            self.client_socket.send(input_text.encode())  # Send input to the server
            # Update the message label based on the current input mode
            if self.input_mode == "start":
                self.message_label.config(text="Waiting for Player1 to set the word...")
            elif self.input_mode == "word":
                self.message_label.config(text="Waiting for Player2 to guess...")
            elif self.input_mode == "guess":
                self.message_label.config(text="Waiting for response...")

    def receive_messages(self):
        # Continuously listen for messages from the server
        while True:
            try:
                message = self.client_socket.recv(1024).decode()  # Receive and decode the message
                self.process_message(message)  # Process the received message
            except:
                # Update message label if disconnected from the server
                self.message_label.config(text="Disconnected from server.")
                break

    def process_message(self, message):
        # Process and handle the server's message
        print(message)  # Print the message to the console for debugging

        if "Type 'start' to begin the game." in message:
            # If message prompts to start the game
            self.input_mode = "start"
            self.message_label.config(text=message)
            self.banner_label.config(text="", bg="#2C3E50")
        elif "Enter a word" in message:
            # If message prompts to enter a word
            self.input_mode = "word"
            self.message_label.config(text=message)
        elif "Enter your guess" in message:
            # If message prompts to enter a guess
            self.input_mode = "guess"
            self.message_label.config(text=message)
        elif message.strip() == "reset":
            # If message indicates a reset
            self.reset_game_state()
        else:
            # If message contains game state updates
            if "Word: " in message and "Attempts left: " in message:
                parts = message.split("|")
                word = parts[0].split(":")[1].strip()
                attempts = int(parts[1].split(":")[1].strip())
                guessed_letters = parts[2].split(":")[1].strip()

                self.word_label.config(text=f"Word: {word}")
                self.attempts_label.config(text=f"Attempts Left: {attempts}")
                self.guess_label.config(text=f"Guessed Letters: {guessed_letters}")
                self.update_hangman_image(attempts)  # Update hangman image based on attempts left

            if "wins!" in message or "Game over!" in message:
                # If game ends (win or lose)
                self.message_label.config(text=message)
                self.entry.config(state=tk.DISABLED)  # Disable entry widget
                self.send_button.config(state=tk.DISABLED)  # Disable send button
                self.display_end_game_banner(message)  # Display end game banner
            else:
                # Otherwise, just update the message label
                self.message_label.config(text=message)

    def update_hangman_image(self, attempts=0):
        # Update hangman image based on remaining attempts
        self.current_stage = 6 - attempts  # Assuming 6 attempts max
        self.image_label.config(image=self.hangman_stages[self.current_stage])

    def display_end_game_banner(self, message):
        # Display end game banner based on the message
        if "wins!" in message:
            self.banner_label.config(text="YOU'VE WON!", bg="green", fg="white")
        else:
            self.banner_label.config(text="GAME OVER!", bg="red", fg="white")

    def reset_game(self):
        # Send reset command to the server
        self.client_socket.send("reset".encode())

    def reset_game_state(self):
        # Reset game state to initial conditions
        self.entry.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.message_label.config(text="The game has been reset. Player1, type 'start' to begin the game.")
        self.word_label.config(text="Word: ")
        self.attempts_label.config(text="Attempts Left: ")
        self.guess_label.config(text="Guessed Letters: ")
        self.update_hangman_image(6)
        self.banner_label.config(text="", bg="#2C3E50")

    def quit_game(self):
        # Send quit command to the server and close the application
        self.client_socket.send("quit".encode())
        self.client_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    # Create the main window and start the application
    root = tk.Tk()
    app = HangmanClient(root)
    root.mainloop()
