"""CLI entry point for sift-search."""

import argparse
import sys

from .indexer import build_index


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

    args = parser.parse_args()

    if args.command == "index":
        build_index(args.directory, args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
