import os
import unittest
import funcnodes as fn
import funcnodes_sec as fnmodule
from funcnodes_span.peaks import PeakProperties
from funcnodes_span.peak_analysis import peak_finder
# from fnmodule.data import sec_read_node


class TestSECReport(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), "win_gpc_sample"), "rb") as f:
            self.bytes = f.read()

    async def test_report_sec(self):
        sec: fn.Node = fnmodule.read_data.retrieve_data()
        sec.inputs["sec_data"].value = self.bytes
        sec.inputs["molarmass_min"].value = 200
        sec.inputs["molarmass_max"].value = 1000000
        self.assertIsInstance(sec, fn.Node)
        await sec
        # volume = sec.outputs["volume"].value
        # mass = sec.outputs["mass"].value
        # sigma = sec.outputs["sigma"].value

        self.assertEqual(len(sec.outputs["signal"].value), 663)

        peaks: fn.Node = peak_finder()
        peaks.inputs["y"].connect(sec.outputs["signal"])
        peaks.inputs["x"].connect(sec.outputs["volume"])
        peaks.inputs["height"].value = 0.0299
        self.assertIsInstance(peaks, fn.Node)
        await peaks
        main_peak = peaks.outputs["peaks"].value
        self.assertIsInstance(main_peak, list)
        self.assertIsInstance(main_peak[0], PeakProperties)

        sec_report: fn.Node = fnmodule.report.sec_report_node()
        sec_report.inputs["mass"].connect(sec.outputs["mass"])
        sec_report.inputs["sigma"].connect(sec.outputs["sigma"])
        sec_report.inputs["peaks"].connect(peaks.outputs["peaks"])
        self.assertIsInstance(sec_report, fn.Node)
        await sec_report
        # print(sec_report.outputs["sec_report"].value)

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
