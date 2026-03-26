# Chess Game

Browser (web) and terminal chess game with online multiplayer support.

## Features

### Web Version (Node.js)
- Play in browser with mouse
- WebSocket-based real-time multiplayer
- Drag & click to move pieces
- Legal move highlighting

### Terminal Version (Python)
- Keyboard-only play (`e2 e4` format)
- ASCII pieces with ANSI color board (works on any terminal)
- AI opponent (Minimax + Alpha-Beta pruning, 3 difficulty levels)
- **Network play** — TCP socket multiplayer between remote servers

### Chess Engine
- Full rules: castling, en passant, promotion
- Check / checkmate / stalemate detection
- Legal move validation (pins, check escape auto-handled)

---

## Quick Start

### Requirements

- **Web version**: Node.js 18+
- **Terminal version**: Python 3.8+ (no packages needed)

### Install

```bash
git clone https://github.com/<your-username>/chess.git
cd chess
```

### Web Version

```bash
npm install
node server.js
```

Open `http://localhost:3000` in 2 browser tabs.

### Terminal Version

```bash
python3 terminal_chess.py
```

Menu:
```
    +--------------------------------------------------+
    |             TERMINAL CHESS                        |
    +--------------------------------------------------+
    |                                                  |
    |   1.  Human vs Human  (local)                    |
    |   2.  Human vs AI     (easy,   depth=2)          |
    |   3.  Human vs AI     (normal, depth=3)          |
    |   4.  Human vs AI     (hard,   depth=4)          |
    |   5.  Network game    (host / server)             |
    |   6.  Network game    (join / client)             |
    |   q.  Quit                                       |
    |                                                  |
    +--------------------------------------------------+
```

Board display:
```
         a        b        c        d        e        f        g        h

    +--------+--------+--------+--------+--------+--------+--------+--------+
  8 |   r    |   n    |   b    |   q    |   k    |   b    |   n    |   r    | 8
    +--------+--------+--------+--------+--------+--------+--------+--------+
  7 |   p    |   p    |   p    |   p    |   p    |   p    |   p    |   p    | 7
    +--------+--------+--------+--------+--------+--------+--------+--------+
  6 |        |        |        |        |        |        |        |        | 6
    +--------+--------+--------+--------+--------+--------+--------+--------+
  5 |        |        |        |        |        |        |        |        | 5
    +--------+--------+--------+--------+--------+--------+--------+--------+
  4 |        |        |        |        |        |        |        |        | 4
    +--------+--------+--------+--------+--------+--------+--------+--------+
  3 |        |        |        |        |        |        |        |        | 3
    +--------+--------+--------+--------+--------+--------+--------+--------+
  2 |   P    |   P    |   P    |   P    |   P    |   P    |   P    |   P    | 2
    +--------+--------+--------+--------+--------+--------+--------+--------+
  1 |   R    |   N    |   B    |   Q    |   K    |   B    |   N    |   R    | 1
    +--------+--------+--------+--------+--------+--------+--------+--------+
         a        b        c        d        e        f        g        h

    White = UPPERCASE (K Q R B N P)
    Black = lowercase (k q r b n p)
```

---

## Network Play (Linux Server vs Server)

Play chess between two Linux servers over SSH terminals.

### Architecture

```
  Server A (host, white)             Server B (client, black)
  +--------------------+             +--------------------+
  |  $ python3         |    TCP/IP   |  $ python3         |
  |  terminal_chess.py |<----------->|  terminal_chess.py |
  |  --host 0.0.0.0    |   port 5555 |  --connect <IP>    |
  +--------------------+             +--------------------+
```

### Install (both servers)

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/chess.git
cd chess

# Only Python3 required (no pip install needed)
python3 --version   # 3.8 or higher
```

### Server A (host)

```bash
python3 terminal_chess.py --host 0.0.0.0 --port 5555 --name "Alice"
```

Output:
```
    +----------------------------------------------------------+
    |  SERVER MODE - Waiting for opponent...                    |
    +----------------------------------------------------------+
    |                                                          |
    |  Opponent should run:                                    |
    |                                                          |
    |  python3 terminal_chess.py --connect 10.0.1.5            |
    |          --port 5555                                     |
    |                                                          |
    |  (Ctrl+C to cancel)                                      |
    +----------------------------------------------------------+
```

### Server B (client)

```bash
python3 terminal_chess.py --connect <Server-A-IP> --port 5555 --name "Bob"
```

Once connected, both terminals show the chess board and the game begins!

### Firewall Setup

Open the port on Server A:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5555/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --add-port=5555/tcp --permanent
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 5555 -j ACCEPT
```

### Blocked Port? — SSH Tunnel

If you can't open firewall ports, use an SSH tunnel:

```bash
# On Server B: tunnel Server A's port 5555 to localhost
ssh -L 5555:localhost:5555 user@ServerA_IP

# In another terminal, connect via localhost
python3 terminal_chess.py --connect localhost --port 5555 --name "Bob"
```

---

## How to Move Pieces

### No piece name needed!

Just type **from-square** and **to-square**. The engine automatically knows
what piece is on that square and whether the move is legal.

```
  [WHITE] > e2 e4

  What happens internally:
  1. Engine looks at e2 → finds white Pawn
  2. Calculates all legal moves for that Pawn → [e3, e4]
  3. Checks if e4 is in the list → YES
  4. Moves the Pawn from e2 to e4
```

### Input formats

```
  e2 e4         space-separated (recommended)
  e2e4          no space also works
  E2 E4         case-insensitive
```

### Select a piece first (optional)

Type just one square to see where that piece can go:

```
  [WHITE] > e2

  Output:
  Selected e2 -> can go: e3, e4
  (legal move squares are highlighted on the board)

  Then type the full move:
  [WHITE] > e2 e4
```

### Special moves

```
  Castling:     e1 g1         king-side  (king moves 2 squares right)
                e1 c1         queen-side (king moves 2 squares left)
                (just move the king — the rook moves automatically)

  En passant:   d5 c6         just move the pawn diagonally
                (the captured pawn is removed automatically)

  Promotion:    e7 e8         engine asks which piece you want
                e7e8q         or append: q=Queen r=Rook b=Bishop n=Knight
```

### Why piece names are not needed

```
  Traditional chess notation:    Terminal chess input:
  Nf3  (Knight to f3)           g1 f3  (from g1 to f3)
  Bxe5 (Bishop captures e5)     c3 e5  (from c3 to e5)
  O-O  (King-side castle)       e1 g1  (king from e1 to g1)

  In traditional notation, you name the piece because a written
  scoresheet doesn't show the board. But in terminal chess, the
  engine can see the board — it knows g1 has a Knight!
```

### Commands

```
  help          show help screen
  resign / gg   give up
  quit / q      exit game
```

---

## Project Structure

```
chess/
├── server.js            # Web server (Node.js + WebSocket)
├── public/
│   └── index.html       # Web client
├── terminal_chess.py    # Terminal version (Python, single file)
├── package.json         # Node.js dependencies
└── README.md
```

## Tech Stack

| Component | Web Version | Terminal Version |
|-----------|-------------|-----------------|
| Language | JavaScript | Python 3 |
| Server | Express + ws | Socket (stdlib) |
| Protocol | WebSocket | TCP Socket |
| UI | HTML/CSS/Canvas | ANSI Terminal |
| AI | — | Minimax + Alpha-Beta |
| Dependencies | express, ws | None |

## License

MIT
