import os
import unittest
import funcnodes as fn
import pandas as pd
import funcnodes_sec as fnmodule
from funcnodes_span.peaks import PeakProperties
from funcnodes_span.peak_analysis import peak_finder
# from fnmodule.data import sec_read_node


class TestSECReport(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        with open(
            os.path.join(os.path.dirname(__file__), "010_TKH_Ac(e)DexLibrary_SEC"), "rb"
        ) as f:
            self.bytes = f.read()

    async def test_report_sec(self):
        node: fn.Node = fnmodule.read_data.read_sec_from_bytes()
        node.inputs["data"].value = self.bytes
        self.assertIsInstance(node, fn.Node)
        await node
        metadata = node.outputs["sec_metadata"].value
        data = node.outputs["sec_data"].value
        self.assertIsInstance(metadata, pd.DataFrame)
        self.assertIsInstance(data, dict)

        sec: fn.Node = fnmodule.read_data.retrieve_data()
        sec.inputs["data"].value = data
        sec.inputs["metadata"].value = metadata
        sec.inputs["molarmass_min"].value = 200
        sec.inputs["molarmass_max"].value = 1000000
        self.assertIsInstance(sec, fn.Node)
        await sec
        signal = sec.outputs["signal"].value
        volume = sec.outputs["volume"].value
        mass = sec.outputs["mass"].value
        sigma = sec.outputs["sigma"].value

        self.assertEqual(len(signal), 663)

        peaks: fn.Node = peak_finder()
        peaks.inputs["y"].value = signal
        peaks.inputs["x"].value = volume
        peaks.inputs["height"].value = 0.0299
        self.assertIsInstance(peaks, fn.Node)
        await peaks
        main_peak = peaks.outputs["peaks"].value
        self.assertIsInstance(main_peak, list)
        self.assertIsInstance(main_peak[0], PeakProperties)

        sec_report: fn.Node = fnmodule.report.sec_report_node()
        sec_report.inputs["signal"].value = signal
        sec_report.inputs["mass"].value = mass
        sec_report.inputs["sigma"].value = sigma
        sec_report.inputs["peaks"].value = main_peak
        self.assertIsInstance(sec_report, fn.Node)
        await sec_report
        print(sec_report.outputs["sec_report"].value)

        report = sec_report.outputs["sec_report"].value
        peaks_sec = sec_report.outputs["sec_peaks"].value[0]
        self.assertEqual(
            [list(report.keys())[-3], list(report.keys())[-2], list(report.keys())[-1]],
            ["Mn (g/mol)", "Mw (g/mol)", "D"],
        )
        self.assertIsInstance(peaks_sec, PeakProperties)
        self.assertEqual(
            list(peaks_sec._serdata.keys()),
            ["area", "symmetricity", "Mn (g/mol)", "Mw (g/mol)", "D"],
        )
