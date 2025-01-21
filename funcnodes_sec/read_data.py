from typing import List, Tuple
import numpy as np
import pandas as pd
import funcnodes as fn
import json
import lmfit
from io import StringIO


def read_file_lines(data: bytes) -> List[str]:
    lines = [
        line.lstrip(" ") + "\n"
        for line in data.decode("ISO-8859-1").splitlines(keepends=False)
    ]
    return lines


def process_sec_file(lines: List[str]) -> Tuple[dict, List[int]]:
    skipRows = []
    clmLines = []
    skipFooters = []
    blockKeys = []
    corrected_lines = []
    dfTotal = {}

    for lineNr, lineContext in enumerate(lines):
        if "\t\n" not in lineContext:
            lineContext = lineContext.replace("\n", "\t\n")
        if "start" in lineContext and len(lineContext.split(" ")) == 2:
            skipRows.append(lineNr)
            clmLines.append(lineNr + 1)
            blockKeys.append(lineContext.split("start")[0])
        elif "stop" in lineContext and len(lineContext.split(" ")) == 2:
            skipFooters.append(lineNr)
        corrected_lines.append(lineContext)
    for index, key in enumerate(blockKeys):
        lines = "".join(corrected_lines[clmLines[index] : skipFooters[index]])
        fileString = StringIO(lines)
        df = (
            pd.read_csv(
                fileString,
                sep="\t",
                encoding="ISO-8859-1",
                index_col=False,
                thousands=",",
                decimal=".",
            )
            .dropna(axis=1, how="all")
            .dropna(axis=0, how="all")
        )
        dfTotal[key] = df.to_json(orient="split")

    return dfTotal, clmLines


def arrayColumn(arr, n):
    return list(map(lambda x: x[n], arr))


def extract_metadata(lines: list, clmLine: int) -> pd.DataFrame:
    meta_lines = "".join(lines[:clmLine]).replace("\t", "")
    metadata_dict = {}
    for line in meta_lines.split("\n"):
        key_val = line.split(":", 1)
        if len(key_val) == 2:
            key = key_val[0].strip()
            val = key_val[1].strip()
            if key != "" and val != "":
                metadata_dict[key] = [val]
    metadata_df = pd.DataFrame.from_dict(metadata_dict)
    return metadata_df


def read_sec_from_bytes(data: bytes) -> Tuple[dict, pd.DataFrame]:
    lines = read_file_lines(data)
    data_dict, clmLines = process_sec_file(lines)
    metadata_df = extract_metadata(lines, clmLines[0])
    # print(data_dict['RAW'].keys())
    return data_dict, metadata_df


@fn.NodeDecorator(
    node_id="fnsec.data.readfrombytes",
    name="SEC from Bytes",
    inputs=[
        {"name": "sec_data", "dtype": "bytes"},
        {"name": "molarmass_min", "dtype": "int"},
        {"name": "molarmass_max", "dtype": "int"},
    ],
    description="Retrieve the SEC data from WinGPC system file.",
    outputs=[
        {"name": "signal", "dtype": "np.ndarray"},
        {"name": "mass", "dtype": "np.ndarray"},
        {"name": "sigma", "dtype": "np.ndarray"},
        {"name": "volume", "dtype": "np.ndarray"},
        {"name": "time", "dtype": "np.ndarray"},
        {"name": "mass_f", "dtype": "np.ndarray"},
        {"name": "df"},
    ],
)
def retrieve_data(
    sec_data: bytes, molarmass_min: int, molarmass_max: int
) -> Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame
]:
    # fitting_degree = int(metadata["Fit"][0].strip().split(" ")[-1])
    # fitting = metadata["Fit"][0].strip().split(" ")[0]
    data, metadata = read_sec_from_bytes(sec_data)
    const = float(metadata["Const."][0].strip())
    coef2 = float(metadata["Coef.2"][0].strip())
    coef3 = float(metadata["Coef.3"][0].strip())
    coef4 = float(metadata["Coef.4"][0].strip())
    coef5 = float(metadata["Coef.5"][0].strip())
    coef6 = float(metadata["Coef.6"][0].strip())
    coef7 = float(metadata["Coef.7"][0].strip())
    # coef8 = float(metadata["Coef.8"][0].strip())

    flow = float(metadata["Flow"][0].split("ml")[0].strip())
    raw_signal_column_name = [
        clm for clm in json.loads(data["RAW"])["columns"] if "RI" in clm
    ][0]

    rawSignal = np.array(
        arrayColumn(
            json.loads(data["RAW"])["data"],
            json.loads(data["RAW"])["columns"].index(raw_signal_column_name),
        )
    )

    if "Volume" in json.loads(data["RAW"])["columns"]:
        volume = np.array(
            arrayColumn(
                json.loads(data["RAW"])["data"],
                json.loads(data["RAW"])["columns"].index("Volume"),
            )
        )
        measurement_time = volume / flow
    else:
        measurement_time = np.array(
            arrayColumn(
                json.loads(data["RAW"])["data"],
                json.loads(data["RAW"])["columns"].index("Time"),
            )
        )
        volume = measurement_time * flow

    f = lmfit.models.__dict__["lmfit_models"]["Polynomial"](prefix="polynomial")
    sigma = -f.func(x=volume, c0=coef2, c1=2 * coef3, c2=3 * coef4)
    masses = 10 ** f.func(
        x=volume, c0=const, c1=coef2, c2=coef3, c3=coef4, c4=coef5, c5=coef6, c6=coef7
    )
    Signal_norm_0_to_1 = (rawSignal - np.amin(rawSignal)) / (
        np.amax(rawSignal) - np.amin(rawSignal)
    )
    mass_f = Signal_norm_0_to_1 / (masses * sigma)

    minIndex = np.abs(masses - molarmass_max).argmin()
    maxIndex = np.abs(masses - molarmass_min).argmin()

    SelectedSignal = rawSignal[minIndex:maxIndex]
    SelectedMass = masses[minIndex:maxIndex]
    SelectedSigma = sigma[minIndex:maxIndex]
    SelectedVolume = volume[minIndex:maxIndex]
    SelectedTime = measurement_time[minIndex:maxIndex]
    SelectedMassFraction = mass_f[minIndex:maxIndex]

    df = pd.DataFrame(
        {
            "Signal": SelectedSignal,
            "Mass": SelectedMass,
            "Sigma": SelectedSigma,
            "Volume": SelectedVolume,
            "Time": SelectedTime,
            "Mass_f": SelectedMassFraction,
        }
    )

    return (
        SelectedSignal,
        SelectedMass,
        SelectedSigma,
        SelectedVolume,
        SelectedTime,
        SelectedMassFraction,
        df,
    )


READ_SHELF = fn.Shelf(
    nodes=[
        retrieve_data,
    ],
    subshelves=[],
    name="sec Read",
    description="sec Read Nodes",
)
