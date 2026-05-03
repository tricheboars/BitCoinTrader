"""Static text — banners, help, ending screens."""

BANNER = r"""
 ▄▄▄▄    ██  ██████  ▄▄▄▄  ▄▄▄▄  ██  ██▄  ██     ▄▄▄▄▄ ▄▄▄▄   ▄▄▄  ▄▄▄  ▄▄▄▄ ▄▄▄▄
 █  █    ██    ██    █     █  █  ██  █▀█  ██       █   █  █  ▄▀  ▀ █  █ █    █  █
 █▄▄█    ██    ██    █     █  █  ██  █  █ ██       █   █▄▄█  █▄▄█  █  █ █▄▄  █▄▄█
 █  █ ▄▄ ██    ██    █     █  █  ██  █  █ ██       █   █  █  █  █  █▄▄█ █    █  █
 ▀  ▀ ▀▀ ▀▀    ▀▀    ▀▀▀▀  ▀▀▀▀  ▀▀  ▀  ▀ ▀▀       ▀   ▀  ▀  ▀  ▀  ▀▀▀  ▀▀▀▀ ▀  ▀

  ── GREED IS GOOD ──
  market open. tick interval: 5s. starting wad: $10,000.
  type 'help' for commands. type 'market' for the tape.
"""

HELP = """
COMMANDS
  market                 show the ticker tape
  portfolio              show your holdings + P/L
  buy  <TICKER> <$amt>   open/add to a position by dollar amount
  sell <TICKER> <shares> close shares of a position  (or 'all')
  news                   how news works (it just happens — watch the wire)
  help                   this screen
  clear                  clear the scrollback

OBJECTIVE
  reach $1,000,000 net worth → MASTER OF THE UNIVERSE
  hit $0 cash AND $0 holdings → MARGIN CALL
"""

MASTER_TEXT = r"""
  ╔══════════════════════════════════════════════════════════╗
  ║                                                          ║
  ║          MASTER OF THE UNIVERSE                          ║
  ║          ──────────────────────                          ║
  ║                                                          ║
  ║   you crossed $1,000,000.                                ║
  ║   the brick phone rings. it's a yacht broker.            ║
  ║   greed was, in fact, good.                              ║
  ║                                                          ║
  ╚══════════════════════════════════════════════════════════╝
"""

MARGIN_CALL_TEXT = r"""
  ╔══════════════════════════════════════════════════════════╗
  ║                                                          ║
  ║          MARGIN CALL                                     ║
  ║          ───────────                                     ║
  ║                                                          ║
  ║   you are out of cash. you are out of shares.            ║
  ║   the brick phone rings. it's not a yacht broker.        ║
  ║                                                          ║
  ╚══════════════════════════════════════════════════════════╝
"""
