# ♔ Chess Game ♚

브라우저(웹) 및 터미널에서 플레이 가능한 온라인 체스 게임입니다.

## 기능

### 웹 버전 (Node.js)
- 브라우저에서 마우스로 플레이
- WebSocket 기반 실시간 대전
- 드래그 & 클릭으로 기물 이동
- 합법수 하이라이트

### 터미널 버전 (Python)
- 키보드만으로 플레이 (`e2 e4` 형식)
- 유니코드 기물 + ANSI 컬러 체스판
- AI 대전 (Minimax + Alpha-Beta 가지치기, 난이도 3단계)
- **네트워크 대전** — 원격 서버 간 TCP 소켓 대전

### 체스 엔진 (공통)
- 모든 규칙 지원: 캐슬링, 앙파상, 프로모션
- 체크 / 체크메이트 / 스테일메이트 판정
- 합법수 검증 (핀, 체크 탈출 자동 처리)

---

## 설치 및 실행

### 요구사항

- **웹 버전**: Node.js 18+
- **터미널 버전**: Python 3.8+ (추가 패키지 없음)

### 설치

```bash
git clone https://github.com/<your-username>/chess.git
cd chess
```

### 웹 버전 실행

```bash
npm install
node server.js
```

브라우저에서 `http://localhost:3000` 접속 (탭 2개로 대전)

### 터미널 버전 실행

```bash
python3 terminal_chess.py
```

메뉴에서 모드를 선택합니다:

```
  ╔══════════════════════════════════════════╗
  ║         ♔  터미널 체스  ♚               ║
  ╠══════════════════════════════════════════╣
  ║                                          ║
  ║   1. 👥 사람 vs 사람 (로컬)             ║
  ║   2. 🤖 사람 vs AI (쉬움)               ║
  ║   3. 🤖 사람 vs AI (보통)               ║
  ║   4. 🤖 사람 vs AI (어려움)             ║
  ║   5. 🌐 네트워크 대전 (호스트)           ║
  ║   6. 🌐 네트워크 대전 (접속)             ║
  ║   q. 종료                                ║
  ║                                          ║
  ╚══════════════════════════════════════════╝
```

---

## 네트워크 대전 (리눅스 서버 간 대전)

두 대의 리눅스 서버에서 SSH 터미널로 체스를 즐길 수 있습니다.

### 구성도

```
  서버 A (호스트, 백)                서버 B (접속, 흑)
  ┌──────────────────┐             ┌──────────────────┐
  │  $ python3       │    TCP/IP   │  $ python3       │
  │  terminal_chess  │◄───────────►│  terminal_chess  │
  │  --host 0.0.0.0  │   포트 5555 │  --connect <IP>  │
  └──────────────────┘             └──────────────────┘
```

### 설치 (양쪽 서버 모두)

```bash
# 1. 저장소 클론
git clone https://github.com/<your-username>/chess.git
cd chess

# Python3만 있으면 됨 (추가 패키지 불필요)
python3 --version   # 3.8 이상 확인
```

### 실행 — 서버 A (호스트)

```bash
python3 terminal_chess.py --host 0.0.0.0 --port 5555 --name "철수"
```

출력:
```
  ┌──────────────────────────────────────────────────┐
  │  🌐 서버 모드 — 상대 접속 대기 중...              │
  │                                                  │
  │  상대방이 이 명령어로 접속:                       │
  │                                                  │
  │  python terminal_chess.py --connect 10.0.1.5 \   │
  │         --port 5555                               │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

### 실행 — 서버 B (접속)

```bash
python3 terminal_chess.py --connect <서버A의 IP> --port 5555 --name "영희"
```

접속되면 양쪽 터미널에 체스판이 표시되고 대전이 시작됩니다!

### 방화벽 설정

서버 A에서 해당 포트를 열어야 합니다:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5555/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --add-port=5555/tcp --permanent
sudo firewall-cmd --reload

# 또는 iptables
sudo iptables -A INPUT -p tcp --dport 5555 -j ACCEPT
```

### 포트가 막혀 있다면? — SSH 터널

방화벽을 건드릴 수 없을 때, SSH 터널로 우회할 수 있습니다:

```bash
# 서버 B에서 실행 (서버 A의 5555 포트를 로컬로 터널링)
ssh -L 5555:localhost:5555 user@서버A_IP

# 다른 터미널에서 localhost로 접속
python3 terminal_chess.py --connect localhost --port 5555 --name "영희"
```

---

## 조작법

```
  이동:      e2 e4     (출발 도착, 공백 구분)
             e2e4      (붙여써도 가능)

  기물 선택: e2        (합법수 하이라이트 표시)

  프로모션:  e7e8q     (q=퀸, r=룩, b=비숍, n=나이트)

  캐슬링:   e1 g1     (킹사이드)
             e1 c1     (퀸사이드)

  기타:     help      도움말
             resign    기권
             quit      종료
```

---

## 프로젝트 구조

```
chess/
├── server.js            # 웹 버전 서버 (Node.js + WebSocket)
├── public/
│   └── index.html       # 웹 버전 클라이언트
├── terminal_chess.py    # 터미널 버전 (Python, 단일 파일)
├── package.json         # Node.js 의존성
└── README.md
```

## 기술 스택

| 구성 요소 | 웹 버전 | 터미널 버전 |
|----------|---------|------------|
| 언어 | JavaScript | Python 3 |
| 서버 | Express + ws | 소켓 (stdlib) |
| 통신 | WebSocket | TCP 소켓 |
| UI | HTML/CSS/Canvas | ANSI 터미널 |
| AI | — | Minimax + Alpha-Beta |
| 외부 의존성 | express, ws | 없음 |

## 라이선스

MIT
