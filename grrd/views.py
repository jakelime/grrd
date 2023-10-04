# views.py is part of VIEW in the design framework
# Responsible for generating different analysis views

# global libraries
from typing import Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table

# local libraries
import utils
import models
from config import Config

APP_NAME = "grrd"
PART = "SerialNumber"  # CRITICAL to be fixed! make this a variable instead..
log = utils.setup_logger(APP_NAME)


@dataclass
class GaiaData:
    fom: str
    operator: str
    df: pd.DataFrame
    df_condensed: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    grr_passed: bool = False  # True: pass, False: fail or error
    grr_limits: float = float("inf")

    def __str__(self) -> str:
        parts_failed = len(self.df) - self.df["grr_part_passed"].sum()
        return f"{self.__class__.__name__}(fom={self.fom}, passed={self.grr_passed}, operator={self.operator}, {parts_failed=}, df.shape={self.df.shape})"


class GaiaDataMaker:
    def __init__(
        self,
        cfg: Mapping,
        dataparam_list: list[models.ParamData],
        dflimits: pd.DataFrame,
    ) -> None:
        self.log = utils.setup_logger(APP_NAME)
        VARS = cfg["input_settings"]["variable_names"]
        self.OPERATOR = VARS["OPERATOR"]
        self.PART = VARS["PART"]
        self.USL = "usl"
        self.LSL = "lsl"
        self.UNITS = "units"
        self.REP = "rep"
        self.VALUE = "value"
        self.dflimits = dflimits
        self.is_pseudo_golden = True
        self.gaiadata_store = []
        n = len(dataparam_list)
        for i, dataparam in enumerate(dataparam_list, 1):
            self.log.debug(f"  [{i}/{n}] breaking down into operators")
            self.breakdown_to_sockets(dataparam)
        n = len(self.gaiadata_store)
        for i, data in enumerate(self.gaiadata_store, 1):
            self.log.debug(f"  [{i}/{n}] computing grr_status")
            self.compute_grr_status(data)

        # Special df that contains nested dataframes
        df = pd.DataFrame(self.gaiadata_store)
        self.df_summary = df[["fom", "operator", "grr_passed", "grr_limits"]]
        self.dfs = self.compile_dfs(self.gaiadata_store)

    def __str__(self):
        number_of_datatables = len(self.gaiadata_store)
        return f"{self.__class__.__name__}(datastore: n={number_of_datatables})"

    def transform_data(
        self, dfin: pd.DataFrame, operator: str, is_golden: bool = False
    ) -> pd.DataFrame:
        if not operator and is_golden:
            # Pseudo-golden mode. Take average of everything
            df = dfin
        else:
            df = dfin[dfin[self.OPERATOR] == operator]

        # outname = f"output-{self.data.name}-{self.OPERATOR}.csv"
        # df.to_csv(outname)
        dfp = pd.pivot_table(
            data=df,
            index=self.PART,
            values=self.VALUE,
            aggfunc=["mean", "count", "min", "max"],
        ).reset_index()
        dfp.columns = dfp.columns.map("_".join).str.strip("_")
        if is_golden:
            dfp.set_index(self.PART, inplace=True)
            dfp.columns = dfp.columns.map(lambda x: f"golden_{x}")
            dfp.reset_index(inplace=True)
        # return PlotData(operator=operator, df=dfp)
        return dfp

    def breakdown_to_sockets(self, paramdata: models.ParamData) -> None:
        operators = paramdata.dfdata[self.OPERATOR].unique()
        is_golden_socket = [
            True if ("_gold" in op.lower()) else False for op in operators
        ]
        match golden_operator_count := sum(is_golden_socket):
            case 0:
                self.is_pseudo_golden = True
                self.golden_operator = ""
            case 1:
                self.is_pseudo_golden = False
                self.golden_operator = operators[is_golden_socket.index(True)]
            case _:
                raise RuntimeError(
                    f"more than 1 golden operator, found ({golden_operator_count=})"
                )

        if self.is_pseudo_golden:
            dfgolden = self.transform_data(
                paramdata.dfdata, self.golden_operator, is_golden=False
            )
        else:
            dfgolden = self.transform_data(
                paramdata.dfdata, self.golden_operator, is_golden=True
            )

        for operator in operators:
            dftarget = self.transform_data(paramdata.dfdata, operator, is_golden=False)
            df = pd.merge(left=dfgolden, right=dftarget, on=self.PART, how="outer")
            df = self.compute_grr_pct(df, limits=paramdata.limits, fom=paramdata.name)
            self.gaiadata_store.append(
                GaiaData(
                    fom=paramdata.name,
                    operator=operator,
                    df=df,
                    grr_limits=paramdata.limits["grr_limit"],
                )
            )

    def compute_grr_pct(
        self, dfin: pd.DataFrame, limits: pd.Series, fom: str
    ) -> pd.DataFrame:
        df = dfin
        df["grr_limits"] = limits["grr_limit"]
        df["grr_mean_offset"] = df["mean_value"] - df["golden_mean_value"]
        df["grr_pos_offset"] = abs(df["max_value"] - df["golden_mean_value"])
        df["grr_neg_offset"] = abs(df["min_value"] - df["golden_mean_value"])
        df["grr_high_pct"] = df["grr_pos_offset"] / df["grr_limits"] * 100
        df["grr_low_pct"] = df["grr_neg_offset"] / df["grr_limits"] * 100
        return df

    def compute_grr_status(self, gaiadata: GaiaData) -> GaiaData:
        # computes grr status and updates GaiaData object in place
        gaiadata.df["grr_part_passed"] = (gaiadata.df["grr_high_pct"] < 100) & (
            gaiadata.df["grr_low_pct"] < 100
        )
        df = gaiadata.df[
            [
                "SerialNumber",
                "mean_value",
                "golden_mean_value",
                "grr_mean_offset",
                "grr_limits",
                "grr_pos_offset",
                "grr_neg_offset",
                "grr_high_pct",
                "grr_low_pct",
                "grr_part_passed",
            ]
        ]

        gaiadata.df_condensed = df
        gaiadata.grr_passed = df["grr_part_passed"].all()

        return gaiadata

    def compile_dfs(self, datalist: list[GaiaData]) -> pd.DataFrame:
        # compile a huge dataframe to send to plotly
        dflist = []
        for data in datalist:
            df = data.df_condensed
            df["fom"] = data.fom
            df["operator"] = data.operator
            dflist.append(df)
        return pd.concat(dflist)

    def pretty_print(self, dfin: pd.DataFrame, name: str) -> None:
        df = dfin[
            [
                self.PART,
                "mean_value",
                "golden_mean_value",
                "grr_mean_offset",
                "grr_high_pct",
                "grr_low_pct",
            ]
        ]
        print(f"{name=}\n{df}")


