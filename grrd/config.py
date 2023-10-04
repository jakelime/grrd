# config.py

# global libraries
import tomlkit
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Mapping
from utils import setup_logger

APP_NAME = "grrd"


class Config:
    cfg: Mapping

    def __init__(self, filepath: str = "") -> None:
        self.log = setup_logger(APP_NAME)
        self.cfg = self.load_toml()
        self.load_env_variables()

    def load_env_variables(self):
        load_dotenv()
        self.log.warning("environment var loading to be coded")

    def get_default_config_filepath(self) -> str:
        cwd = Path(__file__).parent
        bundles = cwd.parent / "bundles"
        config_filepath = bundles / "config.toml"
        if not config_filepath.is_file():
            raise RuntimeError("missing factory config file")
        return str(config_filepath.absolute())

    def load_toml(self, config_fp: str = "") -> Mapping:
        if config_fp:
            fp = Path(config_fp)
            if not fp.is_file():
                self.log.error(f"config file not found: {fp}")
                fp = Path(self.get_default_config_filepath())
        else:
            fp = Path(self.get_default_config_filepath())

        with open(fp, mode="rt", encoding="utf-8") as fp:
            self.cfg = tomlkit.load(fp)
        self.log.info("config loaded")
        return self.cfg


def pretty_print(d, n: int = 0, log=None):
    spaces = " " * n * 2
    for k, v in d.items():
        if isinstance(v, dict):
            if isinstance(log, logging.Logger):
                log.info(f"{spaces}{k}:")
            else:
                print(f"{spaces}{k}:")
            pretty_print(v, n=n + 1, log=log)
        else:
            try:
                if isinstance(log, logging.Logger):
                    log.info(f"{spaces}{k}: {v}")
                else:
                    print(f"{spaces}{k}: {v}")
            except AttributeError:
                # Happens when parsing toml (below is to handle tomlkit class)
                if isinstance(log, logging.Logger):
                    log.info(f"{spaces}{k=}, {v=}")
                else:
                    print(f"{spaces}{k=}, {v=}")


def main():
    c = Config()
    cfg = c.cfg
    # print(f"{c.bundles=}")
    pretty_print(cfg, log=c.log)
    # import pandas as pd

    # # print(cfg['grr_settings']['foms'])
    # df = pd.DataFrame(cfg['grr_settings']['foms'])
    # df["grr_usl"] = df['grr_limits'].apply(lambda x: x[0]).astype(float)
    # df["grr_lsl"] = df['grr_limits'].apply(lambda x: x[1]).astype(float)
    # print(df)
    # print(cfg)


if __name__ == "__main__":
    main()
