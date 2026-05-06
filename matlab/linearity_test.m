% --- 1. Data Input ---
% Assume we have data structured where:
% - refValues is a vector of unique reference values used.
% - measuredData is a matrix where each column corresponds to one reference value 
%   and rows are the multiple measurements taken for that value.

% Example Data (5 samples measured 10 times each):
T = [0.0	-0.481	-0.481;
0.0	-0.460	-0.460;
1.0	1.400	0.400;
2.0	2.500	0.500;
4.0	3.900	-0.100;
8.0	9.000	1.000;
16.0	17.000	1.000;
20.0	19.300	-0.700;
40.0	39.050	-0.950]

% --- 2. Data Processing: Calculate Average Bias ---
%%
avgMeasured = T(:, 2);
refValues = T(:,1);

%%

% Calculate the average bias for each reference value
avgBias = avgMeasured - refValues;

% Prepare data for regression (x = Reference, y = Avg Bias)
x_ref = refValues';
y_bias = avgBias';

% --- 3. Quantitative Analysis: Linear Regression of Bias vs Reference ---

% Fit a linear model: Bias = Intercept + (Slope * Reference Value)
mdl = fitlm(x_ref, y_bias, 'linear');

% Display the model summary
disp('--- Regression Model Summary (Bias vs. Reference Value) ---');
disp(mdl);

% Extract key metrics for the slope (index 2 in the coefficients table)

slope_pValue = mdl.Coefficients.pValue(2);
slope_estimate = mdl.Coefficients.Estimate(2);
intercept_estimate = mdl.Coefficients.Estimate(1);

fprintf('\nRegression Equation: Bias = %.4f + (%.4f * Reference Value)\n', intercept_estimate, slope_estimate);
fprintf('P-value for the slope: %.4f\n', slope_pValue);

% --- 4. Acceptance Criteria Check ---

alpha = 0.05; % Significance level

disp('--- Linearity Assessment ---');
if slope_pValue > alpha
    fprintf('Result: P-value (%.4f) > alpha (%.2f).\n', slope_pValue, alpha);
    disp('Conclusion: The slope is NOT statistically different from zero. The measurement system IS linear.');
else
    fprintf('Result: P-value (%.4f) <= alpha (%.2f).\n', slope_pValue, alpha);
    disp('Conclusion: The slope IS statistically different from zero. The measurement system HAS a linearity problem.');
end

% x = vals2(:,1);
% y = vals2(:,2);

%%

% --- 5. Optional: Plot the results ---

figure;
scatter(x_ref, y_bias, 'filled');

hold on;

% Plot the regression line
plot(x_ref, mdl.Coefficients.Estimate(1) + mdl.Coefficients.Estimate(2)*x_ref,  'r:', 'LineWidth', 2);

% Plot the ideal zero-bias line
yline(0, '--k', 'LineWidth', 1.5);
ylim([-4, 4])
xlabel('Reference Value');
ylabel('Average Bias (Measured Avg - Reference)');
title('Gauge Linearity Analysis: Bias vs. Reference Value');
legend('Average Bias Data Points', 'Regression Line', 'Zero Bias Line', 'Location', 'best');
grid on;
hold off;

text(5, 3, sprintf('Y = %.4f + %.4f*X, R^2 = %4.3f', intercept_estimate, slope_estimate, mdl.Rsquared.Ordinary));

%%

% --- 5. Optional: Plot the results ---

y = avgMeasured;
mdl2 = fitlm(x_ref, y, 'linear');


figure;
scatter(x_ref, y, 'filled');

hold on;

% Plot the regression line
plot(x_ref, mdl2.Coefficients.Estimate(1) + mdl2.Coefficients.Estimate(2)*x_ref,  'r:', 'LineWidth', 2);

% Plot the ideal zero-bias line
plot([-5, 40], [-5, 40], 'k--')

xlim([-4,40])
ylim([-4,40])
axis square
xlabel('Reference Value');
ylabel('Measured Av');
title('Gauge Linearity Analysis: Measured vs. Reference Value');
legend('Average Bias Data Points', 'Regression Line', '1:1', 'Location', 'SouthEast');
grid on;
hold off;

text(5, 30, sprintf('Y = %.4f + %.4f*X, R^2 = %4.3f', mdl2.Coefficients.Estimate(1), mdl2.Coefficients.Estimate(2) , mdl2.Rsquared.Ordinary));

