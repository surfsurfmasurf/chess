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

## Controls

```
  Move:       e2 e4     (from to, space separated)
              e2e4      (no space also works)

  Select:     e2        (highlight legal moves)

  Promotion:  e7e8q     (q=queen, r=rook, b=bishop, n=knight)

  Castling:   e1 g1     (king-side)
              e1 c1     (queen-side)

  Commands:   help      show help
              resign    give up
              quit      exit game
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
