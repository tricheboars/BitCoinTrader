"""Entry point — launches the FastAPI/uvicorn server."""
import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="bitcointrader")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--tick-ms", type=int, default=5000,
                        help="market tick interval in milliseconds")
    parser.add_argument("--start-cash", type=float, default=10000.0)
    parser.add_argument("--no-news", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    from bitcointrader.server import config
    config.TICK_MS = args.tick_ms
    config.START_CASH = args.start_cash
    config.NEWS_ENABLED = not args.no_news
    config.SEED = args.seed
    config.DEBUG = args.debug

    uvicorn.run(
        "bitcointrader.server.app:app",
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
