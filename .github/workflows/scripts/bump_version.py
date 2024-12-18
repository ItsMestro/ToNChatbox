import os
import re
import sys


def repl(match: re.Match[str]) -> str:
    new_version = os.environ.get("NEW_VERSION", "")
    return f'_VERSION = "{new_version}"'


with open("ton_chatbox.py", encoding="utf-8") as fp:
    new_contents, found = re.subn(
        pattern=r'^_VERSION = "(?P<version>[^"]*)"$',
        repl=repl,
        string=fp.read(),
        count=1,
        flags=re.MULTILINE,
    )

if not found:
    print("Couldn't find `_VERSION` line!")
    sys.exit(1)

with open("ton_chatbox.py", "w", encoding="utf-8", newline="\n") as fp:
    fp.write(new_contents)
