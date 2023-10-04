from typing import Mapping
from pathlib import Path

import config
import views
import models
import platform

APP_NAME = "grrd"


def start_flask_error_dev(
    exc: Exception = Exception("Unknown error"),
    port: int = 8000,
):
    from flask import Flask

    error_template = f"""<html>
    <h1>ERROR: Unable to start {APP_NAME} app</h1>
    <h4>Details:</h4>
    <b>{repr(exc)}</b>
    </html>"""

    app = Flask(APP_NAME)

    @app.route("/")
    def index():
        return error_template

    app.run(host="0.0.0.0", port=port)


def start_flask_error_server(
    exc: Exception = Exception("Unknown error"),
    port: int = 8000,
):
    from flask import Flask, Blueprint

    bp = Blueprint(APP_NAME, APP_NAME)

    error_template = f"""<html>
    <h1>ERROR: Unable to start {APP_NAME} app</h1>
    <h4>Details:</h4>
    <b>{repr(exc)}</b>
    </html>"""

    @bp.route("/")
    def index():
        return error_template

    app = Flask(APP_NAME)
    app.register_blueprint(bp, url_prefix="/grrd")
    app.run(host="0.0.0.0", port=port)


def load_filepaths() -> tuple[Mapping, str, str]:
    """initialises the cfg and filepath variables by based on machines"""
    cfg = config.Config().cfg

    cwd = Path(__file__).parent.parent
    user_dir = cwd / "targetdir"
    
    if not user_dir.is_dir():
        raise RuntimeError(f"unable to load {user_dir=}")

    specs_files = [fp for fp in user_dir.glob("*grr[cC]onfig.csv")]
    if not specs_files:
        raise Exception(f"no specs. check {user_dir}")
    specs_file = specs_files[0]
    cfg["general"]["grr_config_csv_filepath"] = str(specs_file.resolve())

    target_files = [
        fp for fp in user_dir.glob("*.csv") if "grrconfig" not in fp.name.lower()
    ]
    target_file = None
    match len(target_files):
        case 0:
            raise Exception(f"no *.csv files. check {user_dir}")
        case 1:
            target_file = target_files[0]
        case _:
            raise Exception(f"only 1 *.csv file is support for now. check {user_dir}")

    return (
        cfg,
        cfg["general"]["grr_config_csv_filepath"],
        str(target_file.resolve()),
    )


def main():

    PORT = 8501

    try:
        cfg, specs_file, target_file = load_filepaths()
        specs = models.SpecsParser(
            cfg=cfg,
            filepath=specs_file,
        )
        data = models.StandardParser(cfg=cfg, filepaths=[target_file])
        plot_data = views.GaiaDataMaker(
            cfg=cfg,
            dataparam_list=data.datastore,
            dflimits=specs.df,
        )
        views.run_plotly(plot_data.dfs, port=str(PORT))

    except Exception as e:

        match platform.system():
            case "Darwin":
                start_flask_error_dev(e, port=PORT)
            case "Linux":
                start_flask_error_server(e, port=PORT)
            case _:
                raise NotImplementedError()


if __name__ == "__main__":
    main()
