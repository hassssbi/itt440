import socket
import threading
import tkinter as tk
from tkinter import simpledialog, PhotoImage
import pygame  # Importing pygame for sound effects

class HangmanClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Hangman Client")
        self.master.geometry("500x600")
        self.master.config(bg="#2C3E50")

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load sound effects
        self.correct_sound = pygame.mixer.Sound("correct.wav")
        self.incorrect_sound = pygame.mixer.Sound("incorrect.wav")
        self.bg_music = pygame.mixer.Sound("background_music.mp3")

        # Play background music
        self.bg_music.play(-1)  # Loop indefinitely

        self.hangman_stages = [PhotoImage(file=f"{i}.png") for i in range(7)]
        self.current_stage = 0

        self.banner_label = tk.Label(self.master, bg="#2C3E50", font=("Helvetica", 24, "bold"))
        self.banner_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")

        self.image_label = tk.Label(self.master, bg="#2C3E50")
        self.image_label.grid(row=1, column=0, columnspan=3, pady=20, sticky="nsew")
        self.update_hangman_image()

        self.message_label = tk.Label(self.master, text="Connecting to the server...", fg="white", bg="#2C3E50", font=("Helvetica", 14))
        self.message_label.grid(row=2, column=0, columnspan=3, pady=10, sticky="nsew")

        self.word_label = tk.Label(self.master, text="Word: ", fg="white", bg="#2C3E50", font=("Helvetica", 16))
        self.word_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="nsew")

        self.guess_label = tk.Label(self.master, text="Guessed Letters: ", fg="white", bg="#2C3E50", font=("Helvetica", 14))
        self.guess_label.grid(row=4, column=0, columnspan=3, pady=5, sticky="nsew")

        self.attempts_label = tk.Label(self.master, text="Attempts Left: ", fg="#E74C3C", bg="#2C3E50", font=("Helvetica", 14, "bold"))
        self.attempts_label.grid(row=5, column=0, columnspan=3, pady=5, sticky="nsew")

        self.entry = tk.Entry(self.master, font=("Helvetica", 14))
        self.entry.grid(row=6, column=0, columnspan=2, padx=10, pady=20, sticky="nsew")

        self.send_button = tk.Button(self.master, text="Send", command=self.send_input, bg="#3498DB", fg="white", font=("Helvetica", 12, "bold"))
        self.send_button.grid(row=6, column=2, padx=10, sticky="nsew")

        self.reset_button = tk.Button(self.master, text="Reset", command=self.reset_game, bg="#27AE60", fg="white", font=("Helvetica", 12, "bold"))
        self.reset_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="nsew")

        self.quit_button = tk.Button(self.master, text="Quit", command=self.quit_game, bg="#E74C3C", fg="white", font=("Helvetica", 12, "bold"))
        self.quit_button.grid(row=7, column=2, pady=10, sticky="nsew")

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("127.0.0.1", 9999))

        self.input_mode = "start"

        threading.Thread(target=self.receive_messages).start()

        # Configure grid to expand
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)

    def send_input(self):
        input_text = self.entry.get().strip().lower()
        self.entry.delete(0, tk.END)

        if input_text:
            if self.input_mode == "guess":
                if len(input_text) == 1 and input_text.isalpha():
                    self.client_socket.send(input_text.encode())
                    self.entry.config(state=tk.DISABLED)
                    self.send_button.config(state=tk.DISABLED)
                else:
                    self.message_label.config(text="Please enter only one alphabet.")
            else:
                self.client_socket.send(input_text.encode())
                self.entry.config(state=tk.DISABLED)
                self.send_button.config(state=tk.DISABLED)

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                self.process_message(message)
            except:
                self.message_label.config(text="Disconnected from server.")
                break

    def process_message(self, message):
        print(message)
        if "Type 'start' to begin the game." in message:
            self.input_mode = "start"
            self.message_label.config(text=message)
            self.banner_label.config(text="", bg="#2C3E50")
            self.entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
        elif "Enter a word" in message:
            self.input_mode = "word"
            self.message_label.config(text=message)
            self.entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
        elif "Enter your guess" in message:
            self.input_mode = "guess"
            self.message_label.config(text=message)
            self.entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
        elif message.strip() == "reset":
            self.reset_game_state()
        else:
            if "Word: " in message and "Attempts left: " in message:
                parts = message.split("|")
                word = parts[0].split(":")[1].strip()
                attempts = int(parts[1].split(":")[1].strip())
                guessed_letters = parts[2].split(":")[1].strip()

                self.word_label.config(text=f"Word: {word}")
                self.attempts_label.config(text=f"Attempts Left: {attempts}")
                self.guess_label.config(text=f"Guessed Letters: {guessed_letters}")
                self.update_hangman_image(attempts)

                if attempts < 6:
                    self.incorrect_sound.play()

            if "wins!" in message or "Game over!" in message:
                self.message_label.config(text=message)
                self.entry.config(state=tk.DISABLED)
                self.send_button.config(state=tk.DISABLED)
                self.display_end_game_banner(message)
                if "wins!" in message:
                    self.correct_sound.play()
            else:
                self.message_label.config(text=message)
                self.entry.config(state=tk.NORMAL)
                self.send_button.config(state=tk.NORMAL)

    def update_hangman_image(self, attempts=0):
        self.current_stage = 6 - attempts  # Assuming 6 attempts max
        self.image_label.config(image=self.hangman_stages[self.current_stage])

    def display_end_game_banner(self, message):
        if "wins!" in message:
            self.banner_label.config(text="YOU'VE WON!", bg="green", fg="white")
        else:
            self.banner_label.config(text="GAME OVER!", bg="red", fg="white")

    def reset_game(self):
        self.client_socket.send("reset".encode())

    def reset_game_state(self):
        self.entry.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.message_label.config(text="The game has been reset. Player1, type 'start' to begin the game.")
        self.word_label.config(text="Word: ")
        self.attempts_label.config(text="Attempts Left: ")
        self.guess_label.config(text="Guessed Letters: ")
        self.update_hangman_image(6)
        self.banner_label.config(text="", bg="#2C3E50")

    def quit_game(self):
        self.client_socket.send("quit".encode())
        self.client_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HangmanClient(root)
    root.mainloop()
