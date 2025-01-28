from typing import List, Tuple
from funcnodes_span.peaks import PeakProperties
import numpy as np
import pandas as pd
import funcnodes as fn


def molar_mass_value_round(val):
    if val < 2000:
        return round(val, -1)
    elif val < 20000:
        return round(val, -2)
    else:
        return round(val, -3)


def molarMass_summation_series(Mass, Signal, Sigma) -> Tuple[float, float, np.ndarray]:
    Signal_norm_0_to_1 = (Signal - np.amin(Signal)) / (
        np.amax(Signal) - np.amin(Signal)
    )

    Wm = Signal_norm_0_to_1 / (Mass * Sigma)

    Mn = np.trapezoid(Wm, Mass) / np.trapezoid(Wm / Mass, Mass)
    Mw = np.trapezoid(Wm * Mass, Mass) / np.trapezoid(Wm, Mass)
    return Mn, Mw, Wm


def sec_peak_analysis(
    peaks: List[PeakProperties],
    mass: np.ndarray,
    sigma: np.ndarray,
) -> Tuple[pd.DataFrame, List[PeakProperties], pd.DataFrame]:
    output_peaks = []

    mwd = pd.DataFrame(
        {
            "logM": np.log10(mass),
        }
    )

    if peaks:
        for peak in peaks:
            output_peak = {}
            peak.to_dict()
            output_peak["Peak #"] = peak.id
            output_peak["Retention"] = peak.x_at_index
            # output_peak["Area"] = peak.area
            output_peak["Height"] = peak.y_at_index
            # output_peak["Symmetricity"] = peak.symmetricity
            # output_peak["FWHM"] = peak.fwhm

            peak_left = peak.i_index
            peak_right = peak.f_index
            SelectedPeakMass = mass[peak_left : peak_right + 1]
            SelectedPeakSignal = peak.yrange
            SelectedPeakSigma = sigma[peak_left : peak_right + 1]
            mn, mw, Wm = molarMass_summation_series(
                SelectedPeakMass, SelectedPeakSignal, SelectedPeakSigma
            )
            peak.add_serializable_property("Mn (g/mol)", molar_mass_value_round(mn))
            peak.add_serializable_property("Mw (g/mol)", molar_mass_value_round(mw))
            peak.add_serializable_property("D", round(mw / mn, 2))
            mwd[peak.id] = np.nan

            mwd.loc[peak_left:peak_right, peak.id] = Wm

            output_peak["Mn (g/mol)"] = peak._serdata["Mn (g/mol)"]
            output_peak["Mw (g/mol)"] = peak._serdata["Mw (g/mol)"]
            output_peak["D"] = peak._serdata["D"]
            output_peaks.append(output_peak)
    return pd.DataFrame(output_peaks), peaks, mwd


sec_report_node = fn.NodeDecorator(
    node_id="fnsec.report.sec_report",
    name="sec Report",
    inputs=[
        {"name": "mass"},
        {"name": "sigma"},
        {"name": "peaks"},
    ],
    description="Calculates sec report data from peaks and sec data.",
    outputs=[
        {"name": "sec_report"},
        {"name": "sec_peaks"},
        {"name": "MWD"},
    ],
)(sec_peak_analysis)

REPORT_SHELF = fn.Shelf(
    nodes=[
        sec_report_node,
    ],
    subshelves=[],
    name="sec Report",
    description="sec Report Nodes",
)
