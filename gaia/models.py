# models.py is part of MODEL in the design framework

# global libraries
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Mapping

import numpy as np
import pandas as pd


# local libraries
from config import Config
import utils
from utils import get_time

APP_NAME = "gaia"
pd.options.mode.chained_assignment = None  # type: ignore


def dataframe_count_reps(
    df: pd.DataFrame, PART: str, OPERATOR: str, REP: str = "rep"
) -> pd.DataFrame:
    dfindexer = df.groupby(by=[PART, OPERATOR]).count().reset_index()
    index_cols = list(dfindexer.columns)
    index_cols[-1] = "count"
    dfindexer.columns = index_cols

    dflist = []
    for _, row in dfindexer.iterrows():
        df_ = df[(df[PART] == row[PART]) & (df[OPERATOR] == row[OPERATOR])].copy()
        df_.loc[:, REP] = np.arange(1, len(df_) + 1)
        dflist.append(df_)

    df = pd.concat(dflist)
    return df.reset_index(drop=True)


class ParamData:
    limits: pd.Series
    dfdata: pd.DataFrame

    def __init__(
        self,
        name: str,
        dfdata: pd.DataFrame,
        dslimits: pd.Series,
        grrlimits: pd.DataFrame,
    ):
        """Dataclass container for FOM data
        :param name: name of the parameter
        :type name: str
        :param dfdata: _description_
        :type dfdata: pd.DataFrame(columns=[OPERATOR, PART, VALUE])
        :param dslimit: _description_
        :type dslimit: pd.Series(index=[grr_limit, usl, lsl])
        :param grrlimits: grrlimits specified in user config file
        :type grrlimits: pd.DataFrame, optional
        """
        self.grrlimits = grrlimits
        self.name = name
        self.dfdata = dfdata
        self.limits = dslimits
        self.update_grr_limits()
        self.update_no_specs()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}( \n  limits: pd.Series,\n  dfdata: pd.DataFrame,\n  name={self.name},\n  shape={self.dfdata.shape})\n)"

    def update_grr_limits(self) -> None:
        if self.name in self.grrlimits.index:
            self.limits["grr_limit"] = self.grrlimits.loc[self.name, "grr_limit"]
        else:
            self.limits["grr_limit"] = np.nan

    def update_no_specs(self):
        for x in ["usl", "lsl"]:
            self.limits[x] = pd.to_numeric(self.limits[x], errors="coerce")
        if np.isnan(self.limits["lsl"]) and np.isnan(self.limits["usl"]):
            self.limits["is_no_testspecs"] = True
        else:
            self.limits["is_no_testspecs"] = False
        if np.isnan(self.limits["grr_limit"]):
            self.limits["is_no_grrspecs"] = True
        else:
            self.limits["is_no_grrspecs"] = False


class SpecsParser:
    df: pd.DataFrame = pd.DataFrame()

    def __init__(self, cfg: Mapping, filepath: Path | str) -> None:
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        if not filepath.is_file():
            raise RuntimeError(f"missing grr_config {filepath=}")
        self.log = utils.setup_logger(APP_NAME)
        self.cfg = cfg["input_settings"]["reading_format"]["grr_config_csv"]
        self.FOM = self.cfg["FOM"]
        self.GRR_LIMIT = self.cfg["GRR_LIMIT"]
        self.df = self.read_and_parse_data(filepath)
        self.log.debug(f"grrspecs loaded from {filepath.name}")
        print(f"{self.__class__.__name__}() done")

    def read_and_parse_data(self, fp: Path) -> pd.DataFrame:
        df = pd.read_csv(fp, skiprows=self.cfg["skip_rows"])
        df.rename(
            mapper={
                self.FOM: "fom",
                self.GRR_LIMIT: "grr_limit",
            },
            axis=1,
            inplace=True,
        )
        df = df[["fom", "grr_limit"]].set_index("fom")
        return df


