% Test T = processGaussianPeak(filename)

rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt-20251030/';
[fname, folder] = uigetfile('*.csv', 'Select MSO file', rootDir);
fpath = fullfile(rootDir, fname);

hf = figure();
T = getSignals(fpath);
h = plotSignals(T);

%%

datasets = [0:7];

fset = sprintf('RigolDS%d*.csv', datasets(8));
fnames = dir([rootDir fset]);

hf = figure;
Tmean = averageSignals(fnames);
h = plotSignals(Tmean);

%%
function Tmean = averageSignals(fnames)

    N = length(fnames);
    sum_x = 0;      % Sum of sample values
    sum_x2 = 0;     % Sum of squares of sample values
    current_std = 0; % Current standard deviation
    
    for n = 1:N
        fpath = fullfile(fnames(n).folder, fnames(n).name);
        disp(fnames(n).name)
    
        T = getSignals(fpath);
        sum_x = sum_x + T.CH1;
        sum_x2 = sum_x2 + T.CH1.^2;
        
        % Calculate the current mean
        current_mean = sum_x / n;
    
        % Calculate the current standard deviation (sample standard deviation)
        if n > 1
            % Formula: sqrt((sum_x2 - n * current_mean^2) / (n - 1))
            % Or, equivalently: sqrt((sum_x2 / (n - 1)) - (sum_x^2 / (n * (n - 1))))
            % Or, a more stable form:
            current_std = sqrt(abs(sum_x2 - (sum_x.^2)/n) / (n - 1));
            Tmean.Trigger = Tmean.Trigger + T.Trigger;
        else
            current_std = 0; % Cannot calculate std with only one data point
            Tmean.time = T.time;
            Tmean.Trigger = T.Trigger;
        end
        Tmean.CH1 = current_mean;
    
        % yyaxis left; plot(T.time, T.CH1, 'color',[255,165,0]/255, 'LineWidth', 0.5, 'LineStyle',':', 'DisplayName',fnames(i).name); hold on;
    end
    
    Tmean.CH1std = current_std;
    Tmean.Trigger = Tmean.Trigger / N;
    Tmean.Properties.UserData.filename = fnames(1).name;

end
%%
function T = getSignals(filename)
%PROCESSGAUSSIANPEAK Read file, fit Gaussian to first large negative peak, and correct CH1.
%
%   T = getSignals(FILENAME)
%     1. Reads FILENAME into a table with columns renamed: time, CH1, Trigger

%   Returns a table T with the original data.
%
%   The CSV file is assumed to have at least three numeric columns.

    % --- Step 1: Read file and rename columns ---
    T = readtable(filename, 'NumHeaderLines', 1, 'ReadVariableNames', false);
    if width(T) < 3
        error('File must contain at least three numeric columns.');
    end
    T.Properties.VariableNames(1:3) = {'time', 'CH1', 'Trigger'};
    T.Properties.UserData.filename = filename;
    fnum = split(filename, '/');
    fnum = fnum{end};
    fnum = fnum(8:end);
    T.fnum = repmat(str2double(fnum(1:end-4)), height(T), 1);
end
%%
function h = plotSignals(T)
    y = T.CH1;
    x = T.time;
    e = T.CH1std;
    dname = split(T.Properties.UserData.filename, '/');
    dname = dname{end};

    yyaxis left;

    h = plot(x, y, 'color',[255,165,0]/255, 'LineWidth', 2, 'DisplayName', dname); hold on;
    plot(x, y+e, 'color',[255,165,0]/255, 'LineWidth', 1, 'DisplayName', dname, 'LineStyle',':'); hold on;
    plot(x, y-e, 'color',[255,165,0]/255, 'LineWidth', 1, 'DisplayName', dname,'LineStyle', ':'); hold on;
    xlabel('Time');
    ylabel('Signal (V)');

    yyaxis right;
    h = plot(x, T.Trigger, 'm', 'DisplayName', 'CH3 Trigger');
    ylabel('Trigger (V)')

    legend('location', 'SouthEast');
    title(T.Properties.UserData.filename);
    grid;
end