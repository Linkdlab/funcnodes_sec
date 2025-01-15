# this is an autogenerated file, do not edit it directly or your changes might be lost.
import unittest
from funcnodes_sec import NODE_SHELF  # noqa
from functools import wraps
from typing import List
import funcnodes as fn
import asyncio


def passfunc(self, *args, **kwargs):
    pass


async def async_passfunc(self, *args, **kwargs):
    pass


def add_subclass_tests(cls):
    # Dynamically add test methods from sub_test_classes
    if not hasattr(cls, "sub_test_classes"):
        return
    for testcase in cls.sub_test_classes:
        if hasattr(testcase, "setUp"):
            inner_setup = testcase.setUp
        else:
            inner_setup = passfunc

        if hasattr(testcase, "asyncSetUp"):
            inner_async_setup = testcase.asyncSetUp
        else:
            inner_async_setup = async_passfunc

        if hasattr(testcase, "tearDown"):
            inner_teardown = testcase.tearDown
        else:
            inner_teardown = passfunc

        if hasattr(testcase, "asyncTearDown"):
            inner_async_teardown = testcase.asyncTearDown
        else:
            inner_async_teardown = async_passfunc

        for attr_name in dir(testcase):
            if attr_name.startswith("test_"):
                # Retrieve the test method from the subclass
                test_method = getattr(testcase, attr_name)

                # Create a new test method that wraps the original test method
                def make_new_test_method(
                    test_method=test_method,
                    inner_setup=inner_setup,
                    inner_teardown=inner_teardown,
                    inner_async_setup=inner_async_setup,
                    inner_async_teardown=inner_async_teardown,
                ):
                    if asyncio.iscoroutinefunction(test_method):

                        async def test_method_wrapper(self, *args, **kwargs):
                            # Call the inner setup method
                            inner_setup(self)
                            await inner_async_setup(self)
                            # Call the test method
                            await test_method(self, *args, **kwargs)
                            print(f"Test {test_method.__name__} passed")
                            # Call the inner teardown method
                            inner_teardown(self)
                            await inner_async_teardown(self)

                    else:

                        def test_method_wrapper(self, *args, **kwargs):
                            # Call the inner setup method
                            inner_setup(self)
                            # Call the test method
                            test_method(self, *args, **kwargs)
                            print(f"Test {test_method.__name__} passed")
                            # Call the inner teardown method
                            inner_teardown(self)

                    return test_method_wrapper

                # Create a unique name for the test method in this class
                new_test_name = f"test_{testcase.__name__}_{attr_name}"
                # Add the test method to this class
                setattr(
                    cls,
                    new_test_name,
                    make_new_test_method(
                        test_method=test_method,
                        inner_setup=inner_setup,
                        inner_teardown=inner_teardown,
                        inner_async_setup=inner_async_setup,
                        inner_async_teardown=inner_async_teardown,
                    ),
                )


class TestAllNodesBase(unittest.IsolatedAsyncioTestCase):
    # if you tests your nodes with in other test classes, add them here
    # this will automtically extend this test class with the tests in the other test classes
    # but this will also mean if you run all tests these tests might run multiple times
    # also the correspondinig setups and teardowns will not be called, so the tests should be
    # independently callable
    sub_test_classes: List[unittest.IsolatedAsyncioTestCase] = []

    # if you have specific nodes you dont want to test, add them here
    # But why would you do that, it will ruin the coverage?!
    # a specific use case would be ignore nodes that e.g. load a lot of data, but there we would recommend
    # to write tests with patches and not ignore them.
    ignore_nodes: List[fn.Node] = []

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        add_subclass_tests(cls)
        return cls

    @classmethod
    def setUpClass(cls):
        def get_all_nodes_classes(shelf: fn.Shelf, current=None):
            if current is None:
                current = []
            for node in shelf.nodes:
                if node not in current:
                    current.append(node)

            for subshelf in shelf.subshelves:
                get_all_nodes_classes(subshelf, current)

            return current

        all_nodes = fn.flatten_shelf(NODE_SHELF)[0]
        nodes_to_test = all_nodes.copy()

        for node in cls.ignore_nodes:
            if node in nodes_to_test:
                nodes_to_test.remove(node)

        # monkey patching the async func method in the nodeclasses that if they are called the nodeclass
        # is removed from the NODES_TO_TEST list
        def monkey_patch_func(node_class):
            ofunc = node_class.func
            node_class.TestAllNodes_func = ofunc

            @wraps(ofunc)
            async def func(self, *args, **kwargs):
                res = await ofunc(self, *args, **kwargs)
                if node_class in nodes_to_test:
                    nodes_to_test.remove(node_class)
                return res

            node_class.func = func

        for node_class in all_nodes:
            monkey_patch_func(node_class)

        cls.all_nodes = all_nodes
        cls.nodes_to_test = nodes_to_test

    @classmethod
    def tearDownClass(cls):
        # undo the monkey patching
        for node_class in cls.all_nodes:
            if hasattr(node_class, "TestAllNodes_func"):
                node_class.func = node_class.TestAllNodes_func
                del node_class.TestAllNodes_func

        # Final assertion to ensure all nodes were tested
        if cls.nodes_to_test:
            raise AssertionError(
                f"These nodes were not tested ({len(cls.nodes_to_test)}): {cls.nodes_to_test}"
            )
