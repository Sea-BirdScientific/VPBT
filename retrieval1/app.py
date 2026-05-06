from flask import Flask, render_template, request
import glob
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from scipy.interpolate import CubicSpline, LSQUnivariateSpline
except ImportError:
    CubicSpline = None
    LSQUnivariateSpline = None

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.io.pmt import PMTCal


app = Flask(__name__)

DEFAULT_DATA_DIR = "/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/355_532 VPBT/"
DEFAULT_STAGE = "og"
DEFAULT_WAVELENGTH = "355"
DEFAULT_TURBIDITY = "add1"
DEFAULT_CLEAR_WATER = "cw0"
DEFAULT_GAIN = 2.5
ALLOWED_GAINS = (2.5, 3.0)
DEFAULT_T0 = 1.305e-8
DEFAULT_T0_CW = DEFAULT_T0
DEFAULT_T0_TURB = DEFAULT_T0
DEFAULT_FIT_MIN = 0.1
DEFAULT_FIT_MAX = 2.0
DEFAULT_KNOTS = "0.5,1.5"
DEFAULT_FIT_MODE = "spline"
DEFAULT_EXPGRID = "/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/355_532 VPBT/ExpGrid-20260428.json"


def parse_gain_and_iris(csv_filepath):
    """Extract gain and iris position from CSV header."""
    gain_value = 2.0
    iris_mm = None

    try:
        with open(csv_filepath, "r") as f:
            line1 = f.readline().strip()
            line2 = f.readline().strip()

        gain_match = re.search(r"Gain\s*([\d.]+)", line1)
        if gain_match:
            gain_value = float(gain_match.group(1))

        iris_match = re.search(r"absolute position \(mm\):\s*([\d.]+)", line2)
        if iris_match:
            iris_mm = float(iris_match.group(1))
    except Exception:
        return gain_value, iris_mm

    return gain_value, iris_mm


def parse_turbidity_from_filename(filepath):
    """Decode turbidity index from filename: cw0, cw1, add1...add10."""
    name = os.path.basename(filepath).lower()
    match = re.search(r"_(cw\d+|add\d+)_water", name)
    if match:
        return match.group(1)
    return None


def find_turbidity_dir(root_dir, turbidity_key):
    """Find a subdirectory like CONFIG5_add1 or CONFIG5_cw0 under root."""
    candidates = sorted(glob.glob(os.path.join(root_dir, f"*_{turbidity_key}")))
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def is_water_only_file(filepath):
    """Keep only water files and ignore target/targe files."""
    name = os.path.basename(filepath).lower()
    return "water" in name and "target" not in name and "arget" not in name


def parse_knots(knots_str):
    if not knots_str.strip():
        return []
    parts = [p.strip() for p in knots_str.split(",")]
    knots = []
    for p in parts:
        if not p:
            continue
        knots.append(float(p))
    return knots

def load_expgrid(expgrid_path):
    with open(expgrid_path, "r") as f:
        meta = json.load(f)
    return meta 

def load_pmt_models(expgrid_path):
    meta = load_expgrid(expgrid_path)
    pmt_cal1 = PMTCal.from_expgrid(meta, "R9880U210")
    pmt_cal3 = PMTCal.from_expgrid(meta, "R9880U20")
    return pmt_cal1, pmt_cal3


def compute_ratio(wide_curve, narrow_curve):
    """Compute wide/narrow ratio with strict x-grid identity."""
    x_w, y_w = wide_curve
    x_n, y_n = narrow_curve

    if not (len(x_w) == len(x_n) and np.allclose(x_w, x_n)):
        return None

    eps = 1e-30
    ratio = np.where(np.abs(y_n) > eps, y_w / y_n, np.nan)

    valid = np.isfinite(ratio)
    if not np.any(valid):
        return None
    return x_n[valid], ratio[valid]


def select_one_curve(curves):
    """Return exactly one curve from candidates, preferring the first by filename."""
    if not curves:
        return None
    ordered = sorted(curves, key=lambda c: c[0])
    _, x, y = ordered[0]
    return x, y


