import os
import unittest
import funcnodes as fn

# import pandas as pd
import funcnodes_sec as fnmodule
# from funcnodes_sec import read_data  # noqa
# from fnmodule.data import sec_read_node


class TestSECData(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), "win_gpc_sample"), "rb") as f:
            self.bytes = f.read()

    async def test_read_sec(self):
        sec: fn.Node = fnmodule.read_data.retrieve_data()
        sec.inputs["sec_data"].value = self.bytes
        sec.inputs["molarmass_min"].value = 200
        sec.inputs["molarmass_max"].value = 1000000
        self.assertIsInstance(sec, fn.Node)
        await sec
        signal = sec.outputs["signal"].value
        self.assertEqual(len(signal), 663)
