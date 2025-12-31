#!/usr/bin/env python3
"""Entry point para o web dashboard da Luna."""

import argparse

from src.web.server import run_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Luna Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host para bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Porta (default: 8080)")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
