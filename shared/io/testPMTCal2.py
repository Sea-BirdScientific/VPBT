import json, pandas as pd
# from shared.io.expgrid_parser import parse_expgrid
# from shared.io.pmt import PMTCal
from expgrid_parser import parse_expgrid
from pmt import PMTCal

meta = json.load(open('../data/355_532 VPBT/ExpGrid-20260428.json','r'))
rows = [r.to_dict() for r in parse_expgrid(meta)]
row0 = rows[0]

# pmt_cal = PMTCal.from_manifest_row(row0)  # uses rootDir / pmts.relative_path_to_PMT_files
PMT = 'R9880U210'
pmt_cal = PMTCal.from_expgrid(meta, PMT)  # uses rootDir / pmts.relative_path_to_PMT_files

# Test PMTcal
print(f"PMTCal parameters using {PMT}:")
control_voltage_V = 3.0 #row0['pmt_control_V']
supply_multiplier = row0['pmt_supply_voltage_multiplier']
wavelength = row0['laser_wavelength_nm']
print(control_voltage_V, supply_multiplier, wavelength)

print(pmt_cal.resp_model(wavelength))
print(pmt_cal.gain_model(control_voltage_V * supply_multiplier))

ch532_V = -1
watts = pmt_cal.volts_to_watts(
    volts=ch532_V,            # numpy vector from Rigol CSV
    wavelength_nm=row0['laser_wavelength_nm'],      # for now (we’ll add 355 nm later)
    control_voltage_V=row0['pmt_control_V'],
    supply_multiplier=row0['pmt_supply_voltage_multiplier']
)
print(watts)