def plot_overlay(
    fig: go.Figure,
    df: pd.DataFrame,
    scale_factor: float = 1.2,
    grr_limits: float = 0.0,
) -> tuple[float, float]:
    try:
        grr_limits = df.loc[df.index[0], "grr_limits"]
    except Exception:
        log.debug(f"failed to get grr_limits df=\n{df}")
        grr_limits = 0
    finally:
        if np.isnan(grr_limits):
            grr_limits = 0

    xmin, xmax = (
        min(
            df["golden_mean_value"].min() - grr_limits,
            df["mean_value"].min() - grr_limits,
        ),
        max(
            df["golden_mean_value"].max() + grr_limits,
            df["mean_value"].max() + grr_limits,
        ),
    )

    plotrange = xmax - xmin
    xmin, xmax = (
        xmin - (plotrange / 2 * scale_factor),
        xmax + (plotrange / 2 * scale_factor),
    )

    xvalues = np.linspace(xmin, xmax, 3)

    fig.add_trace(
        go.Scatter(
            x=xvalues,
            y=xvalues,
            mode="lines",
            name="centerline",
            hoverinfo="skip",
            line=dict(color="darkgrey"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=xvalues,
            y=[x + grr_limits for x in xvalues],
            mode="lines",
            name="grr_upper_limit",
            line=dict(color="darkgrey", dash="dot"),
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xvalues,
            y=[x - grr_limits for x in xvalues],
            mode="lines",
            name="grr_lower_limit",
            line=dict(color="darkgrey", dash="dot"),
            hoverinfo="skip",
        )
    )

    return xmin, xmax


def run_plotly(df: pd.DataFrame, port: str = "8501") -> None:
    # app = Dash(APP_NAME)
    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    app = Dash(
        APP_NAME,
        external_stylesheets=external_stylesheets,
        routes_pathname_prefix="/grrd/",
        requests_pathname_prefix="/grrd/",
    )
    operators = list(df["operator"].unique())
    foms = list(df["fom"].unique())
    app.layout = html.Div(
        [
            html.H4("GR&R Dashboard App"),
            dcc.Graph(id="scatter-plot"),
            html.P("Filter by FOM"),
            dcc.Dropdown(id="foms-dropdown", options=foms, value=foms[0]),
            html.P("Filter by operator"),
            dcc.Dropdown(id="operator-dropdown", options=operators, value=operators[0]),
            html.P("Datatable:"),
            html.Div(id="datatable"),
        ]
    )

    @app.callback(
        Output("datatable", "children"),
        Input("operator-dropdown", "value"),
        Input("foms-dropdown", "value"),
    )
    def update_datatable(operator, fom):

        dfmasked = df[(df["operator"] == operator) & (df["fom"] == fom)]
        dftable = dfmasked[
            [
                PART,
                "grr_part_passed",
                "mean_value",
                "grr_mean_offset",
                "grr_high_pct",
                "grr_low_pct",
                "grr_pos_offset",
                "grr_neg_offset",
            ]
        ].dropna()

        grr_status = "error"

        grr_limits = "error"
        try:
            grr_limits = dfmasked.loc[dfmasked.index[0], "grr_limits"]
            grr_limits = f"{grr_limits:.4g}"
        except Exception as e:
            log.error(e)

        grr_score = "error"
        try:
            grr_score = max(
                dfmasked["grr_low_pct"].max(), dfmasked["grr_high_pct"].max()
            )
            if grr_score <= 100:
                grr_status = "PASS"
            else:
                grr_status = "FAIL"
            grr_score = f"{grr_score:.2f}%"
        except Exception as e:
            log.error(e)

        foms = ";".join(dfmasked["fom"].unique())
        operators = ";".join(dfmasked["operator"].unique())
        markdown_text = f"""
        ### GRR Results
        - fom = {foms}
        - operator = {operators}
        - grr_status = {grr_status}
        - grr_limits = {grr_limits}
        - grr_score = {grr_score}
        """

        return html.Div(
            [
                html.Div(
                    [dcc.Markdown(markdown_text)],
                    style={
                        "margin": "10px",
                    },
                ),
                dash_table.DataTable(
                    dftable.to_dict("records"),
                    [{"name": i, "id": i} for i in dftable.columns],
                ),
            ]
        )

    @app.callback(
        Output("scatter-plot", "figure"),
        Input("operator-dropdown", "value"),
        Input("foms-dropdown", "value"),
    )
    def update_scatterplot(operator, fom):

        dfmasked = df[(df["operator"] == operator) & (df["fom"] == fom)]
        fig = go.Figure()

        # Add traces
        parts = dfmasked[PART].unique()
        for part in parts:
            df_ = dfmasked[dfmasked[PART] == part]
            fig.add_trace(
                go.Scatter(
                    x=df_["golden_mean_value"],
                    y=df_["mean_value"],
                    mode="markers",
                    name=f"{part}",
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=df_["grr_pos_offset"],
                        arrayminus=df_["grr_neg_offset"],
                    ),
                )
            )
        xmin, xmax = plot_overlay(fig, dfmasked)

        fig.update_xaxes(range=[xmin, xmax])
        fig.update_yaxes(range=[xmin, xmax])
        fig.update_layout(width=800, height=500)

        # dfmasked.to_csv(f"output-{utils.get_time()}.csv")
        return fig

    app.run(debug=True, host="0.0.0.0", port=port)


def main():

    cfg = Config().cfg
    specs = models.SpecsParser(
        cfg=cfg,
        filepath="/Users/jli8/activedir/grrd/resources/gaia_config.csv",
    )
    data = models.StandardParser(
        cfg=cfg,
        filepaths=[
            "/Users/jli8/activedir/grrd/resources/sample_files/samplecsv-cleaned_gaia.csv"
        ],
    )
    plot_data = GaiaDataMaker(cfg=cfg, dataparam_list=data.datastore, dflimits=specs.df)
    run_plotly(plot_data.dfs)


if __name__ == "__main__":
    main()
