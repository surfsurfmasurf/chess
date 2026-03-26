#!/usr/bin/env python3
"""
Terminal Chess Game - 키보드만으로 플레이하는 체스
사용법: python terminal_chess.py
"""

import os
import sys

# UTF-8 입출력 보장
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace('-', '') != 'utf8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
try:
    if sys.stderr.encoding and sys.stderr.encoding.lower().replace('-', '') != 'utf8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
try:
    if sys.stdin.encoding and sys.stdin.encoding.lower().replace('-', '') != 'utf8':
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def safe_input(prompt=""):
    """인코딩 오류에 안전한 input 래퍼"""
    try:
        return input(prompt)
    except UnicodeDecodeError:
        # stdin에서 직접 바이트로 읽기
        sys.stdout.write(prompt)
        sys.stdout.flush()
        try:
            raw = sys.stdin.buffer.readline()
            return raw.decode('utf-8', errors='replace').rstrip('\n\r')
        except Exception:
            return raw.decode('latin-1', errors='replace').rstrip('\n\r')
    except Exception:
        return ""

# ═══════════════════════════════════════════
#  기물 유니코드 & 색상
# ═══════════════════════════════════════════

# ASCII 약자 — 모든 터미널에서 폭이 일정하게 정렬됨
PIECES = {
    ('king',   'white'): 'K', ('queen',  'white'): 'Q',
    ('rook',   'white'): 'R', ('bishop', 'white'): 'B',
    ('knight', 'white'): 'N', ('pawn',   'white'): 'P',
    ('king',   'black'): 'k', ('queen',  'black'): 'q',
    ('rook',   'black'): 'r', ('bishop', 'black'): 'b',
    ('knight', 'black'): 'n', ('pawn',   'black'): 'p',
}

# 유니코드 기물 (--unicode 옵션용)
PIECES_UNICODE = {
    ('king',   'white'): 'K', ('queen',  'white'): 'Q',
    ('rook',   'white'): 'R', ('bishop', 'white'): 'B',
    ('knight', 'white'): 'N', ('pawn',   'white'): 'P',
    ('king',   'black'): 'k', ('queen',  'black'): 'q',
    ('rook',   'black'): 'r', ('bishop', 'black'): 'b',
    ('knight', 'black'): 'n', ('pawn',   'black'): 'p',
}

# ANSI 색상 코드
class Color:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    BG_DARK  = '\033[48;5;94m'   # 어두운 칸
    BG_LIGHT = '\033[48;5;223m'  # 밝은 칸
    BG_HIGHLIGHT = '\033[48;5;228m'  # 선택된 칸
    BG_MOVE  = '\033[48;5;114m'  # 이동 가능 칸
    BG_CAPTURE = '\033[48;5;203m'  # 캡처 가능 칸
    BG_LASTMOVE = '\033[48;5;186m'  # 마지막 이동

# ═══════════════════════════════════════════
#  체스 엔진
# ═══════════════════════════════════════════