def build_piecewise_cubic_fit(x, y, fit_min, fit_max, knots):
    """Fit ratio with cubic spline using user-specified internal knots."""
    mask = np.isfinite(x) & np.isfinite(y) & (x >= fit_min) & (x <= fit_max)
    xf = x[mask]
    yf = y[mask]
    if len(xf) < 6:
        return None, None, None

    order = np.argsort(xf)
    xf = xf[order]
    yf = yf[order]

    # Collapse duplicate x values by averaging.
    uniq_x, inv = np.unique(xf, return_inverse=True)
    sums = np.zeros_like(uniq_x, dtype=float)
    counts = np.zeros_like(uniq_x, dtype=float)
    for i, idx in enumerate(inv):
        sums[idx] += yf[i]
        counts[idx] += 1.0
    uniq_y = sums / np.maximum(counts, 1.0)

    if len(uniq_x) < 6:
        return None, None, None

    valid_knots = sorted([k for k in knots if fit_min < k < fit_max])

    # Try LSQ piecewise cubic with decreasing number of knots if needed.
    if LSQUnivariateSpline is not None:
        for n in range(len(valid_knots), -1, -1):
            trial_knots = valid_knots[:n]
            try:
                if n > 0:
                    spline = LSQUnivariateSpline(uniq_x, uniq_y, trial_knots, k=3)
                else:
                    if CubicSpline is None:
                        return None, None, None
                    spline = CubicSpline(uniq_x, uniq_y, bc_type="natural")
                fit_x = uniq_x
                fit_y = spline(fit_x)
                return spline, fit_x, fit_y
            except Exception:
                continue

    if CubicSpline is not None:
        try:
            spline = CubicSpline(uniq_x, uniq_y, bc_type="natural")
            fit_x = uniq_x
            fit_y = spline(fit_x)
            return spline, fit_x, fit_y
        except Exception:
            return None, None, None

    return None, None, None


def apply_running_median_mean(y, window=11):
    """Same-length smoothing: running median then running mean."""
    s = pd.Series(y)
    s = s.rolling(window=window, center=True, min_periods=1).median()
    s = s.rolling(window=window, center=True, min_periods=1).mean()
    return s.to_numpy()


def canonical_iris(iris_mm):
    """Map measured iris value to narrow/wide bins."""
    if iris_mm is None:
        return None
    if abs(iris_mm - 0.75) <= 0.05:
        return 0.75
    if abs(iris_mm - 1.5) <= 0.05:
        return 1.5
    return None


