# from zhinst.labber.generator.generator import LabberConfig
# import typing as t
# from zhinst.toolkit.nodetree import Node


# class Generator(Node):
#     def __init__(self):
#         ...

#     def gen_func(self):
#         ...


# class PropertyModule(Node):
#     def __init__(self):
#         pass

#     def cool_function(self):
#         ...

#     @property
#     def generator(self) -> Generator:
#         ...


# class PropertyModuleNo2(Node):
#     def __init__(self):
#         pass

#     def cool_function2(self):
#         ...


# class BaseClass(Node):
#     def __init__(self):
#         self.__nodes_test = {
#             "/dev12018/baseclass/awg/0/generator": {
#                 "Node": "/DEV12018/BASECLASS/AWG/0/GENERATOR",
#                 "Description": "Description for a node 0.",
#                 "Properties": "Read",
#                 "Type": "Double",
#                 "Unit": "V",
#             },
#             "/dev12018/baseclass/awg/1/generator": {
#                 "Node": "/DEV12018/BASECLASS/AWG/1/GENERATOR",
#                 "Description": "Description for a node 1.",
#                 "Properties": "Read",
#                 "Type": "Double",
#                 "Unit": "V",
#             },
#         }

#     def __iter__(self):
#         for k, v in self.__nodes_test.items():
#             yield k, v

#     def activate(self):
#         ...

#     def deactivate(self):
#         ...

#     @property
#     def awg(self) -> t.Sequence[PropertyModule]:
#         ...

#     @property
#     def chs(self) -> PropertyModuleNo2:
#         ...


# class TestLabberConfig:
#     def test_labber_config(self):
#         conf = LabberConfig(BaseClass(), None)
#         fs = conf.generate_functions()
#         assert fs == {
#             "ACTIVATE - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "ACTIVATE",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "SYSTEM",
#                 "set_cmd": "ACTIVATE",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#             "AWG - 0 - COOL_FUNCTION - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "AWG - 0 - COOL_FUNCTION",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "AWG - 0",
#                 "set_cmd": "AWG - 0 - COOL_FUNCTION",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#             "AWG - 0 - GENERATOR - GEN_FUNC - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "AWG - 0 - GENERATOR - GEN_FUNC",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "AWG - 0",
#                 "set_cmd": "AWG - 0 - GENERATOR - GEN_FUNC",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#             "AWG - 1 - CHS - COOL_FUNCTION2 - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "AWG - 1 - CHS - COOL_FUNCTION2",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "AWG - 1",
#                 "set_cmd": "AWG - 1 - CHS - COOL_FUNCTION2",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#             "AWG - 1 - COOL_FUNCTION - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "AWG - 1 - COOL_FUNCTION",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "AWG - 1",
#                 "set_cmd": "AWG - 1 - COOL_FUNCTION",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#             "AWG - 1 - GENERATOR - GEN_FUNC - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "AWG - 1 - GENERATOR - GEN_FUNC",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "AWG - 1",
#                 "set_cmd": "AWG - 1 - GENERATOR - GEN_FUNC",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#             "DEACTIVATE - EXECUTEFUNC": {
#                 "datatype": "BOOLEAN",
#                 "group": "DEACTIVATE",
#                 "label": "Executefunc",
#                 "permission": "WRITE",
#                 "section": "SYSTEM",
#                 "set_cmd": "DEACTIVATE",
#                 "tooltip": "<html><body><p></p></body></html>",
#             },
#         }
