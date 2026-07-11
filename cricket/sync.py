import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .storage import DB_PATH


def sync_run_outputs(config: Dict, paths: Iterable[Path]) -> Tuple[List[str], List[str]]:
    data_store = config.get("data_store", {})
    if not data_store.get("sync_on_report", False):
        return [], []

    root_value = data_store.get("windows_root")
    if not root_value:
        return [], ["data_store.windows_root is not configured"]

    root = Path(root_value)
    synced: List[str] = []
    errors: List[str] = []
    for path in list(paths) + [DB_PATH]:
        source = Path(path)
        if not source.exists():
            errors.append("%s does not exist" % source)
            continue
        destination = root / source
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            synced.append(str(destination))
        except OSError as exc:
            errors.append("%s -> %s: %s" % (source, destination, exc))
    return synced, errors
