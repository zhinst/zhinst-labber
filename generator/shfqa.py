from element import Element
from base_instrument import BaseInstrument
from pathlib import Path
import zhinst.toolkit as tk
import numpy as np


class SHFQA(BaseInstrument):
    def __init__(self):
        super().__init__(
            "Zurich Instruments SHFQA",
            Path("Zurich_Instruments_SHFQA"),
            "1.1",
            ["SHFQA2", "SHFQA4"],
        )

    def generate(self, device_id: str):
        device = tk.SHFQA("shfqa", device_id)
        device.setup()  # set up data server connection
        device.connect_device()  # connect device to data server

        self.device_section()
        self.inAndOut()
        self.qaSetup()
        self.qaResult()
        self.generator(device)
        self.sweeper()
        self.scope()

        self.validate(device)
        self.write_ini()

    def device_section(self):
        section = "Device"

        # Preset
        group = "Preset"
        self.add_element(
            Element(
                None,
                "Factory Reset",
                "BUTTON",
                group,
                section,
                tooltip="Load the factory default settings.",
            )
        )

        # Revisions
        group = "Revisions"
        self.add_element(
            Element(
                "data_server_version",
                "Data Server",
                "STRING",
                group,
                section,
                def_value="",
            )
        )
        self.add_element(
            Element(
                "firmware_version",
                "Firmware",
                "STRING",
                group,
                section,
                def_value="",
            )
        )
        self.add_element(
            Element(
                "fpga_version",
                "FPGA",
                "STRING",
                group,
                section,
                def_value="",
            )
        )

        # Input Reference Clock
        group = "Input Reference Clock"
        self.add_element(
            Element(
                "ref_clock",
                "Set Source",
                "COMBO",
                group,
                section,
                def_value="internal",
            )
        )
        self.add_element(
            Element(
                "ref_clock_actual",
                "Actual Source",
                "COMBO",
                group,
                section,
                def_value="internal",
            )
        )
        self.add_element(
            Element(
                "ref_clock_status",
                "Status",
                "COMBO",
                group,
                section,
                def_value="locked",
                mapping={0: "locked", 1: "error", 2: "busy"},
            )
        )

        # Extras
        group = "Extras"
        self.add_element(
            Element(
                None,
                "Enable Internal Trigger Loopback",
                "BOOLEAN",
                group,
                section,
                def_value=False,
                tooltip="Start a trigger pulse using the internal loopback. "
                "This is A 1kHz continuous trigger pulse from marker "
                "1 A using the internal loopback to trigger in 1 A.",
            )
        )
        self.add_element(
            Element(
                None,
                "Self Trigger Channel",
                "BUTTON",
                group,
                section,
                tooltip="Combined with `Enable Internal Trigger Loopback`, this "
                "controller is used to realize mesaurements with internal "
                "trigger loopback. Use this controller as trigger channel "
                "in arm/trig mode.",
                show_in_measurement_dlg=True,
            )
        )

    def inAndOut(self):
        section = "In / Out"

        for qachannel in range(4):
            group = f"Channel {qachannel+1}"
            if qachannel < 2:
                model_values = ["SHFQA2", "SHFQA4"]
            elif qachannel >= 2:
                model_values = ["SHFQA4"]

            self.add_element(
                Element(
                    f"qachannels[{qachannel}].center_freq",
                    "Center Frequency",
                    "DOUBLE",
                    group,
                    section,
                    def_value=1e9,
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].input_range",
                    "Input Range",
                    "COMBO",
                    group,
                    section,
                    def_value=10,
                    combo_defs=[-i for i in range(-10, 55, 5)],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].input",
                    f"Input On",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].output_range",
                    "Output Range",
                    "COMBO",
                    group,
                    section,
                    def_value=10,
                    combo_defs=[-i for i in range(-10, 35, 5)],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].output",
                    f"Output On",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    model_values=model_values,
                )
            )

    def qaSetup(self):
        section = "QA Setup"

        for qachannel in range(4):
            group = f"QA Channel {qachannel+1}"
            if qachannel < 2:
                model_values = ["SHFQA2", "SHFQA4"]
            elif qachannel >= 2:
                model_values = ["SHFQA4"]

            self.add_element(
                Element(
                    f"qachannels[{qachannel}].mode",
                    "Application Mode",
                    "COMBO",
                    group,
                    section,
                    def_value="spectroscopy",
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].generator.dig_trigger1_source",
                    "Digital Trigger 1",
                    "COMBO",
                    group,
                    section,
                    def_value="Channel 1, Trigger Input A",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                    extended_map=True,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].generator.dig_trigger2_source",
                    "Digital Trigger 2",
                    "COMBO",
                    group,
                    section,
                    def_value="Channel 1, Trigger Input A",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                    extended_map=True,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].readout.integration_length",
                    "Readout Integration Length",
                    "DOUBLE",
                    group,
                    section,
                    def_value=128,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].readout.integration_delay",
                    "Readout Integration Delay",
                    "DOUBLE",
                    group,
                    section,
                    def_value=0,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Integration Weights File Path",
                    "PATH",
                    group,
                    section,
                    def_value="",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.trigger_source",
                    "Trigger Signal",
                    "COMBO",
                    group,
                    section,
                    def_value="Channel 1, Trigger Input A",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                    extended_map=True,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.trigger_level",
                    "Trigger Level",
                    "DOUBLE",
                    group,
                    section,
                    unit="V",
                    def_value=0.5,
                    tooltip="Defines the analog Trigger level.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.trigger_imp50",
                    "Trigger Input Impedance",
                    "COMBO",
                    group,
                    section,
                    def_value="OFF: 1 k Ohm",
                    tooltip="Trigger Input impedance: When on, the Trigger "
                    "Input impedance is 50 Ohm; when off, 1 kOhm.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                    mapping={0: "OFF: 1 k Ohm", 1: "ON: 50 Ohm"},
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.integration_length",
                    "Spectroscopy Integration Length",
                    "DOUBLE",
                    group,
                    section,
                    def_value=1024,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.integration_delay",
                    "Spectroscopy Integration Delay",
                    "DOUBLE",
                    group,
                    section,
                    def_value=0,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.oscillator_freq",
                    "Offset Frequency",
                    "DOUBLE",
                    group,
                    section,
                    def_value=10e6,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.output_freq",
                    "Output Frequency",
                    "DOUBLE",
                    group,
                    section,
                    unit="Hz",
                    def_value=1.01e9,
                    tooltip="Displays the carrier frequency of the microwave signal "
                    "at the Out connector. This frequency corresponds to the "
                    "sum of the Center Frequency and the Offset Frequency.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                    permission="READ",
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.oscillator_gain",
                    "Amplitude",
                    "DOUBLE",
                    group,
                    section,
                    def_value=0.5,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                )
            )

    def qaResult(self):
        section = "QA Result"
        qubits = np.arange(1, 17)
        for qachannel in range(4):
            group = f"Readout {qachannel+1}"
            if qachannel < 2:
                model_values = ["SHFQA2", "SHFQA4"]
            elif qachannel >= 2:
                model_values = ["SHFQA4"]

            self.add_element(
                Element(
                    f"nodetree.qachannels[{qachannel}].readout.result.enable",
                    "Enable Readout",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                )
            )

            self.add_element(
                Element(
                    f"qachannels[{qachannel}].readout.result_source",
                    "Result Source",
                    "COMBO",
                    group,
                    section,
                    def_value="result_of_integration",
                    state_quant=f"Readout {qachannel+1} - Enable Readout",
                    state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].readout.result_length",
                    "Length (Sample)",
                    "DOUBLE",
                    group,
                    section,
                    def_value=1,
                    state_quant=f"Readout {qachannel+1} - Enable Readout",
                    state_values=[True],
                    model_values=model_values,
                )
            )

            self.add_element(
                Element(
                    f"qachannels[{qachannel}].readout.num_averages",
                    "Averages",
                    "DOUBLE",
                    group,
                    section,
                    def_value=1,
                    state_quant=f"Readout {qachannel+1} - Enable Readout",
                    state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].readout.result.mode",
                    "Mode",
                    "COMBO",
                    group,
                    section,
                    def_value="cyclic",
                    state_quant=f"Readout {qachannel+1} - Enable Readout",
                    state_values=[True],
                    combo_defs=list(("cyclic", "sequential")),
                    cmd_defs=list(range(2)),
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Number of Integration Units",
                    "COMBO",
                    group,
                    section,
                    def_value=1,
                    state_quant=f"Readout {qachannel+1} - Enable Readout",
                    state_values=[True],
                    combo_defs=list(qubits),
                    cmd_defs=list(qubits),
                    model_values=model_values,
                )
            )

            for qubit in range(len(qubits)):
                self.add_element(
                    Element(
                        None,
                        f"Result Average - Integration {qubit+1}",
                        "COMPLEX",
                        group,
                        section,
                        def_value=0 + 0j,
                        state_quant=f"Readout {qachannel+1} - Result Source",
                        state_values=["result_of_integration"],
                        second_state_quant=f"Readout {qachannel+1} - Number of Integration Units",
                        second_state_values=[
                            i for i in range(qubit + 1, len(qubits) + 1)
                        ],
                        model_values=model_values,
                        permission="READ",
                        show_in_measurement_dlg=True,
                    )
                )

            for qubit in range(len(qubits)):
                self.add_element(
                    Element(
                        None,
                        f"Result Average - Discrimination {qubit+1}",
                        "DOUBLE",
                        group,
                        section,
                        def_value=0,
                        state_quant=f"Readout {qachannel+1} - Result Source",
                        state_values=["result_of_discrimination"],
                        second_state_quant=f"Readout {qachannel+1} - Number of Integration Units",
                        second_state_values=[
                            i for i in range(qubit + 1, len(qubits) + 1)
                        ],
                        model_values=model_values,
                        permission="READ",
                        show_in_measurement_dlg=True,
                    )
                )

            for qubit in range(len(qubits)):
                self.add_element(
                    Element(
                        None,
                        f"Result Vector - Integration {qubit+1}",
                        "VECTOR_COMPLEX",
                        group,
                        section,
                        def_value=[],
                        x_name="Length",
                        x_unit="Sample",
                        state_quant=f"Readout {qachannel+1} - Result Source",
                        state_values=["result_of_integration"],
                        second_state_quant=f"Readout {qachannel+1} - Number of Integration Units",
                        second_state_values=[
                            i for i in range(qubit + 1, len(qubits) + 1)
                        ],
                        model_values=model_values,
                        permission="READ",
                        show_in_measurement_dlg=True,
                    )
                )

            for qubit in range(len(qubits)):
                self.add_element(
                    Element(
                        None,
                        f"Result Vector - Discrimination {qubit+1}",
                        "VECTOR",
                        group,
                        section,
                        def_value=[],
                        x_name="Length",
                        x_unit="Sample",
                        state_quant=f"Readout {qachannel+1} - Result Source",
                        state_values=["result_of_discrimination"],
                        second_state_quant=f"Readout {qachannel+1} - Number of Integration Units",
                        second_state_values=[
                            i for i in range(qubit + 1, len(qubits) + 1)
                        ],
                        model_values=model_values,
                        permission="READ",
                        show_in_measurement_dlg=True,
                    )
                )

    def generator(self,device):
        section = "Generator"
        sequence_types = [i.value for i in device.allowed_sequences]
        trigger_modes = [i.value for i in device.allowed_trigger_modes]

        for qachannel in range(4):
            group = f"Sequencer {qachannel+1}"
            if qachannel < 2:
                model_values = ["SHFQA2", "SHFQA4"]
            elif qachannel >= 2:
                model_values = ["SHFQA4"]

            self.add_element(
                Element(
                    f"qachannels[{qachannel}].generator.playback_delay",
                    "Playback Delay",
                    "DOUBLE",
                    group,
                    section,
                    def_value=0,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].generator.single",
                    "Single",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=True,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Sequence Type",
                    "COMBO",
                    group,
                    section,
                    def_value="None",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    combo_defs=sequence_types,
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Program Path",
                    "PATH",
                    group,
                    section,
                    def_value="",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    second_state_quant=f"Sequencer {qachannel+1} - Sequence Type",
                    second_state_values=["Custom"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Custom Parameters",
                    "STRING",
                    group,
                    section,
                    def_value="",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    second_state_quant=f"Sequencer {qachannel+1} - Sequence Type",
                    second_state_values=["Custom"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Waveform Source",
                    "COMBO",
                    group,
                    section,
                    def_value="Vector Data",
                    combo_defs=["File Path", "Vector Data"],
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    second_state_quant=f"Sequencer {qachannel+1} - Sequence Type",
                    second_state_values=["Custom"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Waveform Path",
                    "PATH",
                    group,
                    section,
                    def_value="",
                    state_quant=f"Sequencer {qachannel+1} - Sequence Type",
                    state_values=["Custom"],
                    second_state_quant=f"Sequencer {qachannel+1} - Waveform Source",
                    second_state_values=["File Path"],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Waveform Vector",
                    "VECTOR_COMPLEX",
                    group,
                    section,
                    def_value=[],
                    state_quant=f"Sequencer {qachannel+1} - Sequence Type",
                    state_values=["Custom"],
                    second_state_quant=f"Sequencer {qachannel+1} - Waveform Source",
                    second_state_values=["Vector Data"],
                    model_values=model_values,
                    permission="WRITE",
                    show_in_measurement_dlg=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Trigger Mode",
                    "COMBO",
                    group,
                    section,
                    def_value="None",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["readout"],
                    combo_defs=trigger_modes,
                    model_values=model_values,
                )
            )
            num_user_regs = 16
            self.add_element(
                Element(
                    None,
                    "SHOW User registers",
                    "COMBO",
                    group,
                    section,
                    def_value=1,
                    combo_defs=list(range(1, num_user_regs + 1)),
                    cmd_defs=list(range(num_user_regs)),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            for reg in range(num_user_regs):
                self.add_element(
                    Element(
                        f"qachannels[{qachannel}].generator.user_registers[{reg}]",
                        f"User Register {reg+1}",
                        "DOUBLE",
                        group,
                        section,
                        unit="Hz",
                        def_value=0,
                        state_quant=f"{group} - SHOW User registers",
                        show_in_measurement_dlg="True",
                        model_values=model_values,
                    )
                )
            self.add_element(
                Element(
                    None,
                    "Run/Stop",
                    "BUTTON",
                    group,
                    section,
                    tooltip="Runs/stops the Generator",
                    model_values=model_values,
                )
            )

    def sweeper(self):
        section = "Sweeper"

        for qachannel in range(4):
            group = f"Sweeper {qachannel+1}"
            if qachannel < 2:
                model_values = ["SHFQA2", "SHFQA4"]
            elif qachannel >= 2:
                model_values = ["SHFQA4"]

            self.add_element(
                Element(
                    None,
                    "Enable Sweeper",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    model_values=model_values,
                )
            )

            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.start_frequency",
                    "Start Frequency",
                    "DOUBLE",
                    group,
                    section,
                    def_value=-300e6,
                    tooltip="Set or get the start frequency for the sweeper.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.stop_frequency",
                    "Stop Frequency",
                    "DOUBLE",
                    group,
                    section,
                    def_value=300e6,
                    tooltip="Set or get the stop frequency for the sweeper.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.num_points",
                    "Number of Points",
                    "DOUBLE",
                    group,
                    section,
                    def_value=100,
                    tooltip="Set or get the number of points for the sweeper.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Mapping",
                    "COMBO",
                    group,
                    section,
                    def_value="linear",
                    tooltip="Set or get the mapping configuration for the sweeper.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                    combo_defs=["linear", "log"],
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.num_averages",
                    "Number of Averages",
                    "DOUBLE",
                    group,
                    section,
                    def_value=1,
                    tooltip="'Set or get the number of averages for the sweeper.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"qachannels[{qachannel}].sweeper.averaging_mode",
                    "Averaging Mode",
                    "COMBO",
                    group,
                    section,
                    def_value="cyclic",
                    tooltip="Set or get the averaging mode for the sweeper.",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                    combo_defs=["sequential", "cyclic"],
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Result Vector",
                    "VECTOR_COMPLEX",
                    group,
                    section,
                    unit="Voltage",
                    def_value=[],
                    x_name="Frequency",
                    x_unit="Hz",
                    state_quant=f"QA Channel {qachannel+1} - Application Mode",
                    state_values=["spectroscopy"],
                    second_state_quant=f"Sweeper {qachannel+1} - Enable Sweeper",
                    second_state_values=[True],
                    model_values=model_values,
                    permission="READ",
                    show_in_measurement_dlg=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Run",
                    "BUTTON",
                    group,
                    section,
                    tooltip="Run the Sweeper",
                    model_values=model_values,
                )
            )

    def scope(self):
        section = "Scope"

        # Recording
        group = "Recording"
        self.add_element(
            Element(
                f"nodetree.scope.enable",
                "Enable Scope",
                "BOOLEAN",
                group,
                section,
                def_value=False,
            )
        )
        self.add_element(
            Element(
                f"scope.length",
                "Length",
                "DOUBLE",
                group,
                section,
                def_value=32,
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )
        self.add_element(
            Element(
                f"scope.time",
                "Sampling Rate",
                "COMBO",
                group,
                section,
                def_value="2 GHz",
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )

        for qachannel in range(4):
            group = f"Scope Channel {qachannel+1}"
            if qachannel < 2:
                model_values = ["SHFQA2", "SHFQA4"]
            elif qachannel >= 2:
                model_values = ["SHFQA4"]

            self.add_element(
                Element(
                    None,
                    "Enable",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    state_quant=f"Recording - Enable Scope",
                    state_values=[True],
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"scope.input_select{qachannel+1}",
                    "Signal Source",
                    "COMBO",
                    group,
                    section,
                    def_value=f"Signal Input Channel {qachannel+1}",
                    state_quant=f"Recording - Enable Scope",
                    second_state_quant=f"Scope Channel {qachannel+1} - Enable",
                    second_state_values=[True],
                    state_values=[True],
                    model_values=model_values,
                    extended_map=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    f"Result Vector",
                    "VECTOR_COMPLEX",
                    group,
                    section,
                    unit="Voltage",
                    def_value=[],
                    x_name="Time",
                    x_unit="s",
                    state_quant=f"Recording - Enable Scope",
                    state_values=[True],
                    second_state_quant=f"Scope Channel {qachannel+1} - Enable",
                    second_state_values=[True],
                    model_values=model_values,
                    permission="READ",
                    show_in_measurement_dlg=True,
                )
            )
        # Trigger
        group = "Trigger"
        self.add_element(
            Element(
                f"scope.trigger_source",
                "Source",
                "COMBO",
                group,
                section,
                def_value=f"Channel 1, Trigger Input A",
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
                extended_map=True,
            )
        )
        self.add_element(
            Element(
                f"scope.trigger_delay",
                "Delay",
                "DOUBLE",
                group,
                section,
                def_value=0,
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )
        # Segments
        group = "Segments"
        self.add_element(
            Element(
                f"nodetree.scope.segments.enable",
                "Enable",
                "BOOLEAN",
                group,
                section,
                def_value=False,
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )
        self.add_element(
            Element(
                f"nodetree.scope.segments.count",
                "Segments",
                "DOUBLE",
                group,
                section,
                def_value=1,
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )
        # Averaging
        group = "Averaging"
        self.add_element(
            Element(
                f"nodetree.scope.averaging.enable",
                "Enable",
                "BOOLEAN",
                group,
                section,
                def_value=False,
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )
        self.add_element(
            Element(
                f"nodetree.scope.averaging.count",
                "Averages",
                "DOUBLE",
                group,
                section,
                def_value=1,
                state_quant=f"Recording - Enable Scope",
                state_values=[True],
            )
        )



test = SHFQA()
test.generate("DEV12047")
