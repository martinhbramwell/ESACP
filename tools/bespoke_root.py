"""Root directory for sibling bespoke-app checkouts (ce_sri, BaRe, returnable, etc.).

Override via the BESPOKE_ROOT env var; default assumes the convention
`~/projects/bespoke-apps -> <wherever-your-checkouts-live>` (symlink or real dir).
"""

import os
from pathlib import Path

BESPOKE_ROOT = Path(
    os.environ.get("BESPOKE_ROOT", Path.home() / "projects" / "bespoke-apps")
)
