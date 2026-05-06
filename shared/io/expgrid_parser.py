from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

@dataclass
class ExpGridRow:
    trial_label: str
    dataset: int
    fov_label: Optional[str]
    target_dist_m: Optional[float]
    a_532: Optional[float]
    c_532: Optional[float]
    date: Optional[str]
    time: Optional[str]
    pmt_control_V: Optional[float]
    # file/glob info
    root_dir: Optional[str]
    rel_raw_dir: Optional[str]
    pattern_fstring: Optional[str]
    path_glob_primary: Optional[str]
    # waveform alignment
    t_win_s: Optional[float]
    # FOV geometry if available
    iris_diameter_mm: Optional[float]
    iris_fov_deg: Optional[float]
    # instrument/PMT meta
    pmt_model: Optional[str]
    pmt_resistance_ohms: Optional[float]
    pmt_supply_voltage_multiplier: Optional[float]
    pmt_rel_path: Optional[str]
    pmt_resp_file: Optional[str]
    pmt_gain_file: Optional[str]
    # NEW: laser fields
    laser_name: Optional[str]
    laser_wavelength_nm: Optional[float]
    laser_average_power_mW: Optional[float]
    laser_prr_kHz: Optional[float]
    # mapping
    mapping_json: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def _safe_get(d: Dict[str, Any], key: str, default=None):
    return d.get(key, default) if isinstance(d, dict) else default

def _at_or_none(seq, idx):
    try:
        return seq[idx]
    except Exception:
        return None

def _join_paths(root_dir: Optional[str], rel: Optional[str], name: str) -> Optional[str]:
    parts = [p for p in [root_dir, rel, name] if p]
    return '/'.join([p.rstrip('/').lstrip('/') if i>0 else p.rstrip('/') for i, p in enumerate(parts)]) if parts else None

# --- NEW: normalize PMT_control_V (singleton or per-dataset list) ---
def _normalize_pmt_control(value, n: int, trial_label: str) -> List[Optional[float]]:
    """Normalize trials.<label>.PMT_control_V to a list of length n.
       - number -> broadcast to length n
       - list/tuple -> must match length n
       - missing/None -> [None]*n
    """
    if value is None:
        return [None] * n
    if isinstance(value, (int, float)):
        return [float(value)] * n
    if isinstance(value, (list, tuple)):
        if len(value) != n:
            raise ValueError(
                f"PMT_control_V length {len(value)} != datasets length {n} for trial='{trial_label}'"
            )
        return [float(x) for x in value]
    raise TypeError(f"Unsupported PMT_control_V type {type(value)} for trial='{trial_label}'")

