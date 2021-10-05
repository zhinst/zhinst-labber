from element import Element
from base_instrument import BaseInstrument
from pathlib import Path
import zhinst.toolkit as tk
import numpy as np


class SHFSG(BaseInstrument):
    def __init__(self):
        super().__init__(
            "Zurich Instruments SHFSG",
            Path("Zurich_Instruments_SHFSG"),
            "1.1",
            ["SHFSG4", "SHFSG8"],
            False,
        )

    def generate(self, device_id: str):
        device = tk.SHFSG("shfsg", device_id)
        device.setup()  # set up data server connection
        device.connect_device()  # connect device to data server

        self.device_section()
        self.output_section()
        self.sequencer_section()
        self.oscillator_section()
        self.sine_section()
        self.dio_section()

        self.validate(device)
        self.write_ini()

    def device_section(self):
        section = "Device"

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
                "ref_clock_status",
                "Status",
                "COMBO",
                group,
                section,
                def_value="locked",
                mapping={0: "locked", 1: "error", 2: "busy"},
            )
        )

        # Output Reference Clock
        group = "Output Reference Clock"
        self.add_element(
            Element(
                "ref_clock_out",
                "Enable",
                "BOOLEAN",
                group,
                section,
                def_value=False,
            )
        )
        self.add_element(
            Element(
                "ref_clock_out_freq",
                "Center Frequency",
                "COMBO",
                group,
                section,
                def_value="100 MHz",
                combo_defs=list(("10 MHz", "100 MHz",)),
                cmd_defs=list((10e6,100e6)),
            )
        )

    def output_section(self):
        section = "Output"

        for sgchannel in range(8):
            group = f"SGChannel {sgchannel+1}"
            if sgchannel < 4:
                model_values = ["SHFSG4", "SHFSG8"]
            elif sgchannel >= 4:
                model_values = ["SHFSG8"]

            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].output",
                    "Output",
                    "COMBO",
                    group,
                    section,
                    def_value="on",
                    combo_defs=list(("on", "off")),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].output_range",
                    "Range",
                    "COMBO",
                    group,
                    section,
                    def_value="-30",
                    combo_defs=list(np.arange(-30, 11, 5)),
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].rflfpath",
                    "Path",
                    "COMBO",
                    group,
                    section,
                    def_value="lf",
                    combo_defs=list(("lf", "rf")),
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].rf_center_freq",
                    "Center Frequency",
                    "DOUBLE",
                    group,
                    section,
                    state_quant=f"{group} - Path",
                    state_values=["rf"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].marker_source",
                    "Marker Source",
                    "COMBO",
                    group,
                    section,
                    def_value="AWG Trigger 1",
                    combo_defs=list((
                        "AWG Trigger 1",
                        "AWG Trigger 2",
                        "AWG Trigger 3",
                        "Output 1 Marker 1",
                        "Output 1 Marker 2",
                        "Output 2 Marker 1",
                        "Output 2 Marker 2",
                        "Trigger Input 0",
                        "Trigger Input 1",
                        "Trigger Input 2",
                        "Trigger Input 3",
                        "Trigger Input 4",
                        "Trigger Input 5",
                        "Trigger Input 6",
                        "Trigger Input 7",
                        "Trigger Input 8",
                        "Low",
                        "High",)),
                    cmd_defs=list(range(18)),
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                )
            )

            # self.add_element(
            #     Element(
            #         f"sgchannels[{sgchannel}].digital_mixer_center_freq",
            #         "Digital Mixer Center Frequency",
            #         "DOUBLE",
            #         group,
            #         section,
            #         state_quant=f"{group} - Path",
            #         state_values=["lf"],
            #         show_in_measurement_dlg="False",
            #         model_values=model_values,
            #     )
            # )

    def sequencer_section(self):
        for sgchannel in range(8):
            section = f"Sequencer {sgchannel+1}"
            if sgchannel < 4:
                model_values = ["SHFSG4", "SHFSG8"]
            elif sgchannel >= 4:
                model_values = ["SHFSG8"]

            group = f"Control"

            self.add_element(
                Element(
                    None,
                    "Run",
                    "BUTTON",
                    group,
                    section,
                    tooltip="Activates the AWG",
                    model_values=model_values,
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )
            # IQ Modulation
            group = f"IQ Modulation"

            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.gain00",
                    "Gain 00",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1.0",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.gain01",
                    "Gain 01",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1.0",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.gain10",
                    "Gain 10",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1.0",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.gain11",
                    "Gain 11",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1.0",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.modulation_freq",
                    "Modulation Frequency",
                    "DOUBLE",
                    group,
                    section,
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.modulation_phase_shift",
                    "Modulation Phase",
                    "DOUBLE",
                    group,
                    section,
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.osc_select",
                    "Oscillator",
                    "COMBO",
                    group,
                    section,
                    def_value=1,
                    combo_defs=list(range(1, 9)),
                    cmd_defs=list(range(8)),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )

            # Sequencer Program
            group = f"Sequencer Program"
            self.add_element(
                Element(
                    None,
                    "Sequence",
                    "COMBO",
                    group,
                    section,
                    def_value="None",
                    combo_defs=list(
                        ("None", "Simple", "Rabi", "T1", "T2*", "Custom", "Trigger")
                    ),
                    cmd_defs=list(range(7)),
                    model_values=model_values,
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Trigger Mode",
                    "COMBO",
                    group,
                    section,
                    def_value="None",
                    combo_defs=list(
                        ("None", "Send Trigger", "Receive Trigger")
                    ),
                    cmd_defs=list(range(3)),
                    model_values=model_values,
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Waveform Path",
                    "PATH",
                    group,
                    section,
                    model_values=model_values,
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Custom", "Simple"],
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Command Table Path",
                    "PATH",
                    group,
                    section,
                    model_values=model_values,
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Custom"],
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Sequence Path",
                    "PATH",
                    group,
                    section,
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Custom"],
                    model_values=model_values,
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )

            self.add_element(
                Element(
                    None,
                    "Custom Params",
                    "STRING",
                    group,
                    section,
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Custom"],
                    model_values=model_values,
                    show_in_measurement_dlg="True",
                    multi_section=True,
                )
            )


            self.add_element(
                Element(
                    None,
                    "Pulse Amplitude Start",
                    "DOUBLE",
                    group,
                    section,
                    def_value="0.0",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Rabi"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )

            self.add_element(
                Element(
                    None,
                    "Pulse Amplitude Stop",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1.0",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Rabi"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )

            self.add_element(
                Element(
                    None,
                    "Pulse Amplitude Number",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Rabi"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )

            self.add_element(
                Element(
                    None,
                    "Pulse Amplitude",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1.0",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["T1", "T2*"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    low_lim=0,
                    high_lim=1,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Pulse Width",
                    "DOUBLE",
                    group,
                    section,
                    def_value="50e-9",
                    unit="s",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["Rabi", "T1", "T2*"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Delay Time Start",
                    "DOUBLE",
                    group,
                    section,
                    def_value="0.1e-6",
                    unit="s",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["T1", "T2*"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Delay Time Stop",
                    "DOUBLE",
                    group,
                    section,
                    def_value="10e-6",
                    unit="s",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["T1", "T2*"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Delay Time Number",
                    "DOUBLE",
                    group,
                    section,
                    def_value="1",
                    unit="s",
                    state_quant=f"{section} - {group} - Sequence",
                    state_values=["T1", "T2*"],
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )

            # Advance
            group = "Advance"
            self.add_element(
                Element(
                    None,
                    "Trigger Delay",
                    "DOUBLE",
                    group,
                    section,
                    def_value="0",
                    unit="s",
                    tooltip="addittional delay in seconds that shifts the time origin `t=0` with respect to the trigger signal.",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Repetitions",
                    "DOUBLE",
                    group,
                    section,
                    def_value="100",
                    tooltip="The number of repetitions of the experiment.",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Period",
                    "DOUBLE",
                    group,
                    section,
                    def_value="100e-6",
                    unit="s",
                    tooltip="Period in seconds at which the experiment is repeated.",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )

            # Sequencer Code Error
            group = "Error"
            self.add_element(
                Element(
                    None,
                    "Sequence Error",
                    "STRING",
                    group,
                    section,
                    def_value="",
                    tooltip="Error of automated sequencer Code generator",
                    show_in_measurement_dlg="False",
                    model_values=model_values,
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Reset Default",
                    "BUTTON",
                    group,
                    section,
                    tooltip="Reset custom sequencer settings to default.",
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )

            # Sequencer Code Manual
            group = "Sequencer Code Manual"
            self.add_element(
                Element(
                    None,
                    "Sequencer Code Output",
                    "PATH",
                    group,
                    section,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Command Table Output",
                    "PATH",
                    group,
                    section,
                    state_quant=f"{section} - Sequencer Program - Sequence",
                    state_values=["Rabi","Custom"],
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Waveform Channel 1",
                    "VECTOR",
                    group,
                    section,
                    permission="READ",
                    x_name="Length",
                    x_unit="Sample",
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Waveform Channel 2",
                    "VECTOR",
                    group,
                    section,
                    permission="READ",
                    x_name="Length",
                    x_unit="Sample",
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Waveform to View",
                    "DOUBLE",
                    group,
                    section,
                    def_value=0,
                    low_lim= 0,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    None,
                    "Download",
                    "BUTTON",
                    group,
                    section,
                    tooltip="Downloads the sequencer code from the device",
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )

            # Trigger
            group = f"Trigger"
            if "SHFSG4" in model_values:
                self.add_element(
                    Element(
                        f"sgchannels[{sgchannel}].awg.digital_trigger1_source",
                        "Digital Trigger 1 (SHFSG4)",
                        "COMBO",
                        group,
                        section,
                        def_value="Trigger In 1",
                        combo_defs=list(
                            (
                                "Trigger In 1",
                                "Trigger In 2",
                                "Trigger In 3",
                                "Trigger In 4",
                            )
                        ),
                        cmd_defs=list(range(4)),
                        model_values=["SHFSG4"],
                        show_in_measurement_dlg="False",
                        multi_section=True,
                    )
                )

            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.digital_trigger1_source",
                    "Digital Trigger 1 (SHFSG8)",
                    "COMBO",
                    group,
                    section,
                    def_value="Trigger In 1",
                    combo_defs=list(
                        (
                            "Trigger In 1",
                            "Trigger In 2",
                            "Trigger In 3",
                            "Trigger In 4",
                            "Trigger In 5",
                            "Trigger In 6",
                            "Trigger In 7",
                            "Trigger In 8",
                        )
                    ),
                    cmd_defs=list(range(8)),
                    model_values=["SHFSG8"],
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.digital_trigger1_slope",
                    "Digital Trigger 1 Slope",
                    "COMBO",
                    group,
                    section,
                    combo_defs=list(("level_sensitive", "rising_edge", "falling_edge", "both_edges")),
                    cmd_defs=list(range(4)),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            if "SHFSG4" in model_values:
                self.add_element(
                    Element(
                        f"sgchannels[{sgchannel}].awg.digital_trigger2_source",
                        "Digital Trigger 2 (SHFSG4)",
                        "COMBO",
                        group,
                        section,
                        def_value="Trigger In 1",
                        combo_defs=list(
                            (
                                "Trigger In 1",
                                "Trigger In 2",
                                "Trigger In 3",
                                "Trigger In 4",
                            )
                        ),
                        cmd_defs=list(range(4)),
                        model_values=["SHFSG4"],
                        show_in_measurement_dlg="False",
                        multi_section=True,
                    )
                )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.digital_trigger2_source",
                    "Digital Trigger 2 (SHFSG8)",
                    "COMBO",
                    group,
                    section,
                    def_value="Trigger In 1",
                    combo_defs=list(
                        (
                            "Trigger In 1",
                            "Trigger In 2",
                            "Trigger In 3",
                            "Trigger In 4",
                            "Trigger In 5",
                            "Trigger In 6",
                            "Trigger In 7",
                            "Trigger In 8",
                        )
                    ),
                    cmd_defs=list(range(8)),
                    model_values=["SHFSG8"],
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].awg.digital_trigger2_slope",
                    "Digital Trigger 2 Slope",
                    "COMBO",
                    group,
                    section,
                    combo_defs=list(("level_sensitive", "rising_edge", "falling_edge", "both_edges")),
                    cmd_defs=list(range(4)),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                    multi_section=True,
                )
            )

    def oscillator_section(self):
        section = "Oscillators"

        for sgchannel in range(8):
            group = f"SGChannel {sgchannel+1}"
            if sgchannel < 4:
                model_values = ["SHFSG4", "SHFSG8"]
            elif sgchannel >= 4:
                model_values = ["SHFSG8"]

            num_osc = 8
            self.add_element(
                Element(
                    None,
                    "SHOW",
                    "COMBO",
                    group,
                    section,
                    def_value=1,
                    combo_defs=list(range(1, num_osc + 1)),
                    cmd_defs=list(range(num_osc)),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            for osc in range(num_osc):
                self.add_element(
                    Element(
                        f"nodetree.sgchannels[{sgchannel}].oscs[{osc}].freq",
                        f"Oscillator {osc+1}",
                        "DOUBLE",
                        group,
                        section,
                        unit="Hz",
                        def_value=10e6,
                        state_quant=f"{group} - SHOW",
                        state_values=list(range(osc + 1, num_osc + 1)),
                        show_in_measurement_dlg="False",
                        model_values=model_values,
                    )
                )

    def sine_section(self):
        section = "Sines"

        for sgchannel in range(8):
            group = f"SGChannel {sgchannel+1}"
            if sgchannel < 4:
                model_values = ["SHFSG4", "SHFSG8"]
            elif sgchannel >= 4:
                model_values = ["SHFSG8"]

            num_osc = 8
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.osc_select",
                    "Oscillator",
                    "COMBO",
                    group,
                    section,
                    def_value=1,
                    combo_defs=list(range(1, num_osc + 1)),
                    cmd_defs=list(range(num_osc)),
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            # self.add_element(
            #     Element(
            #         f"sgchannels[{sgchannel}].sine.freq",
            #         "Frequency",
            #         "DOUBLE",
            #         group,
            #         section,
            #         permission="READ",
            #         model_values=model_values,
            #         show_in_measurement_dlg="False",
            #     )
            # )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.phase_shift",
                    "Phase",
                    "DOUBLE",
                    group,
                    section,
                    unit="deg",
                    def_value=0,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.i_enable",
                    "I Enable",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.i_sin",
                    "I SIN",
                    "Double",
                    group,
                    section,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.i_cos",
                    "I COS",
                    "Double",
                    group,
                    section,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.q_enable",
                    "Q Enable",
                    "BOOLEAN",
                    group,
                    section,
                    def_value=False,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.q_sin",
                    "Q SIN",
                    "Double",
                    group,
                    section,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )
            self.add_element(
                Element(
                    f"sgchannels[{sgchannel}].sine.q_cos",
                    "Q COS",
                    "Double",
                    group,
                    section,
                    model_values=model_values,
                    show_in_measurement_dlg="False",
                )
            )

    def dio_section(self):
        section = "DIO"

        # Digital I/O
        group = "Digital I/O"
        self.add_element(
            Element(
                None,
                "Mode",
                "COMBO",
                group,
                section,
                def_value="Manual",
                combo_defs=list(["Manual"]),
                cmd_defs=list(range(1)),
                set_cmd="/dios/0/mode",
                get_cmd="/dios/0/mode",
                show_in_measurement_dlg="False",
            )
        )
        self.add_element(
            Element(
                None,
                "Output",
                "DOUBLE",
                group,
                section,
                def_value=0,
                set_cmd="/dios/0/output",
                get_cmd="/dios/0/output",
                show_in_measurement_dlg="False",
            )
        )
        self.add_element(
            Element(
                None,
                "Drive",
                "DOUBLE",
                group,
                section,
                def_value=0,
                set_cmd="/dios/0/drive",
                get_cmd="/dios/0/drive",
                show_in_measurement_dlg="False",
            )
        )
        self.add_element(
            Element(
                None,
                "Interface",
                "COMBO",
                group,
                section,
                def_value="LVCMOS",
                combo_defs=list(("LVCMOS", "LVDS")),
                cmd_defs=list(range(2)),
                set_cmd="/dios/0/interface",
                get_cmd="/dios/0/interface",
                show_in_measurement_dlg="False",
            )
        )


test = SHFSG()
test.generate("DEV12050")
