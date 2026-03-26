const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

app.use(express.static(path.join(__dirname, 'public')));

// Game state management
const games = new Map();
let waitingPlayer = null;

function createGame(white, black) {
  const gameId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const game = {
    id: gameId,
    white,
    black,
    board: createInitialBoard(),
    turn: 'white',
    moves: [],
    enPassantTarget: null,
    castlingRights: {
      white: { kingSide: true, queenSide: true },
      black: { kingSide: true, queenSide: true },
    },
    kings: { white: { row: 7, col: 4 }, black: { row: 0, col: 4 } },
    status: 'playing', // playing, check, checkmate, stalemate, draw
  };
  games.set(gameId, game);
  return game;
}

function createInitialBoard() {
  const board = Array(8).fill(null).map(() => Array(8).fill(null));
  const backRank = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook'];
  for (let col = 0; col < 8; col++) {
    board[0][col] = { type: backRank[col], color: 'black' };
    board[1][col] = { type: 'pawn', color: 'black' };
    board[6][col] = { type: 'pawn', color: 'white' };
    board[7][col] = { type: backRank[col], color: 'white' };
  }
  return board;
}

function cloneBoard(board) {
  return board.map(row => row.map(cell => cell ? { ...cell } : null));
}

function isInBounds(r, c) {
  return r >= 0 && r < 8 && c >= 0 && c < 8;
}

function getPseudoLegalMoves(board, row, col, enPassantTarget, castlingRights) {
  const piece = board[row][col];
  if (!piece) return [];
  const moves = [];
  const { type, color } = piece;
  const dir = color === 'white' ? -1 : 1;

  const addIfValid = (r, c, special) => {
    if (!isInBounds(r, c)) return false;
    const target = board[r][c];
    if (target && target.color === color) return false;
    moves.push({ from: { row, col }, to: { row: r, col: c }, capture: !!target, special });
    return !target; // return true if square was empty (for sliding pieces)
  };

  if (type === 'pawn') {
    // Forward
    if (!board[row + dir]?.[col]) {
      moves.push({ from: { row, col }, to: { row: row + dir, col }, capture: false });
      // Double push
      const startRow = color === 'white' ? 6 : 1;
      if (row === startRow && !board[row + 2 * dir][col]) {
        moves.push({ from: { row, col }, to: { row: row + 2 * dir, col }, capture: false, special: 'doublePush' });
      }
    }
    // Captures
    for (const dc of [-1, 1]) {
      const nr = row + dir, nc = col + dc;
      if (!isInBounds(nr, nc)) continue;
      if (board[nr][nc] && board[nr][nc].color !== color) {
        moves.push({ from: { row, col }, to: { row: nr, col: nc }, capture: true });
      }
      // En passant
      if (enPassantTarget && enPassantTarget.row === nr && enPassantTarget.col === nc) {
        moves.push({ from: { row, col }, to: { row: nr, col: nc }, capture: true, special: 'enPassant' });
      }
    }
  } else if (type === 'knight') {
    for (const [dr, dc] of [[-2,-1],[-2,1],[-1,-2],[-1,2],[1,-2],[1,2],[2,-1],[2,1]]) {
      addIfValid(row + dr, col + dc);
    }
  } else if (type === 'king') {
    for (const [dr, dc] of [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]) {
      addIfValid(row + dr, col + dc);
    }
    // Castling
    const rights = castlingRights[color];
    const homeRow = color === 'white' ? 7 : 0;
    if (row === homeRow && col === 4) {
      if (rights.kingSide && !board[homeRow][5] && !board[homeRow][6] && board[homeRow][7]?.type === 'rook') {
        moves.push({ from: { row, col }, to: { row: homeRow, col: 6 }, capture: false, special: 'castleKing' });
      }
      if (rights.queenSide && !board[homeRow][3] && !board[homeRow][2] && !board[homeRow][1] && board[homeRow][0]?.type === 'rook') {
        moves.push({ from: { row, col }, to: { row: homeRow, col: 2 }, capture: false, special: 'castleQueen' });
      }
    }
  } else {
    // Sliding pieces
    const directions = {
      bishop: [[-1,-1],[-1,1],[1,-1],[1,1]],
      rook: [[-1,0],[1,0],[0,-1],[0,1]],
      queen: [[-1,-1],[-1,1],[1,-1],[1,1],[-1,0],[1,0],[0,-1],[0,1]],
    };
    for (const [dr, dc] of directions[type]) {
      for (let i = 1; i < 8; i++) {
        if (!addIfValid(row + dr * i, col + dc * i)) break;
      }
    }
  }

  return moves;
}

