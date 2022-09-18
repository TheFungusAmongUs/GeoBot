import toml
from typing import Any, MutableMapping, TextIO

toml_dict = MutableMapping[str, Any]


def write_toml(to_write: toml_dict, fp: TextIO) -> None:
    fp.seek(0)
    fp.truncate()
    toml.dump(to_write, fp)
