# GuessWord Game

## Instructions

### Setting Up the Server (`server.py`)

1. **Initial Setup**:
   - Ensure you have Python installed on your server machine.
   - Place the `server.py` script in a suitable directory.

2. **Running the Server**:
   - Open a terminal or command prompt.
   - Navigate to the directory containing `server.py`.
   - Run the script by typing `python server.py`.
   - The server will start and listen for client connections.

3. **Server Configuration**:
   - The server binds to `localhost` and listens on two ports: a TCP port and a Unix socket path.
   - These are set in the `GuessWordServer` class's `__init__` method. Modify them if needed.

### Connecting with the Client (`client.py`)

1. **Client Setup**:
   - Ensure Python is installed on the client machine.
   - Place the `client.py` script in a directory on the client machine.

2. **Starting the Client**:
   - Open a terminal or command prompt on the client machine.
   - Navigate to the directory with `client.py`.
   - Run the script by typing `python client.py`.

3. **Client Connection**:
   - Upon starting, the client will attempt to connect to the server.
   - Choose between connecting via Unix socket or TCP by entering `yes` or `no`.
   - Enter the password when prompted.

4. **Playing the Game**:
   - After connecting, you can choose to create a game lobby or wait for an invitation to join a game.
   - If creating a game, you will be prompted to choose an opponent from the listed opponents and set a word for them to guess.
   - If waiting for an invitation, you will be notified when someone invites you to play.

5. **In-Game Actions**:
   - If you are setting the word (game creator), you can send hints to your opponent.
   - If you are guessing the word, type your guesses.
   - You can quit the game at any time by typing `quit`.

6. **Ending the Game**:
   - The game ends either when the word is guessed correctly or when a player quits.
   - After the game ends, you can reconnect to the server to start a new game.

### Notes:

- Ensure the server is running before clients attempt to connect.
- The password for connecting to the server is set in the `verify_password` method of `server.py`. Change it as needed.
- The game uses a custom binary protocol for communication. Make sure both server and client scripts are compatible.
- The game supports multiple clients simultaneously.

Enjoy your GuessWord game!