def parse_expgrid(json_obj: Dict[str, Any]) -> List[ExpGridRow]:
    root_dir = _safe_get(json_obj, 'rootDir')
    files = _safe_get(json_obj, 'files', {})
    rel_raw = _safe_get(files, 'relative_path_to_raw_files')
    pattern = _safe_get(files, 'pattern_fstring')
    mapping = _safe_get(files, 'mapping', {})

    optics = _safe_get(json_obj, 'optics', {})
    t_win_s = _safe_get(optics, 't_win_sec')
    iris_diam = _safe_get(optics, 'iris_diameter_mm', {})
    iris_fov_deg = _safe_get(optics, 'iris_fov_in_water_degrees', {})

    pmts = _safe_get(json_obj, 'pmts', {})
    default_pmt = _safe_get(pmts, 'default_pmt')
    pmt_block = _safe_get(pmts, default_pmt, {}) if default_pmt else {}
    pmt_res_ohm = _safe_get(pmt_block, 'resistance_ohms')
    pmt_mult = _safe_get(pmt_block, 'PMT_supply_voltage_multiplier')
    # relative path may be at pmts level or inside specific model block
    pmt_rel_path = _safe_get(pmts, 'relative_path_to_PMT_files')
    if pmt_rel_path is None:
        pmt_rel_path = _safe_get(pmt_block, 'relative_path_to_PMT_files')
    # files live under the model block
    resp_file = _safe_get(_safe_get(pmt_block, 'responsivity', {}), 'file')
    gain_file = _safe_get(_safe_get(pmt_block, 'gain', {}), 'file')

    lasers = _safe_get(json_obj, 'lasers', {}) or {}
    # default laser name: if only one entry, use it; else None until overridden per trial
    default_laser_name = next(iter(lasers.keys())) if len(lasers) == 1 else None

    def laser_props(lname: Optional[str]):
        if not lname:
            return None, None, None, None
        L = _safe_get(lasers, lname, {})
        return (
            lname,
            _safe_get(L, 'wavelength_nm'),
            _safe_get(L, 'average_power_mW'),
            _safe_get(L, 'pulse_repetition_rate_kHz') or _safe_get(L, 'pulse_repetition_rate', None),
        )

    trials = _safe_get(json_obj, 'trials', {})
    rows: List[ExpGridRow] = []
    for label, t in trials.items():
        datasets = _safe_get(t, 'datasets', []) or []
        fovs = _safe_get(t, 'fov', []) or []
        target_dist = _safe_get(t, 'target_dist_m', []) or []
        a_list = _safe_get(t, 'a_532', []) or _safe_get(t, "a_532'", []) or []
        c_list = _safe_get(t, 'c_532', []) or _safe_get(t, "c_532'", []) or []
        times = _safe_get(t, 'time', []) or []
        date = _safe_get(t, 'date')
        # NEW: normalize PMT_control_V per dataset
        pmt_ctrl_raw = _safe_get(t, 'PMT_control_V')
        pmt_ctrl_list = _normalize_pmt_control(pmt_ctrl_raw, len(datasets), label)

        for i, dset in enumerate(datasets):
            dset_int = int(dset)
            fov_i = _at_or_none(fovs, i)

            iris_mm = None
            iris_deg = None
            if isinstance(fov_i, str):
                iris_mm = _safe_get(iris_diam, fov_i)
                iris_deg = _safe_get(iris_fov_deg, fov_i)
            try:
                iris_mm = float(iris_mm) if iris_mm is not None else None
            except Exception:
                pass
            try:
                iris_deg = float(iris_deg) if iris_deg is not None else None
            except Exception:
                pass

            # Allow per-trial override in future: trials.<label>.laser = "Horus" etc.
            trial_laser_name = _safe_get(t, 'laser', default_laser_name)
            lname, lwl, lpwr, lprr = laser_props(trial_laser_name)

            row = ExpGridRow(
                trial_label=label,
                dataset=dset_int,
                fov_label=fov_i,
                target_dist_m=_at_or_none(target_dist, i),
                a_532=_at_or_none(a_list, i),
                c_532=_at_or_none(c_list, i),
                date=date,
                time=_at_or_none(times, i),
                pmt_control_V=_at_or_none(pmt_ctrl_list, i),
                root_dir=root_dir,
                rel_raw_dir=rel_raw,
                pattern_fstring=pattern,
                path_glob_primary=None,
                t_win_s=t_win_s,
                iris_diameter_mm=iris_mm,
                iris_fov_deg=iris_deg,
                pmt_model=default_pmt,
                pmt_resistance_ohms=pmt_res_ohm,
                pmt_supply_voltage_multiplier=pmt_mult,
                pmt_rel_path=pmt_rel_path,
                pmt_resp_file=resp_file,
                pmt_gain_file=gain_file,
                laser_name=lname,
                laser_wavelength_nm=lwl,
                laser_average_power_mW=lpwr,
                laser_prr_kHz=lprr,
                mapping_json=json.dumps(mapping) if mapping else None,
            )

            if isinstance(pattern, str):
                try:
                    prefix = pattern.format(dataset=dset_int)
                    row.path_glob_primary = _join_paths(root_dir, rel_raw, prefix)
                except Exception:
                    row.path_glob_primary = None

            rows.append(row)
    return rows