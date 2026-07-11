import ast
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_CONFIG_PATH = Path("config/search_config.yaml")


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value in ("true", "false"):
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        return ast.literal_eval(value)
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _container_for_next(lines: List[str], index: int, indent: int) -> Any:
    for next_line in lines[index + 1 :]:
        if not next_line.strip() or next_line.lstrip().startswith("#"):
            continue
        next_indent = len(next_line) - len(next_line.lstrip(" "))
        if next_indent <= indent:
            return {}
        return [] if next_line.strip().startswith("- ") else {}
    return {}


def load_simple_yaml(path: Path) -> Dict[str, Any]:
    """Small YAML reader for this repo's config shape.

    It supports nested dictionaries, lists of scalars, and lists of dictionaries.
    Keeping this local avoids requiring PyYAML for the first manual run.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]
    last_key_at_indent: Dict[int, Tuple[Any, str]] = {}

    for index, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if not isinstance(parent, list):
                holder, key = last_key_at_indent[indent - 2]
                holder[key] = []
                parent = holder[key]
                stack.append((indent - 2, parent))
            scalar_item = item.startswith(("http://", "https://", '"http://', '"https://', "'http://", "'https://"))
            if ":" in item and not scalar_item:
                key, value = item.split(":", 1)
                entry = {key.strip(): _parse_scalar(value)}
                parent.append(entry)
                stack.append((indent, entry))
                last_key_at_indent[indent] = (entry, key.strip())
            else:
                parent.append(_parse_scalar(item))
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = _parse_scalar(value)
        else:
            parent[key] = _container_for_next(lines, index, indent)
        last_key_at_indent[indent] = (parent, key)
        if isinstance(parent[key], (dict, list)):
            stack.append((indent, parent[key]))

    return root


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    return load_simple_yaml(Path(path))
