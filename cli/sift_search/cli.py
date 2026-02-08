"""CLI entry point for sift-search."""

import argparse
import sys

from .indexer import build_index
from .doctor import run_doctor


def main():
    parser = argparse.ArgumentParser(
        prog="sift",
        description="Semantic search for static sites",
    )
    sub = parser.add_subparsers(dest="command")

    idx = sub.add_parser("index", help="Index markdown content into sift-index.db")
    idx.add_argument("directory", help="Path to directory containing .md files")
    idx.add_argument(
        "-o", "--output", default="sift-index.db", help="Output database path"
    )

    doc = sub.add_parser("doctor", help="Validate sift setup and index file")
    doc.add_argument(
        "index", nargs="?", default="sift-index.db", help="Path to index file"
    )

    args = parser.parse_args()

    if args.command == "index":
        build_index(args.directory, args.output)
    elif args.command == "doctor":
        run_doctor(args.index)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
