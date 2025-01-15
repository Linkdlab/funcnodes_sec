from typing import List
from funcnodes_span.peaks import PeakProperties
import numpy as np
import funcnodes as fn


def molar_mass_value_round(val):
    if val < 2000:
        return round(val, -1)
    elif val < 20000:
        return round(val, -2)
    else:
        return round(val, -3)


def molarMass_summation_series(Mass, Signal, Sigma):
    Signal_norm_0_to_1 = (Signal - np.amin(Signal)) / (
        np.amax(Signal) - np.amin(Signal)
    )

    Wm = Signal_norm_0_to_1 / (Mass * Sigma)

    Mn = np.trapz(Wm, Mass) / np.trapz(Wm / Mass, Mass)
    Mw = np.trapz(Wm * Mass, Mass) / np.trapz(Wm, Mass)
    return Mn, Mw


def sec_peak_analysis(data: dict, peaks: List[PeakProperties]) -> List[PeakProperties]:
    signal = data["signal"]
    mass = data["mass"]
    sigma = data["sigma"]
    peak_report = []
    if peaks:
        for peak in peaks:
            peak_left = peak.i_index
            peak_right = peak.f_index
            SelectedPeakMass = mass[peak_left:peak_right]
            SelectedPeakSignal = signal[peak_left:peak_right]
            SelectedPeakSigma = sigma[peak_left:peak_right]
            mn, mw = molarMass_summation_series(
                SelectedPeakMass, SelectedPeakSignal, SelectedPeakSigma
            )
            peak.add_serializable_property("Mn (g/mol)", molar_mass_value_round(mn))
            peak.add_serializable_property("Mw (g/mol)", molar_mass_value_round(mw))
            peak.add_serializable_property("D", round(mw / mn, 2))
            peak_report.append(peak)

    return peak_report


sec_report_node = fn.NodeDecorator(
    node_id="fnsec.report.sec_report",
    name="sec Report",
    inputs=[
        {"name": "data", "dtype": "dict"},
        {"name": "peaks", "dtype": "PeakProperties"},
    ],
    description="Calculates sec report data from peaks and sec data.",
    outputs=[
        {"name": "peaks_sec", "dtype": "PeakProperties"},
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
