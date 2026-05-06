from flask import Flask, json, request, render_template
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.io.pmt import PMTCal


app = Flask(__name__)


def parse_iris_mm(iris_label):
    """Parse iris label like '1.5 mm' into a float value in mm."""
    match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*mm', str(iris_label))
    if match:
        return float(match.group(1))
    return None


def parse_target_distance_label(filepath):
    """Parse target distance from filename and return a display label."""
    filename = os.path.basename(filepath).lower()

    # Handle both 'target' and the observed typo form 'targe'.
    match = re.search(r'targe?t([0-9]+(?:_[0-9]+)?)m', filename)
    if match:
        distance_str = match.group(1).replace('_', '.')
        try:
            distance_val = float(distance_str)
            return f"{distance_val:g} m"
        except ValueError:
            pass

    if 'water' in filename:
        return 'Water'

    return 'Target n/a'

def extract_iris_position(csv_filepath):
    """Extract iris absolute position from second line of CSV header."""
    try:
        with open(csv_filepath, 'r') as f:
            # Read first two lines
            line1 = f.readline().strip()
            line2 = f.readline().strip()
        
        # Look for pattern like "Gain 3.0"
        match = re.search(r'Gain\s*([\d.]+)\s*', line1)
        if match:
            gain_value = float(match.group(1)) # value
        else:
            gain_value = 2.0    # default if not found

        # Look for pattern like "ELL15Z absolute position (mm): 5"
        match = re.search(r'absolute position \(mm\):\s*([0-9.]+)', line2)
        if match:
            iris_position = f"{match.group(1)} mm"
            return iris_position, gain_value
    except Exception:
        pass
    
    # Default fallback
    return os.path.basename(csv_filepath), 2.0

