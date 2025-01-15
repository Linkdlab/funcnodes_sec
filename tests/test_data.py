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
        self.assertEqual(len(sec.outputs["signal"].value), 663)

    # def test_read_file_lines(self):
    #     data = b"  start\n  stop\n"
    #     lines = fnmodule.data.read_file_lines(data)
    #     self.assertEqual(lines, ["start\n", "stop\n"])

    # def test_process_sec_file(self):
    #     lines = ["start\n", "1\t2\n", "stop\n"]
    #     dfTotal, clmLines, heads = fnmodule.data.process_sec_file(lines)
    #     self.assertEqual(dfTotal, {"": '{"columns":["1","2"],"index":[0],"data":[[1,2]]}'})
    #     self.assertEqual(clmLines, [1])
    #     self.assertEqual(heads, ['{"columns":["1","2"],"index":[0],"data":[[1,2]]}'])

    # def test_extract_metadata(self):
    #     lines = ["start\n", "key: value\n", "stop\n"]
    #     metadata_dict = fnmodule.data.extract_metadata(lines, 2)
    #     self.assertEqual(metadata_dict, {"key": " value\n"})
