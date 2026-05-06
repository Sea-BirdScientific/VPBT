from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, Optional

def load_rigol_csv(csv_path: str | Path, mapping: Dict[str,str]) -> Dict[str, np.ndarray]:
    df = pd.read_csv(csv_path)
    out: Dict[str, np.ndarray] = {}
    for raw_col, alias in mapping.items():
        if alias == 'Ignore':
            continue
        if raw_col in df.columns:
            out[alias] = df[raw_col].to_numpy()
    return out

def align_time_zero(time_s: np.ndarray, t_win_s: float) -> np.ndarray:
    return time_s - float(t_win_s)

