#!/usr/bin/env python
"""Database seeding runner - choose dev or demo data."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seed_dev import seed_development
from seed_demo import seed_demo


def main():
    parser = argparse.ArgumentParser(
        description="Seed the GPT-CRM database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed.py              # dev data (default)
  python scripts/seed.py --type demo  # rich demo data
  python scripts/seed.py --type all   # both
  python scripts/seed.py --force      # skip production guard
        """
    )
    parser.add_argument(
        "--type",
        choices=["dev", "demo", "all"],
        default="dev",
        help="Type of seed data to generate (default: dev)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip production safety check"
    )

    args = parser.parse_args()

    if args.type in ("dev", "all"):
        seed_development(force=args.force)

    if args.type in ("demo", "all"):
        if args.type == "all":
            print()
        seed_demo(force=args.force)


if __name__ == "__main__":
    main()