def load_stage_waveform(filepath, stage, t0, wavelength_nm, pmt_cal1, pmt_cal3):
    df = pd.read_csv(filepath, header=2)
    df = df.rename(columns={"time_s": "time", "ch1 voltage_v": "ch1", "ch3 voltage_v": "ch3"})
    required = {"time", "ch1", "ch3"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"Missing required columns in {os.path.basename(filepath)}")

    gain_value, iris_mm = parse_gain_and_iris(filepath)

    time = df["time"].values
    ch1 = df["ch1"].values
    ch3 = df["ch3"].values

    c0 = 299792458.0
    n = 1.33

    time_aligned = time - t0
    r = time_aligned * (c0 / n) / 2.0
    r_raw = time * (c0 / n) / 2.0

    ch1_o = ch1.copy()
    ch3_o = ch3.copy()

    ch1_og = None
    ch3_og = None
    if stage in ("og", "ogr"):
        if pmt_cal1 is None or pmt_cal3 is None:
            raise ValueError("PMT calibration is required for stage og/ogr")
        ch1_og = -pmt_cal1.volts_to_watts(
            volts=ch1_o,
            wavelength_nm=355,
            control_voltage_V=gain_value,
            supply_multiplier=250,
        )
        ch3_og = -pmt_cal3.volts_to_watts(
            volts=ch3_o,
            wavelength_nm=532,
            control_voltage_V=gain_value,
            supply_multiplier=250,
        )

    if stage == "raw":
        x = r_raw
        y355 = ch1
        y532 = ch3
    elif stage == "o":
        x = r
        y355 = ch1_o
        y532 = ch3_o
    elif stage == "og":
        x = r
        y355 = ch1_og
        y532 = ch3_og
    elif stage == "ogr":
        x = r
        y355 = np.multiply(ch1_og, r ** 2)
        y532 = np.multiply(ch3_og, r ** 2)
    else:
        raise ValueError(f"Unknown stage: {stage}")

    y = y355 if wavelength_nm == "355" else y532

    return {
        "x": x,
        "y": y,
        "gain": gain_value,
        "iris_mm": iris_mm,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    stage = request.form.get("stage", DEFAULT_STAGE)
    wavelength_nm = request.form.get("wavelength", DEFAULT_WAVELENGTH)
    selected_turbidity = request.form.get("turbidity", DEFAULT_TURBIDITY)
    clear_water_turbidity = request.form.get("clear_water", DEFAULT_CLEAR_WATER)
    fit_mode = request.form.get("fit_mode", DEFAULT_FIT_MODE)
    selected_gain_str = request.form.get("gain", f"{DEFAULT_GAIN:g}")
    directory = request.form.get("directory", DEFAULT_DATA_DIR)
    expgrid_path = request.form.get("expgrid_path", DEFAULT_EXPGRID)

    if fit_mode not in ("spline", "mean", "filtering"):
        fit_mode = DEFAULT_FIT_MODE

    # try:
    #     t0_cw = float(request.form.get("t0_cw", str(DEFAULT_T0_CW)))
    # except ValueError:
    #     t0_cw = DEFAULT_T0_CW

    # try:
    #     t0_turb = float(request.form.get("t0_turb", str(DEFAULT_T0_TURB)))
    # except ValueError:
    #     t0_turb = DEFAULT_T0_TURB

    try:
        fit_min = float(request.form.get("fit_min", str(DEFAULT_FIT_MIN)))
    except ValueError:
        fit_min = DEFAULT_FIT_MIN

    try:
        fit_max = float(request.form.get("fit_max", str(DEFAULT_FIT_MAX)))
    except ValueError:
        fit_max = DEFAULT_FIT_MAX

    try:
        selected_gain = float(selected_gain_str)
    except ValueError:
        selected_gain = DEFAULT_GAIN
        selected_gain_str = f"{DEFAULT_GAIN:g}"

    if selected_gain not in ALLOWED_GAINS:
        selected_gain = DEFAULT_GAIN
        selected_gain_str = f"{DEFAULT_GAIN:g}"

    knots_str = request.form.get("knots", DEFAULT_KNOTS)
    try:
        knots = parse_knots(knots_str)
    except ValueError:
        knots = parse_knots(DEFAULT_KNOTS)
        knots_str = DEFAULT_KNOTS

    if fit_max <= fit_min:
        fit_min, fit_max = DEFAULT_FIT_MIN, DEFAULT_FIT_MAX

    errors = []

    pmt_cal1 = None
    pmt_cal3 = None
    if stage in ("og", "ogr"):
        try:
            pmt_cal1, pmt_cal3 = load_pmt_models(expgrid_path)
        except Exception as e:
            errors.append(f"Could not load PMT calibration metadata: {e}")

    meta = load_expgrid(expgrid_path)
    t0_cw   = meta['trials'][clear_water_turbidity]['t0'] if 'trials' in meta and clear_water_turbidity in meta['trials'] and 't0' in meta['trials'][clear_water_turbidity] else DEFAULT_T0_CW
    t0_turb = meta['trials'][selected_turbidity]['t0'] if 'trials' in meta and selected_turbidity in meta['trials'] and 't0' in meta['trials'][selected_turbidity] else DEFAULT_T0_TURB

    cw_dir = find_turbidity_dir(directory, clear_water_turbidity)
    turb_dir = find_turbidity_dir(directory, selected_turbidity)

    cw_all_files = sorted(glob.glob(os.path.join(cw_dir, "*.csv"))) if cw_dir else []
    turb_all_files = sorted(glob.glob(os.path.join(turb_dir, "*.csv"))) if turb_dir else []

    cw_water_files = [f for f in cw_all_files if is_water_only_file(f)]
    turb_water_files = [f for f in turb_all_files if is_water_only_file(f)]

    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for turbidity, t0_use, file_list in [
        (clear_water_turbidity, t0_cw, cw_water_files),
        (selected_turbidity, t0_turb, turb_water_files),
    ]:
        for filepath in file_list:
            try:
                wf = load_stage_waveform(filepath, stage, t0_use, wavelength_nm, pmt_cal1, pmt_cal3)
            except Exception as e:
                errors.append(f"Skipped {os.path.basename(filepath)}: {e}")
                continue

            iris_key = canonical_iris(wf["iris_mm"])
            if iris_key is None:
                continue

            gain_key = round(float(wf["gain"]), 6)
            grouped[turbidity][gain_key][iris_key].append((filepath, wf["x"], wf["y"]))

    selected_gain_key = round(float(selected_gain), 6)

    cw_ratio = None
    cw_spline = None
    cw_fit_line = None
    cw_mean_level = None
    cw_filter_fit = None

    cw_iris_map = grouped.get(clear_water_turbidity, {}).get(selected_gain_key, {})
    cw_wide = select_one_curve(cw_iris_map.get(1.5, []))
    cw_narrow = select_one_curve(cw_iris_map.get(0.75, []))
    if cw_wide is not None and cw_narrow is not None:
        cw_ratio = compute_ratio(cw_wide, cw_narrow)
        if cw_ratio is None:
            errors.append("CW wide and narrow x-grids are not identical for selected gain.")
        else:
            x_ratio, y_ratio = cw_ratio
            if fit_mode == "filtering":
                valid_full = np.isfinite(x_ratio) & np.isfinite(y_ratio)
                if np.any(valid_full):
                    fit_x_full = x_ratio[valid_full]
                    fit_y_full = y_ratio[valid_full]
                    fit_y_filtered = apply_running_median_mean(fit_y_full, window=41)
                    cw_filter_fit = (fit_x_full, fit_y_filtered)
                    cw_fit_line = cw_filter_fit
            else:
                fit_mask = np.isfinite(x_ratio) & np.isfinite(y_ratio) & (x_ratio >= fit_min) & (x_ratio <= fit_max)
                if np.any(fit_mask):
                    fit_x_base = x_ratio[fit_mask]
                    fit_y_base = y_ratio[fit_mask]
                    if fit_mode == "mean":
                        cw_mean_level = float(np.mean(fit_y_base))
                        cw_fit_line = (fit_x_base, np.full_like(fit_x_base, cw_mean_level, dtype=float))
                    else:
                        spline, fit_x, fit_y = build_piecewise_cubic_fit(x_ratio, y_ratio, fit_min, fit_max, knots)
                        if spline is not None:
                            cw_spline = spline
                            cw_fit_line = (fit_x, fit_y)

    turb_ratio = None
    turb_iris_map = grouped.get(selected_turbidity, {}).get(selected_gain_key, {})
    turb_wide = select_one_curve(turb_iris_map.get(1.5, []))
    turb_narrow = select_one_curve(turb_iris_map.get(0.75, []))
    if turb_wide is not None and turb_narrow is not None:
        turb_ratio = compute_ratio(turb_wide, turb_narrow)
        if turb_ratio is None:
            errors.append("Selected turbidity wide and narrow x-grids are not identical for selected gain.")

    attenuation = None
    if turb_ratio is not None and (cw_spline is not None or cw_mean_level is not None or cw_filter_fit is not None):
        x_turb, kprime = turb_ratio
        if cw_mean_level is not None:
            kr_fit = np.full_like(x_turb, cw_mean_level, dtype=float)
        elif cw_filter_fit is not None:
            fit_x, fit_y = cw_filter_fit
            kr_fit = np.interp(x_turb, fit_x, fit_y, left=np.nan, right=np.nan)
        else:
            kr_fit = cw_spline(x_turb)

        valid = (
            np.isfinite(x_turb)
            & np.isfinite(kprime)
            & np.isfinite(kr_fit)
            & (x_turb > 0.0)
            & (kprime > 0.0)
            & (kr_fit > 0.0)
        )
        if np.any(valid):
            x_valid = x_turb[valid]
            c_val = (-1.0 / (2.0 * x_valid)) * np.log(kprime[valid] / kr_fit[valid])
            finite = np.isfinite(c_val)
            if np.any(finite):
                attenuation = (x_valid[finite], c_val[finite])

    fig = make_subplots(
        rows=3,
        cols=2,
        shared_xaxes="all",
        specs=[[{}, {}], [{}, {}], [None, {}]],
        subplot_titles=(
            f"CW Waveforms Used For K_R ({wavelength_nm} nm)",
            f"K_R (CW: {clear_water_turbidity}) at {wavelength_nm} nm",
            f"{selected_turbidity} Waveforms Used For K'_R ({wavelength_nm} nm)",
            f"K'_R ({selected_turbidity}) at {wavelength_nm} nm",
            "",
            "c(gain, r)",
        ),
    )

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]

    if cw_ratio is not None:
        x_ratio, y_ratio = cw_ratio
        color = colors[0]
        fig.add_trace(
            go.Scatter(
                x=x_ratio,
                y=y_ratio,
                mode="lines",
                name=f"CW raw gain {selected_gain_key:g}",
                line=dict(color=color, width=1.5),
                hovertemplate="r=%{x:.3f} m<br>K_R=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=1,
            col=2,
        )

    if cw_fit_line is not None:
        fit_x, fit_y = cw_fit_line
        fit_color = "#111111"
        fit_name = f"CW {fit_mode} fit gain {selected_gain_key:g}"
        fig.add_trace(
            go.Scatter(
                x=fit_x,
                y=fit_y,
                mode="lines",
                name=fit_name,
                line=dict(color=fit_color, width=3, dash="dot"),
                hovertemplate="r=%{x:.3f} m<br>K_R,fit=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=1,
            col=2,
        )

        # Show knot locations as markers on the fitted curve for interactive tuning.
        knot_x = sorted([k for k in knots if fit_min < k < fit_max and fit_x[0] <= k <= fit_x[-1]])
        if fit_mode == "spline" and knot_x and cw_spline is not None:
            knot_x_arr = np.array(knot_x, dtype=float)
            knot_y_arr = cw_spline(knot_x_arr)
            fig.add_trace(
                go.Scatter(
                    x=knot_x_arr,
                    y=knot_y_arr,
                    mode="markers",
                    name="CW fit knots",
                    marker=dict(color="#ff006e", size=10, symbol="diamond"),
                    hovertemplate="knot r=%{x:.3f} m<br>K_R,fit=%{y:.3f}<extra>%{fullData.name}</extra>",
                ),
                row=1,
                col=2,
            )

    if cw_wide is not None:
        x_w, y_w = cw_wide
        fig.add_trace(
            go.Scatter(
                x=x_w,
                y=y_w,
                mode="lines",
                name=f"CW wide (1.5 mm) gain {selected_gain_key:g}",
                line=dict(color="#7c3aed", width=2),
                hovertemplate="r=%{x:.3f} m<br>P_W=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=1,
            col=1,
        )

    if cw_narrow is not None:
        x_n, y_n = cw_narrow
        fig.add_trace(
            go.Scatter(
                x=x_n,
                y=y_n,
                mode="lines",
                name=f"CW narrow (0.75 mm) gain {selected_gain_key:g}",
                line=dict(color="#0ea5e9", width=2),
                hovertemplate="r=%{x:.3f} m<br>P_N=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=1,
            col=1,
        )

    if turb_ratio is not None:
        x_ratio, y_ratio = turb_ratio
        color = colors[1]
        fig.add_trace(
            go.Scatter(
                x=x_ratio,
                y=y_ratio,
                mode="lines",
                name=f"{selected_turbidity} gain {selected_gain_key:g}",
                line=dict(color=color, width=2),
                hovertemplate="r=%{x:.3f} m<br>K'_R=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=2,
            col=2,
        )

    if turb_wide is not None:
        x_w, y_w = turb_wide
        fig.add_trace(
            go.Scatter(
                x=x_w,
                y=y_w,
                mode="lines",
                name=f"{selected_turbidity} wide (1.5 mm) gain {selected_gain_key:g}",
                line=dict(color="#7c3aed", width=2),
                hovertemplate="r=%{x:.3f} m<br>P'_W=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=2,
            col=1,
        )

    if turb_narrow is not None:
        x_n, y_n = turb_narrow
        fig.add_trace(
            go.Scatter(
                x=x_n,
                y=y_n,
                mode="lines",
                name=f"{selected_turbidity} narrow (0.75 mm) gain {selected_gain_key:g}",
                line=dict(color="#0ea5e9", width=2),
                hovertemplate="r=%{x:.3f} m<br>P'_N=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=2,
            col=1,
        )

    if attenuation is not None:
        x_c, c_val = attenuation
        color = colors[2]
        fig.add_trace(
            go.Scatter(
                x=x_c,
                y=c_val,
                mode="lines",
                name=f"c gain {selected_gain_key:g}",
                line=dict(color=color, width=2),
                hovertemplate="r=%{x:.3f} m<br>c=%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=3,
            col=2,
        )

    y_label = "Signal (W)" if stage in ("og", "ogr") else "Signal (V)"
    fig.update_xaxes(title_text=None, row=1, col=1)
    fig.update_xaxes(title_text=None, row=1, col=2)
    fig.update_xaxes(title_text=None, row=2, col=1)
    fig.update_xaxes(title_text="Range r (m)", row=3, col=2)
    fig.update_xaxes(title_text=None, row=2, col=2)
    fig.update_xaxes(showticklabels=True, row=1, col=1)
    fig.update_xaxes(showticklabels=True, row=1, col=2)
    fig.update_xaxes(showticklabels=True, row=2, col=1)
    fig.update_xaxes(showticklabels=True, row=2, col=2)
    fig.update_xaxes(showticklabels=True, row=3, col=2)
    fig.update_yaxes(title_text=y_label, row=1, col=1)
    fig.update_yaxes(title_text="K_R", row=1, col=2)
    fig.update_yaxes(title_text=y_label, row=2, col=1)
    fig.update_yaxes(title_text="K'_R", row=2, col=2)
    fig.update_yaxes(title_text="c (1/m)", row=3, col=2)
    fig.update_yaxes(range=[-0.1, 0.5], row=3, col=2)

    fig.update_layout(
        height=1100,
        hovermode="x unified",
        hoverlabel=dict(namelength=-1),
        legend=dict(
            x=1.02,
            y=1.0,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#cccccc",
            borderwidth=1,
        ),
        title=(
            f"Water-only retrieval | stage={stage} | wavelength={wavelength_nm} nm | "
            f"CW={clear_water_turbidity} | turbidity={selected_turbidity} | gain={selected_gain_str} V |"
            f"t0 CW={t0_cw:.3e} s | t0 turb={t0_turb:.3e} s "
        ),
    )

    if cw_wide is None or cw_narrow is None:
        errors.append("Missing CW wide/narrow pair for the selected gain.")
    if turb_wide is None or turb_narrow is None:
        errors.append("Missing selected turbidity wide/narrow pair for the selected gain.")
    if cw_ratio is not None and cw_fit_line is None:
        if fit_mode == "mean":
            errors.append("Could not build CW mean fit in the selected fit range.")
        elif fit_mode == "filtering":
            errors.append("Could not build CW filtering fit in the selected fit range.")
        else:
            errors.append("Could not build CW piecewise cubic fit in the selected fit range.")
    if attenuation is None:
        errors.append("No attenuation curve computed for selected gain (requires valid CW fit and selected turbidity ratio).")

    if cw_dir is None:
        errors.append(f"Could not find directory for clear water key: {clear_water_turbidity}")
    if turb_dir is None:
        errors.append(f"Could not find directory for turbidity key: {selected_turbidity}")

    plot_html = fig.to_html(full_html=False)

    return render_template(
        "index.html",
        plot_html=plot_html,
        errors=errors,
        stage=stage,
        wavelength=wavelength_nm,
        turbidity=selected_turbidity,
        clear_water=clear_water_turbidity,
        fit_mode=fit_mode,
        gain=selected_gain_str,
        directory=directory,
        cw_dir=os.path.basename(cw_dir) if cw_dir else "n/a",
        turb_dir=os.path.basename(turb_dir) if turb_dir else "n/a",
        fit_min=fit_min,
        fit_max=fit_max,
        knots=knots_str,
        expgrid_path=expgrid_path,
        cw_file_count=len(cw_all_files),
        turb_file_count=len(turb_all_files),
        cw_water_file_count=len(cw_water_files),
        turb_water_file_count=len(turb_water_files),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
