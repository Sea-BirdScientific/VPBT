function T = processGaussianPeak(filename)
%PROCESSGAUSSIANPEAK Read file, fit Gaussian to first large negative peak, and correct CH1.
%
%   T = processGaussianPeak(FILENAME)
%     1. Reads FILENAME into a table with columns renamed: time, CH1, CH3
%     2. Fits a Gaussian to the first large *negative* peak in CH1
%        (even if clipped, ignoring the clipped region)
%     3. Subtracts the fitted Gaussian from CH1 to produce CH1corr
%
%   Returns a table T with the original and corrected data.
%
%   The CSV file is assumed to have at least three numeric columns.

    % --- Step 1: Read file and rename columns ---
    T = readtable(filename, 'NumHeaderLines', 1, 'ReadVariableNames', false);
    if width(T) < 3
        error('File must contain at least three numeric columns.');
    end
    T.Properties.VariableNames(1:3) = {'time', 'CH1', 'CH3'};

    % --- Step 2: Identify first large negative peak in CH1 ---
    y = T.CH1;
    x = T.time;


    % Find peaks on inverted signal to locate negative peaks
    [pks, locs] = findpeaks(-y, x, 'MinPeakProminence', std(y)*2);
    if isempty(pks)
        error('No significant negative peaks found in CH1.');
    end
    peakLoc = locs(1);   % take first large negative peak

    % Estimate peak width (using half-height region)
    [~, idx] = min(abs(x - peakLoc));
    ypeak = y(idx);
    halfmax = ypeak / 2.605;  % Fudge factor since we don't know peak height
    leftIdx = find(y > halfmax & x < peakLoc, 1, 'last');
    rightIdx = find(y > halfmax & x > peakLoc, 1, 'first');
    if isempty(leftIdx), leftIdx = max(1, idx - 20); end
    if isempty(rightIdx), rightIdx = min(length(x), idx + 20); end
    fitRegion = leftIdx:rightIdx;

    % --- Step 3: Fit Gaussian to selected region ---
    xfit = x(fitRegion);
    yfit = y(fitRegion);

    % Use fit() with a single-term Gaussian
    % gfit = fit(xfit, yfit, 'gauss1');  % Curve fit toolbox only

    gaussian_func = @(params, x) params(1) * exp(-((x - params(2))./params(3)).^2);
    gfit = @(params) sum((gaussian_func(params, xfit) - yfit).^2);
    initial_guesses = [max(yfit), mean(xfit), std(xfit)]; 
    best_params = fminsearch(gfit, initial_guesses);
    yGauss = gaussian_func(best_params, x);

    % --- Step 4: Subtract fitted Gaussian from CH1 ---
    T.CH1corr = T.CH1 - yGauss;

    % --- Optional: store fit info and plot ---
    T.Properties.UserData.GaussianFit = best_params;

    figure;
    plot(x, y, 'color',[255,165,0]/255, 'DisplayName', 'CH1', 'LineWidth', 2); hold on;
    plot(xfit, yfit, 'r.', 'DisplayName', 'CH1 peak')
    plot(x, yGauss, 'r--', 'LineWidth', 1.5, 'DisplayName', 'Gaussian fit');
    plot(x, T.CH1corr, 'k', 'DisplayName', 'CH1 corrected', 'LineWidth', 2);
    xlabel('Time');
    ylabel('Signal (V)');

    yyaxis right;
    plot(x, T.CH3, 'm', 'DisplayName', 'CH3 Trigger')
    ylabel('Trigger (V)')

    legend('location', 'SouthEast');
    title(sprintf('Gaussian fit to first negative peak at %.3f', peakLoc));
    grid;
end