def load_and_process_file(filepath, stage, x_axis, t0, pmt_cal1=None, pmt_cal3=None):
    """Load a single CSV file and process through pipeline."""
    try:
        df = pd.read_csv(filepath, header=2)
        df = df.rename(columns={'time_s': 'time', 'ch1 voltage_v': 'ch1', 'ch3 voltage_v': 'ch3'})
        iris_position, gain_value = extract_iris_position(filepath)

        time = df['time'].values
        ch1 = df['ch1'].values
        ch3 = df['ch3'].values
        
        c0 = 299792458.0
        n = 1.33
        
        time_aligned = time - t0
        r = time_aligned * (c0 / n) / 2
        r_raw = time * (c0 / n) / 2

        # Pipeline
        # Offset (PMT dark voltage) tbs
        ch1_o = ch1.copy()
        ch3_o = ch3.copy()

        # Gain correction using PMT responsivity and gain models from ExpGrid metadata
        # g1 = 1.0
        # g3 = 1.0
        # ch1_og = ch1_o / g1
        # ch3_og = ch3_o / g3
        ch1_og = -pmt_cal1.volts_to_watts(
            volts=ch1_o,            # numpy vector from Rigol CSV
            wavelength_nm=355,      # for now (we’ll add 355 nm later)
            control_voltage_V=gain_value,
            supply_multiplier=250
        )
        ch3_og = -  pmt_cal3.volts_to_watts(
            volts=ch3_o,            # numpy vector from Rigol CSV
            wavelength_nm=532,      # for now (we’ll add 355 nm later)
            control_voltage_V=gain_value,
            supply_multiplier=250
        )
        
        # Range correction (multiply by r^2 to compensate for 1/r^2 loss)
        # ch1_ogr = np.multiply(ch1_og, r_raw**2)
        # ch3_ogr = np.multiply(ch3_og, r_raw**2)
        ch1_ogr = np.multiply(ch1_og, r**2)
        ch3_ogr = np.multiply(ch3_og, r**2)
        
        # Select data based on stage
        if stage == 'raw':
            y1, y3 = ch1, ch3
            x = time if x_axis == 'time' else r_raw
        elif stage == 'o':
            y1, y3 = ch1_o, ch3_o
            x = time_aligned if x_axis == 'time' else r
        elif stage == 'og':
            y1, y3 = ch1_og, ch3_og
            x = time_aligned if x_axis == 'time' else r
        elif stage == 'ogr':
            y1, y3 = ch1_ogr, ch3_ogr
            x = time_aligned if x_axis == 'time' else r
        else:
            y1, y3 = ch1, ch3
            x = time if x_axis == 'time' else r_raw
        
        return x, y1, y3, iris_position, gain_value
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    # Default values
    stage = request.form.get('stage', 'raw')
    x_axis = request.form.get('x_axis', 'time')
    t0_str = request.form.get('t0', '-1.305e-8')
    directory = request.form.get('directory', '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/355_532 VPBT/')
    pattern = request.form.get('pattern', '*.csv')
    narrow_iris_str = request.form.get('narrow_iris', '0.75')
    wide_iris_str = request.form.get('wide_iris', '1.5')
    
    try:
        t0 = float(t0_str)
    except ValueError:
        t0 = 1.305e-8

    try:
        narrow_iris_mm = float(narrow_iris_str)
    except ValueError:
        narrow_iris_mm = 0.75

    try:
        wide_iris_mm = float(wide_iris_str)
    except ValueError:
        wide_iris_mm = 1.5
    
    # Load PMT calibration models from ExpGrid metadata 
    meta = json.load(open('../data/355_532 VPBT/ExpGrid-20260428.json','r'))
    PMT1 = 'R9880U210'  # UV PMT
    PMT3 = 'R9880U20'   # Green PMT
    pmt_cal1 = PMTCal.from_expgrid(meta, PMT1)  # uses rootDir / pmts.relative_path_to_PMT_files
    pmt_cal3 = PMTCal.from_expgrid(meta, PMT3)  # uses rootDir / pmts.relative_path_to_PMT_files`'

    # Determine x-axis label
    x_label = 'Time (s)' if x_axis == 'time' else 'Range (m)'
    if stage in ['o', 'og', 'ogr']:
        x_label = 'Time Aligned (s)' if x_axis == 'time' else 'Range (m)'
    
    # Find matching files
    search_path = os.path.join(directory, pattern)
    files = sorted(glob.glob(search_path))
    
    # Create subplots with separate legend groups
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=(
            '<span style="color:violet">CH1 (355 nm)</span>',
            '<span style="color:green">CH3 (532 nm)</span>',
            f'Ratio Wide:Narrow ({wide_iris_mm:g} mm:{narrow_iris_mm:g} mm)'
        )
    )
    
    # Define a color palette to reuse
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # Track labels for custom legend annotations
    labels = []
    ratio_traces = {}
    gain_value = 'n/a'
    
    # Load and plot each file
    for idx, filepath in enumerate(files):
        result = load_and_process_file(filepath, stage, x_axis, t0, pmt_cal1, pmt_cal3)
        if result is not None:
            x, y1, y3, iris_position, gain_value = result
            print(iris_position, gain_value)
            color = colors[idx % len(colors)]
            distance_label = parse_target_distance_label(filepath)
            legend_label = f"{distance_label}, {iris_position}, {gain_value}V"
            labels.append((legend_label, color))

            iris_mm = parse_iris_mm(iris_position)
            if iris_mm is not None and iris_mm not in ratio_traces:
                ratio_traces[iris_mm] = (x, y1, y3)
            
            # Add CH1 trace to row 1 (show in legend)
            fig.add_trace(
                go.Scatter(x=x, y=y1, mode='lines', name=legend_label,
                          line=dict(color=color),
                          legendgroup=f'group_{idx}'),
                row=1, col=1
            )
            
            # Add CH3 trace to row 2 (hide from main legend, will use custom annotation)
            fig.add_trace(
                go.Scatter(x=x, y=y3, mode='lines', name=legend_label,
                          line=dict(color=color),
                          legendgroup=f'group_{idx}',
                          showlegend=False),
                row=2, col=1
            )

    # Build Wide:Narrow ratio for selected iris positions when both are available.
    narrow_trace = ratio_traces.get(narrow_iris_mm)
    wide_trace = ratio_traces.get(wide_iris_mm)
    ratio_available = False
    if narrow_trace is not None and wide_trace is not None:
        ratio_available = True
        x_n, ch1_n, ch3_n = narrow_trace
        x_w, ch1_w, ch3_w = wide_trace

        if len(x_n) == len(x_w) and np.allclose(x_n, x_w):
            x_ratio = x_n
            ch1_w_aligned = ch1_w
            ch3_w_aligned = ch3_w
        else:
            x_ratio = x_n
            ch1_w_aligned = np.interp(x_ratio, x_w, ch1_w)
            ch3_w_aligned = np.interp(x_ratio, x_w, ch3_w)

        eps = 1e-30
        ch1_ratio = np.where(np.abs(ch1_n) > eps, ch1_w_aligned / ch1_n, np.nan)
        ch3_ratio = np.where(np.abs(ch3_n) > eps, ch3_w_aligned / ch3_n, np.nan)

        fig.add_trace(
            go.Scatter(
                x=x_ratio,
                y=ch1_ratio,
                mode='lines',
                name=f'CH1 W:N {wide_iris_mm:g}:{narrow_iris_mm:g} mm',
                line=dict(color='#1f77b4', width=2)
            ),
            row=3,
            col=1
        )
        fig.add_trace(
            go.Scatter(
                x=x_ratio,
                y=ch3_ratio,
                mode='lines',
                name=f'CH3 W:N {wide_iris_mm:g}:{narrow_iris_mm:g} mm',
                line=dict(color='#2ca02c', width=2, dash='dash')
            ),
            row=3,
            col=1
        )
    
    fig.update_xaxes(title_text=x_label)
    fig.update_traces(
        hovertemplate='%{fullData.name}<br>X: %{x:.3e}<br>Y: %{y:.3e}<extra></extra>'
    )

    if stage in ['og', 'ogr']:
        fig.update_yaxes(title_text='Watts (W)', row=1, col=1)
        fig.update_yaxes(title_text='Watts (W)', row=2, col=1)
    else:
        fig.update_yaxes(title_text='Voltage (V)', row=1, col=1)
        fig.update_yaxes(title_text='Voltage (V)', row=2, col=1)
    fig.update_yaxes(title_text='Wide/Narrow', row=3, col=1)

    # Add a dedicated legend annotation for ratio traces near subplot 3.
    if ratio_available:
        ratio_legend_text = (
            '<b>Ratio</b><br>'
            f'<span style="color:#1f77b4;">&#x2015;</span> CH1 W:N {wide_iris_mm:g}:{narrow_iris_mm:g} mm<br>'
            f'<span style="color:#2ca02c;">&#x2015;</span> CH3 W:N {wide_iris_mm:g}:{narrow_iris_mm:g} mm'
        )
    else:
        ratio_legend_text = (
            '<b>Ratio</b><br>'
            f'No matching pair for {wide_iris_mm:g} mm and {narrow_iris_mm:g} mm'
        )

    fig.update_xaxes(showticklabels=True)

    fig.add_annotation(
        text=ratio_legend_text,
        xref='paper', yref='paper',
        x=1.02, y=0.06,
        xanchor='left', yanchor='bottom',
        showarrow=False,
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor='#d3d3d3',
        borderwidth=1,
        font=dict(size=11),
        align='left'
    )
    
    # Create custom legend annotation for CH3 subplot
    # legend_text = '<b>CH3</b><br>'
    # for label, color in labels:
    #     legend_text += f'<span style="color:{color};">&#x2015;</span> {label}<br>'
    
    
    # fig.add_annotation(
    #     text=legend_text,
    #     xref='paper', yref='paper',
    #     x=1.02, y=0.22,
    #     xanchor='left', yanchor='top',
    #     showarrow=False,
    #     bgcolor='rgba(255,255,255,0.8)',
    #     bordercolor='#d3d3d3',
    #     borderwidth=1,
    #     font=dict(size=11),
    #     align='left'
    # )
    
    fig.update_layout(
        height=980,
        title=f'Pipeline Stage: {stage.upper()}, X-Axis: {x_axis.capitalize()}, Directory: {directory.split("/")[-2]}/{directory.split("/")[-1]}, Gain: {gain_value} V',
        hovermode='x unified',
        hoverlabel=dict(
            namelength=-1
        ),
        legend=dict(
            x=1.02,
            y=0.99,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#d3d3d3',
            borderwidth=1,
            title=dict(text='<b>Iris Position</b>', font=dict(size=12))
        )
    )
    
    # Convert to HTML
    plot_html = fig.to_html(full_html=False)
    
    return render_template(
        'index.html',
        plot_html=plot_html,
        stage=stage,
        x_axis=x_axis,
        t0=t0,
        directory=directory,
        pattern=pattern,
        narrow_iris=narrow_iris_mm,
        wide_iris=wide_iris_mm
    )

if __name__ == '__main__':
    app.run(debug=True, port=5001)