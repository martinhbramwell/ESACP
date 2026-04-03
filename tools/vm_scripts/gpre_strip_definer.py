"""G-pre: Strip DEFINER clauses from a MariaDB backup archive.

Replaces `DEFINER=<user>@<host>` with `DEFINER=CURRENT_USER` in the SQL
dump inside a .tgz backup archive. Operates in-place on the archive.

Usage (on target VM):
    python3 /tmp/vm_scripts/gpre_strip_definer.py \
        --bench-dir /home/erpadm/frappe-bench-D2IRBL
"""

import argparse
import gzip
import re
import shutil
import tarfile
import tempfile
from pathlib import Path

DEFINER_RE = re.compile(rb"DEFINER=[^ ]*")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bench-dir", required=True,
                        help="Bench directory path")
    args = parser.parse_args()

    bench = Path(args.bench_dir)
    backup_name = (bench / "BKP" / "BACKUP.txt").read_text().strip()
    archive_path = bench / "BKP" / backup_name
    sql_entry = backup_name.removesuffix(".tgz") + "-database.sql.gz"

    work_dir = Path(tempfile.mkdtemp(prefix="_definer_strip_"))
    try:
        # Extract archive
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(work_dir)

        sql_gz_path = work_dir / sql_entry

        # Decompress, replace, recompress
        with gzip.open(sql_gz_path, "rb") as f:
            sql_data = f.read()

        count = len(DEFINER_RE.findall(sql_data))
        sql_data = DEFINER_RE.sub(b"DEFINER=CURRENT_USER", sql_data)

        with gzip.open(sql_gz_path, "wb") as f:
            f.write(sql_data)

        # Repack archive
        with tarfile.open(archive_path, "w:gz") as tf:
            for item in work_dir.iterdir():
                tf.add(item, arcname=item.name)

        print(f"  [OK] Replaced {count} DEFINER clauses in {sql_entry}")
    finally:
        shutil.rmtree(work_dir)


if __name__ == "__main__":
    main()
