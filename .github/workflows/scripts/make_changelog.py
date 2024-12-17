import os
import sys

# Changelog text
with open("pr_body.txt", encoding="utf-8") as fp:
    lines = fp.read().splitlines()

try:
    index = lines.index("## What's Changed")
except ValueError:
    print("PR message is malformed")
    sys.exit(1)

if index + 1 == len(lines):
    print("Changelog is empty")
    sys.exit(1)

with open(".github\\RELEASE_TEMPLATE", mode="a", encoding="utf-8") as fp:
    fp.write("\n".join(lines[index:]) + "\n")

# Version number
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fp:
    fp.write(f'version={os.environ.get("PR_TITLE", "").rsplit(" ", 1)[-1]}\n')
