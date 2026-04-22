#!/usr/bin/env python3
"""Write fresh OAuth tokens to all mcp-remote version dirs.

Invoked by tools/cf-mcp-refresh after a successful refresh_token exchange.
Reads the new token JSON from stdin; mcp_auth_dir + url_hash via argv.
Replaces a bash heredoc that fed Python through three escaping layers (#276).
"""
import glob
import json
import os
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: cf-mcp-write-tokens.py <mcp_auth_dir> <url_hash>",
            file=sys.stderr,
        )
        return 2

    mcp_auth_dir, url_hash = sys.argv[1], sys.argv[2]
    new_tokens = json.load(sys.stdin)

    pattern = os.path.join(mcp_auth_dir, f"mcp-remote-*/{url_hash}_tokens.json")
    written = 0
    for path in glob.glob(pattern):
        with open(path, "w") as fh:
            json.dump(new_tokens, fh, indent=2)
        written += 1

    print(f"cf-mcp-refresh: ✅ token refreshed and written to {written} version dir(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
