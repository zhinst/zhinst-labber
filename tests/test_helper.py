import numpy as np
from zhinst.toolkit import Waveforms
from zhinst.labber import export_waveforms
from pathlib import Path

def test_waveform_export():
    wave = Waveforms()
    wave[0] = (np.ones(100),None,None)
    wave[2] = (2*np.ones(100),4*np.ones(100),None)
    wave[3] = (np.ones(100),np.ones(100),np.ones(100))
    out_dir = Path("waveform_test")

    if out_dir.exists():
        out_dir.rmdir()
    out_dir.mkdir()

    export_waveforms(wave, out_dir)

    assert (out_dir/"wave1").exists()
    assert (out_dir/"wave2").exists()
    assert (out_dir/"makers").exists()


