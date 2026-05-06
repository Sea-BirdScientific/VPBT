% Test T = processGaussianPeak(filename)

rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt-20251029/';

fname = 'RigolDS30.csv';

fpath = fullfile(rootDir, fname);

T = processGaussianPeak(fpath);



