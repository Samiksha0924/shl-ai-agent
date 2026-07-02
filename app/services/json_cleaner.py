import re
from pathlib import Path


class JsonCleaner:
    """
    Repairs common issues found in the SHL catalog JSON.
    """

    @staticmethod
    def clean(path: Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # Fix multiline values like:
        # "name": "Microsoft
        # 365 (New)"
        pattern = r'("name"\s*:\s*")([^"]*?)\n([^"]*?)(")'

        while re.search(pattern, text, flags=re.MULTILINE):
            text = re.sub(
                pattern,
                lambda m: f'{m.group(1)}{m.group(2)} {m.group(3)}{m.group(4)}',
                text,
                flags=re.MULTILINE,
            )

        return text