function isSquareAttacked(board, row, col, byColor) {
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const p = board[r][c];
      if (!p || p.color !== byColor) continue;
      const moves = getPseudoLegalMoves(board, r, c, null, { white: { kingSide: false, queenSide: false }, black: { kingSide: false, queenSide: false } });
      if (moves.some(m => m.to.row === row && m.to.col === col)) return true;
    }
  }
  return false;
}

function findKing(board, color) {
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if (board[r][c]?.type === 'king' && board[r][c]?.color === color) return { row: r, col: c };
    }
  }
  return null;
}

function applyMove(board, move) {
  const newBoard = cloneBoard(board);
  const piece = { ...newBoard[move.from.row][move.from.col] };
  newBoard[move.from.row][move.from.col] = null;
  newBoard[move.to.row][move.to.col] = piece;

  if (move.special === 'enPassant') {
    const capturedRow = move.from.row;
    newBoard[capturedRow][move.to.col] = null;
  } else if (move.special === 'castleKing') {
    const r = move.to.row;
    newBoard[r][5] = newBoard[r][7];
    newBoard[r][7] = null;
  } else if (move.special === 'castleQueen') {
    const r = move.to.row;
    newBoard[r][3] = newBoard[r][0];
    newBoard[r][0] = null;
  }

  // Promotion
  if (piece.type === 'pawn' && (move.to.row === 0 || move.to.row === 7)) {
    newBoard[move.to.row][move.to.col] = { type: move.promotion || 'queen', color: piece.color };
  }

  return newBoard;
}

function getLegalMoves(game, row, col) {
  const piece = game.board[row][col];
  if (!piece) return [];
  const pseudoMoves = getPseudoLegalMoves(game.board, row, col, game.enPassantTarget, game.castlingRights);
  const enemy = piece.color === 'white' ? 'black' : 'white';

  return pseudoMoves.filter(move => {
    // For castling, check that king doesn't pass through or land on attacked square
    if (move.special === 'castleKing' || move.special === 'castleQueen') {
      const r = move.from.row;
      if (isSquareAttacked(game.board, r, 4, enemy)) return false; // king in check
      if (move.special === 'castleKing') {
        if (isSquareAttacked(game.board, r, 5, enemy)) return false;
        if (isSquareAttacked(game.board, r, 6, enemy)) return false;
      } else {
        if (isSquareAttacked(game.board, r, 3, enemy)) return false;
        if (isSquareAttacked(game.board, r, 2, enemy)) return false;
      }
    }

    const newBoard = applyMove(game.board, move);
    const king = findKing(newBoard, piece.color);
    return !isSquareAttacked(newBoard, king.row, king.col, enemy);
  });
}

function getAllLegalMoves(game, color) {
  const moves = [];
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if (game.board[r][c]?.color === color) {
        moves.push(...getLegalMoves(game, r, c));
      }
    }
  }
  return moves;
}

