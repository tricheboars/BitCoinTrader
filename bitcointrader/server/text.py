"""Static text — banners, help, ending screens."""

BANNER = r"""
██████╗ ██╗████████╗ ██████╗ ██████╗ ██╗███╗   ██╗
██╔══██╗██║╚══██╔══╝██╔════╝██╔═══██╗██║████╗  ██║
██████╔╝██║   ██║   ██║     ██║   ██║██║██╔██╗ ██║
██╔══██╗██║   ██║   ██║     ██║   ██║██║██║╚██╗██║
██████╔╝██║   ██║   ╚██████╗╚██████╔╝██║██║ ╚████║
╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝
████████╗██████╗  █████╗ ██████╗ ███████╗██████╗
╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
   ██║   ██████╔╝███████║██║  ██║█████╗  ██████╔╝
   ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝  ██╔══██╗
   ██║   ██║  ██║██║  ██║██████╔╝███████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝

  ── GREED IS GOOD ──

  THE PITCH
    you start with $10,000 cash. ten parody tickers. one rigged market.
    prices walk every 5 seconds. news headlines slam tickers without warning.
    you cannot pause. you cannot undo. the phone is already ringing.

  WIN     reach $1,000,000 net worth ........... MASTER OF THE UNIVERSE
  LOSE    hit $0 cash AND $0 holdings .......... MARGIN CALL

  QUICK START
    market                  see the tape (all 10 tickers + prices)
    buy  $BTCN 1000         spend $1,000 cash on BitCorn
    sell $BTCN all          dump your entire BitCorn position
    portfolio               your holdings · P/L · greed score
    help                    full command list

  TIPS
    · click any ticker in the right sidebar to prefill 'buy <TICKER> '
    · the amber news wire (top) moves prices — you adapt, you don't react
    · greed climbs with every trade. higher greed = wilder swings.
    · ↑ / ↓ for command history.

  good luck. don't get rugged.
"""

HELP = """
COMMANDS
  market                       show the ticker tape (all 10 prices)
  portfolio                    your holdings · cost basis · P/L · greed
  buy  <TICKER> <$amount>      open or add to a position by dollar amount
                                 example:  buy $BTCN 500
                                           buy btcn 1,000
  sell <TICKER> <shares|all>   close shares of a position
                                 example:  sell $MUSK 0.25
                                           sell rugz all
  news                         (news fires automatically — watch the wire)
  help                         this screen
  clear                        clear the scrollback

  shortcuts:
    ↑ / ↓                       command history
    click ticker (sidebar)      prefills 'buy <TICKER> '

OBJECTIVE
  reach $1,000,000 net worth   →  MASTER OF THE UNIVERSE
  hit $0 cash AND $0 holdings  →  MARGIN CALL

GREED METER
  every trade nudges your GREED (0-100). the market reads your greed
  and responds — the fatter your wallet, the meaner the swings. there
  is no "playing it safe" ending. only winners and the margin-called.

NEWS WIRE
  events fire every 30-90 seconds. some hit one ticker (rug pulls,
  SEC probes); some hit ALL tickers (Fed rate cuts). you cannot react
  before the price moves. that's the point.

NOT FINANCIAL ADVICE
  $BTCN is not Bitcoin. $MUSK is not Tesla. nothing here is real.
  any resemblance to actual securities is parody and protected speech.
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
