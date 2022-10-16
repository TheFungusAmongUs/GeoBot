import json
import toml
from pathlib import Path


def setup_toml() -> None:
    if Path('config/config.toml').exists():
        with open("config/config.toml", "r+") as file, open("config/base_config.toml", "r") as base_file:
            # Adds any extra fields from the base config file when updating the bot
            base_toml = toml.load(base_file)
            current_toml = toml.load(file)
            file.seek(0)
            file.truncate()
            toml.dump({**base_toml, **current_toml}, file)

    else:
        with open("config/config.toml", "w") as file, open("config/base_config.toml", "r") as base_file:
            toml.dump(toml.load(base_file), file)


data_files = ["posts.json", "tickets.json"]


def setup_data() -> None:
    for file in data_files:
        if not Path(f'data/{file}').exists():
            with open(f"data/{file}", "w") as data_file, open(f"data/base_{file}", "r") as base_file:
                json.dump(json.load(base_file), data_file)


if __name__ == "__main__":
    setup_data()
    setup_toml()