class ChessEngine:
    def __init__(self):
        self.board = self.create_initial_board()
        self.turn = 'white'
        self.en_passant_target = None
        self.castling_rights = {
            'white': {'king_side': True, 'queen_side': True},
            'black': {'king_side': True, 'queen_side': True},
        }
        self.move_history = []
        self.status = 'playing'  # playing, check, checkmate, stalemate
        self.last_move = None
        self.captured_pieces = {'white': [], 'black': []}  # 잡힌 기물

    def create_initial_board(self):
        board = [[None]*8 for _ in range(8)]
        back_rank = ['rook','knight','bishop','queen','king','bishop','knight','rook']
        for col in range(8):
            board[0][col] = {'type': back_rank[col], 'color': 'black'}
            board[1][col] = {'type': 'pawn', 'color': 'black'}
            board[6][col] = {'type': 'pawn', 'color': 'white'}
            board[7][col] = {'type': back_rank[col], 'color': 'white'}
        return board

    def clone_board(self):
        return [[{**cell} if cell else None for cell in row] for row in self.board]

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_pseudo_legal_moves(self, board, row, col, en_passant=None, castling=None):
        piece = board[row][col]
        if not piece:
            return []
        moves = []
        ptype, color = piece['type'], piece['color']
        direction = -1 if color == 'white' else 1

        def add_if_valid(r, c, special=None):
            if not self.in_bounds(r, c):
                return False
            target = board[r][c]
            if target and target['color'] == color:
                return False
            moves.append({
                'from': (row, col), 'to': (r, c),
                'capture': target is not None, 'special': special
            })
            return target is None

        if ptype == 'pawn':
            # 전진
            nr = row + direction
            if self.in_bounds(nr, col) and not board[nr][col]:
                moves.append({'from': (row,col), 'to': (nr,col), 'capture': False, 'special': None})
                # 2칸 전진
                start_row = 6 if color == 'white' else 1
                nr2 = row + 2 * direction
                if row == start_row and not board[nr2][col]:
                    moves.append({'from': (row,col), 'to': (nr2,col), 'capture': False, 'special': 'double_push'})
            # 대각선 캡처
            for dc in [-1, 1]:
                nr, nc = row + direction, col + dc
                if not self.in_bounds(nr, nc):
                    continue
                if board[nr][nc] and board[nr][nc]['color'] != color:
                    moves.append({'from': (row,col), 'to': (nr,nc), 'capture': True, 'special': None})
                # 앙파상
                if en_passant and en_passant == (nr, nc):
                    moves.append({'from': (row,col), 'to': (nr,nc), 'capture': True, 'special': 'en_passant'})

        elif ptype == 'knight':
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                add_if_valid(row+dr, col+dc)

        elif ptype == 'king':
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                add_if_valid(row+dr, col+dc)
            # 캐슬링
            if castling:
                rights = castling.get(color, {})
                home_row = 7 if color == 'white' else 0
                if row == home_row and col == 4:
                    if rights.get('king_side') and not board[home_row][5] and not board[home_row][6]:
                        if board[home_row][7] and board[home_row][7]['type'] == 'rook':
                            moves.append({'from': (row,col), 'to': (home_row,6), 'capture': False, 'special': 'castle_king'})
                    if rights.get('queen_side') and not board[home_row][3] and not board[home_row][2] and not board[home_row][1]:
                        if board[home_row][0] and board[home_row][0]['type'] == 'rook':
                            moves.append({'from': (row,col), 'to': (home_row,2), 'capture': False, 'special': 'castle_queen'})
        else:
            # 슬라이딩 기물
            directions = {
                'bishop': [(-1,-1),(-1,1),(1,-1),(1,1)],
                'rook':   [(-1,0),(1,0),(0,-1),(0,1)],
                'queen':  [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)],
            }
            for dr, dc in directions[ptype]:
                for i in range(1, 8):
                    if not add_if_valid(row+dr*i, col+dc*i):
                        break
        return moves

    def is_square_attacked(self, board, row, col, by_color):
        no_castling = {'white': {}, 'black': {}}
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if not p or p['color'] != by_color:
                    continue
                moves = self.get_pseudo_legal_moves(board, r, c, None, no_castling)
                if any(m['to'] == (row, col) for m in moves):
                    return True
        return False

    def find_king(self, board, color):
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p['type'] == 'king' and p['color'] == color:
                    return (r, c)
        return None

    def apply_move_to_board(self, board, move):
        new_board = [[{**cell} if cell else None for cell in row] for row in board]
        fr, fc = move['from']
        tr, tc = move['to']
        piece = {**new_board[fr][fc]}
        new_board[fr][fc] = None
        new_board[tr][tc] = piece

        if move['special'] == 'en_passant':
            new_board[fr][tc] = None
        elif move['special'] == 'castle_king':
            new_board[tr][5] = new_board[tr][7]
            new_board[tr][7] = None
        elif move['special'] == 'castle_queen':
            new_board[tr][3] = new_board[tr][0]
            new_board[tr][0] = None

        # 프로모션
        if piece['type'] == 'pawn' and (tr == 0 or tr == 7):
            new_board[tr][tc] = {'type': move.get('promotion', 'queen'), 'color': piece['color']}

        return new_board

    def get_legal_moves(self, row, col):
        piece = self.board[row][col]
        if not piece:
            return []
        pseudo = self.get_pseudo_legal_moves(
            self.board, row, col, self.en_passant_target, self.castling_rights
        )
        enemy = 'black' if piece['color'] == 'white' else 'white'
        legal = []
        for move in pseudo:
            # 캐슬링 특수 검사
            if move['special'] in ('castle_king', 'castle_queen'):
                r = move['from'][0]
                if self.is_square_attacked(self.board, r, 4, enemy):
                    continue
                if move['special'] == 'castle_king':
                    if self.is_square_attacked(self.board, r, 5, enemy):
                        continue
                    if self.is_square_attacked(self.board, r, 6, enemy):
                        continue
                else:
                    if self.is_square_attacked(self.board, r, 3, enemy):
                        continue
                    if self.is_square_attacked(self.board, r, 2, enemy):
                        continue

            new_board = self.apply_move_to_board(self.board, move)
            king = self.find_king(new_board, piece['color'])
            if king and not self.is_square_attacked(new_board, king[0], king[1], enemy):
                legal.append(move)
        return legal

    def get_all_legal_moves(self, color):
        moves = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p['color'] == color:
                    moves.extend(self.get_legal_moves(r, c))
        return moves

    def make_move(self, from_pos, to_pos, promotion='queen'):
        fr, fc = from_pos
        tr, tc = to_pos
        piece = self.board[fr][fc]
        if not piece or piece['color'] != self.turn:
            return False, "자기 기물이 아닙니다"

        legal = self.get_legal_moves(fr, fc)
        move = None
        for m in legal:
            if m['to'] == (tr, tc):
                move = m
                break
        if not move:
            return False, "불법 수입니다"

        # 프로모션
        if piece['type'] == 'pawn' and (tr == 0 or tr == 7):
            move['promotion'] = promotion

        # 캡처된 기물 기록
        captured = self.board[tr][tc]
        if move['special'] == 'en_passant':
            captured = self.board[fr][tc]
        if captured:
            self.captured_pieces[captured['color']].append(captured['type'])

        # 수 적용
        self.board = self.apply_move_to_board(self.board, move)
        self.last_move = move

        # 앙파상 타겟
        self.en_passant_target = None
        if move['special'] == 'double_push':
            self.en_passant_target = ((fr + tr) // 2, fc)

        # 캐슬링 권리
        if piece['type'] == 'king':
            self.castling_rights[piece['color']] = {'king_side': False, 'queen_side': False}
        if piece['type'] == 'rook':
            home_row = 7 if piece['color'] == 'white' else 0
            if fr == home_row and fc == 0:
                self.castling_rights[piece['color']]['queen_side'] = False
            if fr == home_row and fc == 7:
                self.castling_rights[piece['color']]['king_side'] = False
        if move['capture']:
            if (tr, tc) == (0, 0): self.castling_rights['black']['queen_side'] = False
            if (tr, tc) == (0, 7): self.castling_rights['black']['king_side'] = False
            if (tr, tc) == (7, 0): self.castling_rights['white']['queen_side'] = False
            if (tr, tc) == (7, 7): self.castling_rights['white']['king_side'] = False

        # 턴 교대
        prev_turn = self.turn
        self.turn = 'black' if self.turn == 'white' else 'white'

        # 이동 기록
        self.move_history.append({
            'from': from_pos, 'to': to_pos,
            'piece': piece['type'], 'color': prev_turn,
            'special': move['special'], 'notation': self.to_notation(move, piece)
        })

        # 게임 상태 판정
        enemy_moves = self.get_all_legal_moves(self.turn)
        enemy_king = self.find_king(self.board, self.turn)
        in_check = self.is_square_attacked(self.board, enemy_king[0], enemy_king[1], prev_turn)

        if len(enemy_moves) == 0:
            self.status = 'checkmate' if in_check else 'stalemate'
        else:
            self.status = 'check' if in_check else 'playing'

        return True, "OK"

    def to_notation(self, move, piece):
        """수를 체스 표기법으로 변환"""
        files = 'abcdefgh'
        fr, fc = move['from']
        tr, tc = move['to']
        if move['special'] == 'castle_king':
            return 'O-O'
        if move['special'] == 'castle_queen':
            return 'O-O-O'
        piece_letter = {'king':'K','queen':'Q','rook':'R','bishop':'B','knight':'N','pawn':''}.get(piece['type'],'')
        capture = 'x' if move['capture'] else ''
        if piece['type'] == 'pawn' and move['capture']:
            piece_letter = files[fc]
        dest = f"{files[tc]}{8-tr}"
        return f"{piece_letter}{capture}{dest}"


# ═══════════════════════════════════════════
#  터미널 UI
# ═══════════════════════════════════════════

class TerminalChessUI:
    def __init__(self):
        self.engine = ChessEngine()
        self.selected = None
        self.legal_moves = []
        self.message = ""
        self.use_color = self.supports_color()

    def supports_color(self):
        if os.name == 'nt':
            os.system('')  # Windows ANSI 활성화
            return True
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def pos_to_notation(self, row, col):
        return f"{'abcdefgh'[col]}{8-row}"

    def notation_to_pos(self, notation):
        """e2 → (6, 4)"""
        if len(notation) != 2:
            return None
        col = 'abcdefgh'.find(notation[0].lower())
        try:
            row = 8 - int(notation[1])
        except ValueError:
            return None
        if col < 0 or row < 0 or row > 7:
            return None
        return (row, col)

    def piece_value(self, ptype):
        return {'pawn':1,'knight':3,'bishop':3,'rook':5,'queen':9,'king':0}.get(ptype,0)

    def render_captured(self, color):
        """잡힌 기물 표시"""
        pieces = self.engine.captured_pieces[color]
        if not pieces:
            return ""
        sorted_pieces = sorted(pieces, key=self.piece_value, reverse=True)
        symbols = [PIECES.get((p, color), '?') for p in sorted_pieces]
        total = sum(self.piece_value(p) for p in pieces)
        return ' '.join(symbols) + f"  (+{total})" if total > 0 else ' '.join(symbols)

    def render_board(self):
        """체스판 렌더링 — 넓은 칸, ASCII 기물, 깔끔한 정렬"""
        board = self.engine.board
        last = self.engine.last_move
        legal_targets = {m['to'] for m in self.legal_moves}
        capture_targets = {m['to'] for m in self.legal_moves if m['capture']}

        # 칸 너비: 내부 8칸 (공백 포함)
        CW = 8  # cell width (내부)
        lines = []
        lines.append("")

        # 잡힌 흑 기물 (백이 잡은 것)
        cap_black = self.render_captured('black')
        if cap_black:
            lines.append(f"    잡은 기물: {cap_black}")
        lines.append("")

        # 열 레이블 (위)
        col_labels = "      "
        for ch in "abcdefgh":
            col_labels += ch.center(CW) + " "
        lines.append(col_labels)
        lines.append("")

        # 상단 테두리
        top = "    +" + (("-" * CW) + "+") * 8
        lines.append(top)

        for row in range(8):
            rank = str(8 - row)

            # 기물 행 (칸 내부 가운데 줄)
            line = f"  {rank} |"
            for col in range(8):
                piece = board[row][col]
                is_light = (row + col) % 2 == 0
                is_selected = self.selected == (row, col)
                is_legal = (row, col) in legal_targets
                is_capture = (row, col) in capture_targets
                is_last = last and ((row,col) == last['from'] or (row,col) == last['to'])

                # 기물 표시 문자열 결정
                if piece:
                    sym = PIECES.get((piece['type'], piece['color']), '?')
                else:
                    sym = ''

                # 칸 내용 구성
                if self.use_color:
                    # 배경색
                    if is_selected:
                        bg = Color.BG_HIGHLIGHT
                    elif is_capture:
                        bg = Color.BG_CAPTURE
                    elif is_legal:
                        bg = Color.BG_MOVE
                    elif is_last:
                        bg = Color.BG_LASTMOVE
                    elif is_light:
                        bg = Color.BG_LIGHT
                    else:
                        bg = Color.BG_DARK

                    if piece:
                        fg = Color.BOLD + Color.WHITE if piece['color'] == 'white' else Color.BOLD + '\033[30m'
                        content = f"({sym})" if is_capture else f" {sym} "
                        inner = content.center(CW)
                        cell = f"{bg}{fg}{inner}{Color.RESET}"
                    elif is_legal:
                        inner = " .. ".center(CW)
                        cell = f"{bg}{inner}{Color.RESET}"
                    else:
                        inner = " " * CW
                        cell = f"{bg}{inner}{Color.RESET}"
                else:
                    # 색상 미지원
                    if is_selected and piece:
                        content = f"[{sym}]"
                    elif is_capture and piece:
                        content = f"({sym})"
                    elif is_legal and not piece:
                        content = ".."
                    elif piece:
                        # 밝은칸/어두운칸 구분
                        if is_light:
                            content = f" {sym} "
                        else:
                            content = f":{sym}:"
                    else:
                        content = "   " if is_light else ":::"

                    cell = content.center(CW)

                line += cell + "|"

            line += f" {rank}"
            lines.append(line)

            # 행 구분선
            sep = "    +" + (("-" * CW) + "+") * 8
            lines.append(sep)

        # 열 레이블 (아래)
        lines.append(col_labels)

        # 잡힌 백 기물 (흑이 잡은 것)
        lines.append("")
        cap_white = self.render_captured('white')
        if cap_white:
            lines.append(f"    잡은 기물: {cap_white}")

        return '\n'.join(lines)

    def render_move_history(self):
        """이동 기록 표시"""
        history = self.engine.move_history
        if not history:
            return "      (no moves yet)"
        lines = []
        for i in range(0, len(history), 2):
            move_num = i // 2 + 1
            white_move = history[i]['notation'] if i < len(history) else ""
            black_move = history[i+1]['notation'] if i+1 < len(history) else ""
            lines.append(f"      {move_num:>3}. {white_move:<10} {black_move}")
        if len(lines) > 10:
            lines = ['      ...'] + lines[-10:]
        return '\n'.join(lines)

    def render_status(self):
        """게임 상태 표시"""
        e = self.engine
        turn_text = "WHITE (uppercase)" if e.turn == 'white' else "BLACK (lowercase)"
        status_text = ""

        if e.status == 'checkmate':
            winner = "WHITE" if e.turn == 'black' else "BLACK"
            if self.use_color:
                status_text = f"    {Color.RED}{Color.BOLD}*** CHECKMATE! {winner} wins! ***{Color.RESET}"
            else:
                status_text = f"    *** CHECKMATE! {winner} wins! ***"
        elif e.status == 'stalemate':
            if self.use_color:
                status_text = f"    {Color.YELLOW}*** STALEMATE! Draw! ***{Color.RESET}"
            else:
                status_text = "    *** STALEMATE! Draw! ***"
        elif e.status == 'check':
            if self.use_color:
                status_text = f"    {Color.RED}{Color.BOLD}!!! CHECK !!!{Color.RESET}"
            else:
                status_text = "    !!! CHECK !!!"

        lines = [
            f"    Turn: {turn_text}",
        ]
        if status_text:
            lines.append(status_text)
        return '\n'.join(lines)

    def render(self):
        """전체 화면 렌더링"""
        W = 82  # 전체 너비
        self.clear_screen()
        if self.use_color:
            print(f"\n{Color.BOLD}    TERMINAL CHESS{Color.RESET}")
            print(f"    {'=' * (W - 4)}")
        else:
            print(f"\n    TERMINAL CHESS")
            print(f"    {'=' * (W - 4)}")
        print(f"    White = UPPERCASE (K Q R B N P)")
        print(f"    Black = lowercase (k q r b n p)")
        print(self.render_board())
        print()
        print(self.render_status())
        print()
        print(f"    {'-' * (W - 4)}")
        print(f"    기보:")
        print(self.render_move_history())
        print(f"    {'-' * (W - 4)}")
        if self.message:
            if self.use_color:
                print(f"\n    {Color.YELLOW}{self.message}{Color.RESET}")
            else:
                print(f"\n    {self.message}")
        print()

    def show_help(self):
        print(f"""
    +----------------------------------------------------------+
    |  HELP                                                    |
    +----------------------------------------------------------+
    |                                                          |
    |  Move:       e2 e4    (from to)                          |
    |              e2e4     (no space OK)                       |
    |              e7e8q    (promotion: q/r/b/n)               |
    |                                                          |
    |  Select:     e2       (show legal moves)                 |
    |                                                          |
    |  Castling:   e1 g1    (king-side)                        |
    |              e1 c1    (queen-side)                       |
    |                                                          |
    |  Commands:   resign   (give up)                          |
    |              help     (this screen)                      |
    |              quit     (exit)                              |
    |                                                          |
    |  Board:      UPPERCASE = White  (K Q R B N P)            |
    |              lowercase = Black  (k q r b n p)            |
    |              ..       = legal move target                 |
    |              :::      = dark square (no color mode)       |
    |                                                          |
    +----------------------------------------------------------+
""")
        input("    Enter to continue...")

    def ask_promotion(self):
        """프로모션 기물 선택"""
        while True:
            print(f"\n    Promotion! Choose piece:")
            print(f"    q = Queen  |  r = Rook  |  b = Bishop  |  n = Knight")
            choice = safe_input(f"    Choice [q]: ").strip().lower()
            if choice in ('', 'q'): return 'queen'
            if choice == 'r': return 'rook'
            if choice == 'b': return 'bishop'
            if choice == 'n': return 'knight'
            print("    Invalid! Enter q, r, b, or n.")

    def parse_input(self, user_input):
        """사용자 입력 파싱"""
        text = user_input.strip().lower()

        if text in ('quit', 'exit', 'q'):
            return 'quit', None, None
        if text in ('help', 'h', '?'):
            return 'help', None, None
        if text in ('resign', 'gg'):
            return 'resign', None, None

        # "e2 e4" 또는 "e2e4" 형태 파싱
        promotion = None
        # 프로모션 접미사 (e7e8q)
        if len(text) >= 5 and text[-1] in 'qrbn':
            promotion = {'q':'queen','r':'rook','b':'bishop','n':'knight'}[text[-1]]
            text = text[:-1]

        # 공백으로 분리
        parts = text.split()
        if len(parts) == 2:
            from_str, to_str = parts
        elif len(parts) == 1 and len(text) == 4:
            from_str, to_str = text[:2], text[2:]
        elif len(parts) == 1 and len(text) == 2:
            return 'select', self.notation_to_pos(text), None
        else:
            return None, None, None

        from_pos = self.notation_to_pos(from_str)
        to_pos = self.notation_to_pos(to_str)
        if from_pos is None or to_pos is None:
            return None, None, None

        return 'move', (from_pos, to_pos), promotion

    def run(self):
        """메인 게임 루프"""
        self.message = "Type 'help' for commands  |  Move: 'e2 e4'"

        while True:
            self.render()

            # 게임 종료 확인
            if self.engine.status in ('checkmate', 'stalemate'):
                choice = safe_input("    New game(n) / Quit(q): ").strip().lower()
                if choice == 'n':
                    self.engine = ChessEngine()
                    self.selected = None
                    self.legal_moves = []
                    self.message = "New game!"
                    continue
                break

            # 입력 받기
            turn_label = "WHITE" if self.engine.turn == 'white' else "BLACK"
            try:
                user_input = safe_input(f"    [{turn_label}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n    Goodbye!")
                break

            if not user_input:
                self.selected = None
                self.legal_moves = []
                self.message = ""
                continue

            action, data, extra = self.parse_input(user_input)

            if action == 'quit':
                print("\n    Goodbye!")
                break

            elif action == 'help':
                self.show_help()

            elif action == 'resign':
                winner = "BLACK" if self.engine.turn == 'white' else "WHITE"
                self.engine.status = 'checkmate'
                self.message = f"Resigned! {winner} wins!"

            elif action == 'select':
                pos = data
                if pos is None:
                    self.message = "Invalid square. (e.g. e2)"
                    continue
                piece = self.engine.board[pos[0]][pos[1]]
                if piece and piece['color'] == self.engine.turn:
                    self.selected = pos
                    self.legal_moves = self.engine.get_legal_moves(pos[0], pos[1])
                    if self.legal_moves:
                        targets = [self.pos_to_notation(*m['to']) for m in self.legal_moves]
                        self.message = f"Selected {self.pos_to_notation(*pos)} -> can go: {', '.join(targets)}"
                    else:
                        self.message = f"{self.pos_to_notation(*pos)}: no legal moves"
                else:
                    self.message = "Select your own piece"
                    self.selected = None
                    self.legal_moves = []

            elif action == 'move':
                from_pos, to_pos = data
                promotion = extra

                piece = self.engine.board[from_pos[0]][from_pos[1]]
                if piece and piece['type'] == 'pawn' and (to_pos[0] == 0 or to_pos[0] == 7):
                    if not promotion:
                        self.selected = from_pos
                        self.legal_moves = self.engine.get_legal_moves(from_pos[0], from_pos[1])
                        self.render()
                        promotion = self.ask_promotion()

                success, msg = self.engine.make_move(from_pos, to_pos, promotion or 'queen')
                if success:
                    last = self.engine.move_history[-1]
                    self.message = f"OK: {last['notation']}"
                    self.selected = None
                    self.legal_moves = []
                else:
                    self.message = f"ERROR: {msg}"
            else:
                self.message = "Invalid input. Type 'help' for commands"


# ═══════════════════════════════════════════
#  Simple AI (간단한 AI 대전 모드)
# ═══════════════════════════════════════════

class SimpleAI:
    """간단한 평가 함수 + Minimax AI"""

    PIECE_VALUES = {
        'pawn': 100, 'knight': 320, 'bishop': 330,
        'rook': 500, 'queen': 900, 'king': 20000
    }

    # 기물-위치 테이블 (간소화)
    PAWN_TABLE = [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ]

    KNIGHT_TABLE = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]

    def __init__(self, engine, color='black', depth=3):
        self.engine = engine
        self.color = color
        self.depth = depth

    def evaluate(self, board):
        """보드 평가 함수"""
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if not piece:
                    continue
                value = self.PIECE_VALUES.get(piece['type'], 0)
                # 위치 보너스
                idx = r * 8 + c
                if piece['type'] == 'pawn':
                    pos_bonus = self.PAWN_TABLE[idx if piece['color'] == 'black' else 63 - idx]
                elif piece['type'] == 'knight':
                    pos_bonus = self.KNIGHT_TABLE[idx if piece['color'] == 'black' else 63 - idx]
                else:
                    pos_bonus = 0
                total = value + pos_bonus
                if piece['color'] == 'white':
                    score += total
                else:
                    score -= total
        return score

    def minimax(self, engine_state, depth, alpha, beta, maximizing):
        """알파-베타 가지치기가 포함된 Minimax"""
        if depth == 0:
            return self.evaluate(engine_state.board), None

        color = 'white' if maximizing else 'black'
        moves = engine_state.get_all_legal_moves(color)

        if not moves:
            king = engine_state.find_king(engine_state.board, color)
            enemy = 'black' if color == 'white' else 'white'
            if engine_state.is_square_attacked(engine_state.board, king[0], king[1], enemy):
                return (-99999 if maximizing else 99999), None
            return 0, None  # 스테일메이트

        # 수 정렬 (캡처 우선 → 가지치기 효율 향상)
        moves.sort(key=lambda m: (m['capture'], m.get('special', '') or ''), reverse=True)

        best_move = moves[0]
        if maximizing:
            max_eval = -999999
            for move in moves:
                # 임시 엔진 상태 생성
                new_engine = self.clone_engine(engine_state)
                new_engine.make_move(move['from'], move['to'])
                eval_score, _ = self.minimax(new_engine, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = 999999
            for move in moves:
                new_engine = self.clone_engine(engine_state)
                new_engine.make_move(move['from'], move['to'])
                eval_score, _ = self.minimax(new_engine, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def clone_engine(self, engine):
        """엔진 상태 복제"""
        import copy
        new = ChessEngine.__new__(ChessEngine)
        new.board = [[{**cell} if cell else None for cell in row] for row in engine.board]
        new.turn = engine.turn
        new.en_passant_target = engine.en_passant_target
        new.castling_rights = copy.deepcopy(engine.castling_rights)
        new.move_history = list(engine.move_history)
        new.status = engine.status
        new.last_move = engine.last_move
        new.captured_pieces = copy.deepcopy(engine.captured_pieces)
        return new

    def get_best_move(self):
        """최선의 수 계산"""
        maximizing = self.color == 'white'
        _, best_move = self.minimax(self.engine, self.depth, -999999, 999999, maximizing)
        return best_move


class TerminalChessAI(TerminalChessUI):
    """AI 대전 모드"""

    def __init__(self, ai_color='black', depth=3):
        super().__init__()
        self.ai_color = ai_color
        self.ai_depth = depth

    def run(self):
        self.message = f"AI mode (AI={self.ai_color}, depth={self.ai_depth})"

        while True:
            self.render()

            if self.engine.status in ('checkmate', 'stalemate'):
                choice = safe_input("    New game(n) / Quit(q): ").strip().lower()
                if choice == 'n':
                    self.engine = ChessEngine()
                    self.selected = None
                    self.legal_moves = []
                    self.message = "New game!"
                    continue
                break

            # AI 차례
            if self.engine.turn == self.ai_color:
                self.message = "AI thinking..."
                self.render()

                ai = SimpleAI(self.engine, self.ai_color, self.ai_depth)
                best = ai.get_best_move()

                if best:
                    success, _ = self.engine.make_move(best['from'], best['to'])
                    if success:
                        last = self.engine.move_history[-1]
                        self.message = f"AI played: {last['notation']}"
                        self.selected = None
                        self.legal_moves = []
                    continue
                else:
                    self.message = "AI cannot find a move"
                    break

            # 사람 차례
            turn_label = "WHITE" if self.engine.turn == 'white' else "BLACK"
            try:
                user_input = safe_input(f"    [{turn_label}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n    Goodbye!")
                break

            if not user_input:
                self.selected = None
                self.legal_moves = []
                self.message = ""
                continue

            action, data, extra = self.parse_input(user_input)

            if action == 'quit':
                break
            elif action == 'help':
                self.show_help()
            elif action == 'resign':
                self.message = "Resigned! AI wins!"
                self.engine.status = 'checkmate'
            elif action == 'select':
                pos = data
                if pos is None:
                    self.message = "Invalid square"
                    continue
                piece = self.engine.board[pos[0]][pos[1]]
                if piece and piece['color'] == self.engine.turn:
                    self.selected = pos
                    self.legal_moves = self.engine.get_legal_moves(pos[0], pos[1])
                    if self.legal_moves:
                        targets = [self.pos_to_notation(*m['to']) for m in self.legal_moves]
                        self.message = f"Selected {self.pos_to_notation(*pos)} -> {', '.join(targets)}"
                    else:
                        self.message = "No legal moves"
                else:
                    self.message = "Select your own piece"
                    self.selected = None
                    self.legal_moves = []
            elif action == 'move':
                from_pos, to_pos = data
                promotion = extra
                piece = self.engine.board[from_pos[0]][from_pos[1]]
                if piece and piece['type'] == 'pawn' and (to_pos[0] == 0 or to_pos[0] == 7):
                    if not promotion:
                        self.selected = from_pos
                        self.legal_moves = self.engine.get_legal_moves(from_pos[0], from_pos[1])
                        self.render()
                        promotion = self.ask_promotion()
                success, msg = self.engine.make_move(from_pos, to_pos, promotion or 'queen')
                if success:
                    last = self.engine.move_history[-1]
                    self.message = f"OK: {last['notation']}"
                    self.selected = None
                    self.legal_moves = []
                else:
                    self.message = f"ERROR: {msg}"
            else:
                self.message = "Invalid input. Type 'help'"


# ═══════════════════════════════════════════
#  네트워크 대전 모드
# ═══════════════════════════════════════════

import socket
import json
import threading
import select

class NetworkChess(TerminalChessUI):
    """네트워크 대전 모드 — 소켓 기반"""

    def __init__(self, conn, my_color, opponent_name="상대방"):
        super().__init__()
        self.conn = conn
        self.my_color = my_color
        self.opponent_name = opponent_name
        self.received_move = None
        self.disconnected = False
        self.lock = threading.Lock()

        # 수신 스레드 시작
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()

    def _send(self, data):
        """JSON 메시지 전송"""
        try:
            msg = json.dumps(data, ensure_ascii=False).encode('utf-8')
            length = len(msg)
            self.conn.sendall(length.to_bytes(4, 'big') + msg)
        except Exception:
            self.disconnected = True

    def _recv_msg(self):
        """JSON 메시지 수신 (길이 접두사 프로토콜)"""
        try:
            raw_len = self._recv_exact(4)
            if not raw_len:
                return None
            length = int.from_bytes(raw_len, 'big')
            raw_data = self._recv_exact(length)
            if not raw_data:
                return None
            return json.loads(raw_data.decode('utf-8'))
        except Exception:
            return None

    def _recv_exact(self, n):
        """정확히 n바이트 수신"""
        data = b''
        while len(data) < n:
            chunk = self.conn.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _receive_loop(self):
        """별도 스레드에서 상대 수 수신"""
        while not self.disconnected:
            msg = self._recv_msg()
            if msg is None:
                self.disconnected = True
                break
            with self.lock:
                if msg.get('type') == 'move':
                    self.received_move = msg
                elif msg.get('type') == 'resign':
                    self.received_move = {'type': 'resign'}
                elif msg.get('type') == 'chat':
                    self.message = f"💬 {self.opponent_name}: {msg.get('text', '')}"

    def render_status(self):
        """상태 표시에 네트워크 정보 추가"""
        base = super().render_status()
        my_label = "WHITE" if self.my_color == 'white' else "BLACK"
        net_info = f"    You: {my_label} (vs {self.opponent_name})"
        return f"{net_info}\n{base}"

    def run(self):
        my_color = self.my_color
        self.message = f"Online game vs {self.opponent_name} (you={my_color})"

        while True:
            self.render()

            if self.disconnected:
                print(f"\n    !!! Opponent disconnected !!!")
                input("    Press Enter to exit...")
                break

            if self.engine.status in ('checkmate', 'stalemate'):
                choice = safe_input("    New game(n) / Quit(q): ").strip().lower()
                if choice == 'n':
                    self.engine = ChessEngine()
                    self.selected = None
                    self.legal_moves = []
                    self.message = "New game!"
                    continue
                break

            # 상대 차례: 수신 대기
            if self.engine.turn != my_color:
                self.message = f"Waiting for {self.opponent_name}..."
                self.render()

                while True:
                    if self.disconnected:
                        break
                    with self.lock:
                        move_data = self.received_move
                        self.received_move = None

                    if move_data:
                        if move_data.get('type') == 'resign':
                            self.message = f"{self.opponent_name} resigned! You win!"
                            self.engine.status = 'checkmate'
                            break

                        from_pos = tuple(move_data['from'])
                        to_pos = tuple(move_data['to'])
                        promotion = move_data.get('promotion', 'queen')
                        success, msg = self.engine.make_move(from_pos, to_pos, promotion)
                        if success:
                            last = self.engine.move_history[-1]
                            self.message = f"{self.opponent_name}: {last['notation']}"
                        else:
                            self.message = f"Sync error: {msg}"
                        break

                    import time
                    time.sleep(0.1)
                continue

            # 내 차례
            turn_label = "WHITE" if my_color == 'white' else "BLACK"
            try:
                user_input = safe_input(f"    [{turn_label}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                self._send({'type': 'resign'})
                print("\n    Resigned. Goodbye!")
                break

            if not user_input:
                self.selected = None
                self.legal_moves = []
                self.message = ""
                continue

            action, data, extra = self.parse_input(user_input)

            if action == 'quit':
                self._send({'type': 'resign'})
                print("\n    Resigned. Goodbye!")
                break

            elif action == 'help':
                self.show_help()

            elif action == 'resign':
                self._send({'type': 'resign'})
                self.message = "You resigned!"
                self.engine.status = 'checkmate'

            elif action == 'select':
                pos = data
                if pos is None:
                    self.message = "Invalid square"
                    continue
                piece = self.engine.board[pos[0]][pos[1]]
                if piece and piece['color'] == my_color:
                    self.selected = pos
                    self.legal_moves = self.engine.get_legal_moves(pos[0], pos[1])
                    if self.legal_moves:
                        targets = [self.pos_to_notation(*m['to']) for m in self.legal_moves]
                        self.message = f"Selected {self.pos_to_notation(*pos)} -> {', '.join(targets)}"
                    else:
                        self.message = "No legal moves"
                else:
                    self.message = "Select your own piece"
                    self.selected = None
                    self.legal_moves = []

            elif action == 'move':
                from_pos, to_pos = data
                promotion = extra

                piece = self.engine.board[from_pos[0]][from_pos[1]]
                if piece and piece['type'] == 'pawn' and (to_pos[0] == 0 or to_pos[0] == 7):
                    if not promotion:
                        self.selected = from_pos
                        self.legal_moves = self.engine.get_legal_moves(from_pos[0], from_pos[1])
                        self.render()
                        promotion = self.ask_promotion()

                success, msg = self.engine.make_move(from_pos, to_pos, promotion or 'queen')
                if success:
                    self._send({
                        'type': 'move',
                        'from': list(from_pos),
                        'to': list(to_pos),
                        'promotion': promotion or 'queen'
                    })
                    last = self.engine.move_history[-1]
                    self.message = f"OK: {last['notation']}"
                    self.selected = None
                    self.legal_moves = []
                else:
                    self.message = f"ERROR: {msg}"
            else:
                self.message = "Invalid input. Type 'help'"

        try:
            self.conn.close()
        except Exception:
            pass


def run_server(host='0.0.0.0', port=5555, name='호스트'):
    """서버 모드: 상대 접속 대기"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)

    # 실제 IP 표시
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        my_ip = s.getsockname()[0]
        s.close()
    except Exception:
        my_ip = host

    print(f"""
    +----------------------------------------------------------+
    |  SERVER MODE - Waiting for opponent...                    |
    +----------------------------------------------------------+
    |                                                          |
    |  Opponent should run:                                    |
    |                                                          |
    |  python3 terminal_chess.py --connect {my_ip:<15s}        |
    |          --port {port}                                    |
    |                                                          |
    |  (Ctrl+C to cancel)                                      |
    +----------------------------------------------------------+
""")

    try:
        conn, addr = sock.accept()
    except KeyboardInterrupt:
        sock.close()
        print("\n    Server stopped.")
        return

    print(f"    Connected: {addr[0]}:{addr[1]}")

    # 핸드셰이크: 이름 교환
    handshake = json.dumps({'name': name, 'color': 'white'}).encode('utf-8')
    length = len(handshake)
    conn.sendall(length.to_bytes(4, 'big') + handshake)

    # 상대 이름 수신
    raw_len = conn.recv(4)
    opp_length = int.from_bytes(raw_len, 'big')
    opp_data = json.loads(conn.recv(opp_length).decode('utf-8'))
    opponent_name = opp_data.get('name', '상대방')

    print(f"    Game start vs {opponent_name}! (host=white)")

    game = NetworkChess(conn, my_color='white', opponent_name=opponent_name)
    game.run()
    sock.close()


def run_client(host, port=5555, name='게스트'):
    """클라이언트 모드: 서버에 접속"""
    print(f"\n    Connecting to {host}:{port}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(10)
        sock.connect((host, port))
        sock.settimeout(None)
    except Exception as e:
        print(f"    Connection failed: {e}")
        return

    print(f"    Connected!")

    # 핸드셰이크: 서버에서 색상 수신
    raw_len = sock.recv(4)
    srv_length = int.from_bytes(raw_len, 'big')
    srv_data = json.loads(sock.recv(srv_length).decode('utf-8'))
    opponent_name = srv_data.get('name', '호스트')

    # 내 이름 전송
    handshake = json.dumps({'name': name}).encode('utf-8')
    length = len(handshake)
    sock.sendall(length.to_bytes(4, 'big') + handshake)

    print(f"    Game start vs {opponent_name}! (guest=black)")

    game = NetworkChess(sock, my_color='black', opponent_name=opponent_name)
    game.run()


# ═══════════════════════════════════════════
#  메인
# ═══════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description='터미널 체스 게임')
    parser.add_argument('--host', type=str, help='서버 모드: 바인드 주소 (기본: 0.0.0.0)')
    parser.add_argument('--connect', type=str, help='클라이언트 모드: 서버 IP 주소')
    parser.add_argument('--port', type=int, default=5555, help='포트 번호 (기본: 5555)')
    parser.add_argument('--name', type=str, default=None, help='플레이어 이름')
    args = parser.parse_args()

    # 네트워크 모드
    if args.connect:
        name = args.name or input("    Your name: ").strip() or "Guest"
        run_client(args.connect, args.port, name)
        return
    if args.host is not None:
        name = args.name or input("    Your name: ").strip() or "Host"
        run_server(args.host or '0.0.0.0', args.port, name)
        return

    # 로컬 모드
    print(f"""
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
""")

    choice = safe_input("    Select: ").strip()

    if choice == '1':
        ui = TerminalChessUI()
        ui.run()
    elif choice == '2':
        ui = TerminalChessAI(ai_color='black', depth=2)
        ui.run()
    elif choice == '3':
        ui = TerminalChessAI(ai_color='black', depth=3)
        ui.run()
    elif choice == '4':
        ui = TerminalChessAI(ai_color='black', depth=4)
        ui.run()
    elif choice == '5':
        name = safe_input("    Your name: ").strip() or "Host"
        port = safe_input("    Port [5555]: ").strip()
        port = int(port) if port else 5555
        run_server('0.0.0.0', port, name)
    elif choice == '6':
        host = safe_input("    Server IP: ").strip()
        if not host:
            print("    ERROR: IP address required.")
            return
        name = safe_input("    Your name: ").strip() or "Guest"
        port = safe_input("    Port [5555]: ").strip()
        port = int(port) if port else 5555
        run_client(host, port, name)
    elif choice in ('q', 'quit'):
        print("  안녕히! 👋")
    else:
        print("  잘못된 선택입니다.")

if __name__ == '__main__':
    main()