class DataParser(ABC):
    """Abstract class to create a data parser"""

    def __init__(self, cfg: Mapping, filepaths: list[Path | str] = []) -> None:
        self.log = utils.setup_logger(APP_NAME)
        self.cfg = cfg
        VARS = cfg["input_settings"]["variable_names"]
        self.OPERATOR = VARS["OPERATOR"]
        self.PART = VARS["PART"]
        self.USL = VARS["USL"]
        self.LSL = VARS["LSL"]
        self.UNITS = VARS["UNITS"]
        self.TIMESTAMP = VARS["TIMESTAMP"]
        self.REP = VARS["REP"]
        self.VALUE = VARS["VALUE"]
        self.file_info = ""
        self.datastore = []
        self.dfdata = pd.DataFrame()
        self.dfheaders = pd.DataFrame()

        try:
            # grr_config_csv_filepath
            specs = SpecsParser(
                cfg=cfg,
                filepath=cfg["general"]["grr_config_csv_filepath"],
            )
            self.cfg_grrlimits = specs.df
        except Exception as e:
            raise utils.ConfigError(f"error parsing grr_limits; {e}")

        if filepaths:
            self.log.debug(f"parsing {len(filepaths)} files ...")
            counter = 0
            dflist_data, dflist_headers = [], []

            for fp in filepaths:
                dfdata, dfheaders = self.read_data(fp)
                dflist_data.append(dfdata)
                dflist_headers.append(dfheaders)
                counter += 1

            if counter == 1:
                self.file_info = Path(filepaths[0]).name
            elif counter > 1:
                self.file_info = "multiple_files"
            else:
                self.file_info = "file_info_err"

            dfdata = pd.concat(dflist_data)
            dfheaders = pd.DataFrame()
            for i, df in enumerate(dflist_headers):
                if i == 0:
                    dfheaders = df.copy()
                    continue
                dfheaders = dfheaders.compare(df, keep_shape=True, keep_equal=True)

            self.dfdata = dfdata
            self.dfheaders = dfheaders
            self.log.debug(f"{counter} file(s) parsed successfully")

    def get_fixed_columns(self) -> list[str]:
        cols = [self.OPERATOR, self.PART]
        if self.TIMESTAMP:
            cols.append(self.TIMESTAMP)
        return cols

    def get_param_columns(self, all_columns: list[str]) -> list[str]:
        cols = [x for x in all_columns if x not in self.fixed_columns]
        return cols

    def read_data(self, filepath: Path | str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """IO: Read data from CSV file,
        extracting datatable as dfdata and headerstable as dfheaders

        :param filepath: input filepath
        :type filepath: Path | str
        :return: (dfdata, dfheaders)
        :rtype: tuple[pd.DataFrame, pd.DataFrame]
        """
        cfg_data = self.cfg["input_settings"]["reading_format"]["data"]
        df = pd.read_csv(filepath, skiprows=cfg_data["skip_rows"])
        dfdata = df.copy()

        cfg_headers = self.cfg["input_settings"]["reading_format"]["headers"]
        df = pd.read_csv(
            filepath,
            header=cfg_headers["header_row"],
            nrows=cfg_headers["nrows"],
        )
        df["index"] = df[df.columns[0]].copy()
        replacement_dict = {
            self.cfg["input_settings"]["variable_names"]["LSL"]: "lsl",
            self.cfg["input_settings"]["variable_names"]["USL"]: "usl",
            self.cfg["input_settings"]["variable_names"]["UNITS"]: "units",
        }
        df["index"].replace(replacement_dict, inplace=True)
        df.set_index("index", inplace=True)
        dfheaders = df.copy()
        return (dfdata, dfheaders)

    @abstractmethod
    def parse_data(self, dfin: pd.DataFrame, dfheaders: pd.DataFrame) -> None:
        pass

    def export_data(
        self, outdir: Optional[Path] = None, outname: str = "exported.csv"
    ) -> None:

        if not outdir:
            outdir = self.cfg["general"]["system_working_dir"]
        outname, filetype = outname.split(".")
        outpath = outdir / f"{outname}-{get_time()}.{filetype}"  # type: ignore

        match filetype:
            case "csv":
                self.df.to_csv(outpath)
            case "parquet":
                self.df.to_parquet(outpath)
            case "_":
                raise RuntimeError(f"unaccepted {(outname, filetype)=}")

        self.log.info(f"file saved {outpath.name}")


class StandardParser(DataParser):
    def __init__(self, cfg: Mapping, filepaths: list[Path | str] = []) -> None:
        super().__init__(cfg, filepaths)
        self.datastore = self.parse_data(self.dfdata, self.dfheaders)
        print(f"{self.__class__.__name__}() done")

    def parse_data(
        self, dfdata: pd.DataFrame, dfheaders: pd.DataFrame
    ) -> list[ParamData]:
        PART = self.PART
        OPERATOR = self.OPERATOR
        VALUE = self.VALUE
        REP = self.REP
        cfg = self.cfg["grr_settings"]
        df = dfdata.copy()
        numeric_cols = set(dfdata.select_dtypes(include="number").columns)
        descriptive_cols = set([c for c in dfdata.columns if c not in numeric_cols])
        if OPERATOR not in descriptive_cols:
            raise RuntimeError(f"column {OPERATOR=} not in dataframe")
        if PART not in descriptive_cols:
            raise RuntimeError(f"column {PART=} not in dataframe")

        if self.TIMESTAMP in df.columns:
            df.sort_values(by=self.TIMESTAMP, ascending=True, inplace=True)
            df.reset_index(inplace=True)

        if cfg["list_of_foms"]:
            numeric_cols_ = numeric_cols.intersection(set(cfg["list_of_foms"]))
            if not numeric_cols_:
                self.log.error("list_of_foms is specified, but nothing found!")
                [self.log.error(f"  NOT found -> {x}") for x in cfg["list_of_foms"]]
            else:
                numeric_cols = numeric_cols_

        if cfg["list_of_excluded_foms"]:
            numeric_cols = numeric_cols.difference(set(cfg["list_of_excluded_foms"]))

        datastore = []
        fixed_cols = [PART, OPERATOR]
        n = len(numeric_cols)
        for i, fom in enumerate(numeric_cols, 1):
            self.log.debug(f"  [{i}/{n}] processing {fom} to ParamData ...")
            cols = fixed_cols + [fom]
            dffom = df[cols]
            cols_ = list(dffom.columns)
            cols_[-1] = VALUE
            dffom.columns = cols_
            dffom = dataframe_count_reps(
                dffom,
                PART=PART,
                OPERATOR=OPERATOR,
                REP=REP,
            )
            datastore.append(
                ParamData(
                    name=fom,
                    dfdata=dffom,
                    dslimits=dfheaders.loc[:, fom],  # type: ignore
                    grrlimits=self.cfg_grrlimits,
                )
            )
        return datastore

    def __str__(self):
        return f"{self.__class__.__name__}(\n  file_info={self.file_info},\n  x{len(self.datastore)} params)"


def main():
    cfg = Config().cfg
    specs_file = "/Users/jli8/activedir/gaiaweb/resources/grrConfig.csv"
    target_file = "/Users/jli8/activedir/gaiaweb/resources/project1-di-cleaned.csv"
    # target_file = "/Users/jli8/activedir/gaiaweb/resources/project2-sh-cleaned.csv"
    cfg["general"]["grr_config_csv_filepath"] = specs_file
    specs = SpecsParser(
        cfg=cfg,
        filepath=specs_file,
    )
    data = StandardParser(cfg=cfg, filepaths=[target_file])
    # plot_data = views.GaiaDataMaker(
    #     cfg=cfg,
    #     dataparam_list=data.datastore,
    #     dflimits=specs.df,
    # )
    # views.run_plotly(plot_data.dfs, port=str(PORT))


if __name__ == "__main__":
    pd.set_option("display.max_rows", 10)
    pd.set_option("display.max_columns", 5)
    pd.set_option("display.width", 200)
    main()