function makeMove(game, from, to, promotion) {
  const piece = game.board[from.row][from.col];
  if (!piece || piece.color !== game.turn) return { valid: false, reason: 'Not your piece' };

  const legalMoves = getLegalMoves(game, from.row, from.col);
  const move = legalMoves.find(m => m.to.row === to.row && m.to.col === to.col);
  if (!move) return { valid: false, reason: 'Illegal move' };

  // Handle promotion
  if (piece.type === 'pawn' && (to.row === 0 || to.row === 7)) {
    move.promotion = promotion || 'queen';
  }

  // Apply
  game.board = applyMove(game.board, move);

  // Update en passant target
  game.enPassantTarget = null;
  if (move.special === 'doublePush') {
    game.enPassantTarget = { row: (from.row + to.row) / 2, col: from.col };
  }

  // Update castling rights
  if (piece.type === 'king') {
    game.castlingRights[piece.color] = { kingSide: false, queenSide: false };
  }
  if (piece.type === 'rook') {
    const homeRow = piece.color === 'white' ? 7 : 0;
    if (from.row === homeRow && from.col === 0) game.castlingRights[piece.color].queenSide = false;
    if (from.row === homeRow && from.col === 7) game.castlingRights[piece.color].kingSide = false;
  }
  // If a rook is captured
  if (move.capture) {
    if (to.row === 0 && to.col === 0) game.castlingRights.black.queenSide = false;
    if (to.row === 0 && to.col === 7) game.castlingRights.black.kingSide = false;
    if (to.row === 7 && to.col === 0) game.castlingRights.white.queenSide = false;
    if (to.row === 7 && to.col === 7) game.castlingRights.white.kingSide = false;
  }

  // Switch turn
  const prevTurn = game.turn;
  game.turn = game.turn === 'white' ? 'black' : 'white';

  // Record move
  game.moves.push({ from, to, piece: piece.type, special: move.special, promotion: move.promotion });

  // Check game status
  const enemyMoves = getAllLegalMoves(game, game.turn);
  const enemyKing = findKing(game.board, game.turn);
  const inCheck = isSquareAttacked(game.board, enemyKing.row, enemyKing.col, prevTurn);

  if (enemyMoves.length === 0) {
    game.status = inCheck ? 'checkmate' : 'stalemate';
  } else {
    game.status = inCheck ? 'check' : 'playing';
  }

  return { valid: true, move, status: game.status };
}

function send(ws, data) {
  if (ws.readyState === ws.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

wss.on('connection', (ws) => {
  ws.isAlive = true;

  ws.on('message', (raw) => {
    let msg;
    try { msg = JSON.parse(raw); } catch { return; }

    if (msg.type === 'join') {
      ws.playerName = msg.name || 'Player';

      if (waitingPlayer && waitingPlayer.readyState === waitingPlayer.OPEN) {
        // Match found
        const game = createGame(waitingPlayer, ws);
        waitingPlayer.gameId = game.id;
        waitingPlayer.color = 'white';
        ws.gameId = game.id;
        ws.color = 'black';

        send(waitingPlayer, { type: 'gameStart', color: 'white', opponentName: ws.playerName, board: game.board });
        send(ws, { type: 'gameStart', color: 'black', opponentName: waitingPlayer.playerName, board: game.board });

        waitingPlayer = null;
      } else {
        waitingPlayer = ws;
        send(ws, { type: 'waiting' });
      }
    }

    if (msg.type === 'move') {
      const game = games.get(ws.gameId);
      if (!game) return;

      if (ws.color !== game.turn) {
        send(ws, { type: 'error', message: 'Not your turn' });
        return;
      }

      const result = makeMove(game, msg.from, msg.to, msg.promotion);
      if (!result.valid) {
        send(ws, { type: 'error', message: result.reason });
        return;
      }

      const moveData = {
        type: 'moveMade',
        from: msg.from,
        to: msg.to,
        board: game.board,
        turn: game.turn,
        status: game.status,
        promotion: result.move.promotion,
        special: result.move.special,
        moveCount: game.moves.length,
      };

      send(game.white, moveData);
      send(game.black, moveData);
    }

    if (msg.type === 'getLegalMoves') {
      const game = games.get(ws.gameId);
      if (!game) return;
      const moves = getLegalMoves(game, msg.row, msg.col);
      send(ws, { type: 'legalMoves', moves: moves.map(m => m.to) });
    }

    if (msg.type === 'resign') {
      const game = games.get(ws.gameId);
      if (!game) return;
      game.status = 'resigned';
      const winner = ws.color === 'white' ? 'black' : 'white';
      send(game.white, { type: 'gameOver', reason: 'resign', winner });
      send(game.black, { type: 'gameOver', reason: 'resign', winner });
    }
  });

  ws.on('close', () => {
    if (ws === waitingPlayer) {
      waitingPlayer = null;
    }
    const game = games.get(ws.gameId);
    if (game && game.status === 'playing' || game?.status === 'check') {
      const winner = ws.color === 'white' ? 'black' : 'white';
      const opponent = ws.color === 'white' ? game.black : game.white;
      send(opponent, { type: 'gameOver', reason: 'disconnect', winner });
      game.status = 'disconnected';
    }
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Chess server running on http://localhost:${PORT}`);
  console.log(`Open two browser tabs to play!`);
});
