"""Optional piano-specialized Transkun V2 inference with packaged weights."""
from functools import lru_cache
from importlib.resources import files
import threading
import numpy as np

_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def _model(device):
    import torch
    import moduleconf
    from transkun import __name__ as package
    root = files(package).joinpath('pretrained')
    config = moduleconf.parseFromFile(str(root.joinpath('2.0.conf')))
    model = config['Model'].module.TransKun(conf=config['Model'].config)
    # Only the trusted checkpoint bundled with the pinned package is loaded.
    checkpoint = torch.load(str(root.joinpath('2.0.pt')), map_location='cpu', weights_only=False)
    model.load_state_dict(checkpoint.get('best_state_dict', checkpoint.get('state_dict')), strict=True)
    return model.to(device).eval()


def transcribe_piano(audio, rate, device='auto'):
    try:
        import torch
        import soxr
        from transkun.Data import writeMidi
    except ImportError as exc:
        raise RuntimeError('Run INSTALL_PIANO_WINDOWS.bat again to install Transkun V2, then restart the app.') from exc
    if device not in ('auto', 'cpu', 'cuda'):
        raise ValueError('Choose auto, cpu or cuda.')
    device = ('cuda' if torch.cuda.is_available() else 'cpu') if device == 'auto' else device
    if device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Choose CPU or install the NVIDIA model dependencies.')
    with _LOCK, torch.inference_mode():
        model = _model(device)
        wave = np.asarray(audio, dtype=np.float32)
        if wave.ndim == 1:
            wave = wave[:, None]
        if rate != model.fs:
            wave = soxr.resample(wave, rate, model.fs)
        detected = model.transcribe(torch.from_numpy(wave.copy()).to(device), discardSecondHalf=False)
        return writeMidi(detected)
