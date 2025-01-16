import os
import unittest
import funcnodes as fn
import pandas as pd
import funcnodes_sec as fnmodule
# from funcnodes_sec import read_data  # noqa
# from fnmodule.data import sec_read_node


class TestSECData(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        with open(
            os.path.join(os.path.dirname(__file__), "010_TKH_Ac(e)DexLibrary_SEC"), "rb"
        ) as f:
            self.bytes = f.read()

    async def test_read_sec(self):
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
        self.assertEqual(len(signal), 663)
