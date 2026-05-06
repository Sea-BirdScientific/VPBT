% Test_readACSfile

% rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt-20251029/';
% rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt-20251030/';
% rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt-20260120/spectral_acs_20260123/';
% rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt 20260213/';
rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/355_532 VPBT/';

fileList = dir([rootDir '*050126.dat']);

T = [];

N = length(fileList);
% N = 1;
for i = 1:N
    fname = fileList(i).name;
    fullpath = fullfile(fileList(i).folder, fname );
    fprintf(1, '%s\n', fullpath)
    [T0, ~, ~, ~, ~] = readACSfile(fullpath);
    T = [T; T0];
end

Tzero = T.epoch(1);
T.epoch = T.epoch-Tzero;

% Interpolate to 532 nm
T.C532 = interpX(T.C530_4, T.C534_2, 530.4, 534.2, 532.0);
T.A532 = interpX(T.A528_7, T.A532_5, 528.7, 532.5, 532.0);
T.C401 = T.C401_4;
T.A401 = T.A400_9;


%% Filter
filter_width = 401;
kernel = ones(1,filter_width)/filter_width;

T.C532f = conv(medfilt1(T.C532, filter_width), kernel, 'same');
T.A532f = conv(medfilt1(T.A532, filter_width), kernel, 'same');

T.C401f = conv(medfilt1(T.C401, filter_width), kernel, 'same');
T.A401f = conv(medfilt1(T.A401, filter_width), kernel, 'same');

% T.C532f = smooth(T.C532, filter_width, 'rloess');
% T.A532f = smooth(T.A532, filter_width, 'rloess');

% xnum = seconds(T.DateTime - T.DateTime(1));
% T.C532f = spaps(xnum, T.C532, 0.005);
% T.A532f = spaps(xnum, T.A532, 0.005);

%%
hf = figure(1);clf;

h(1) = plot(T.DateTime, T.C532, 'b', 'LineStyle', 'none', 'Marker','.', 'MarkerSize',1 );
hold on;grid;
h(3) = plot(T.DateTime, T.C532f, 'k', 'LineWidth',1);
h(2) = plot(T.DateTime, T.A532, 'g.');
h(4) = plot(T.DateTime, T.A532f, 'k', 'LineWidth',1);

title(fname);
axis tight
ylim([0 1.5])
ylabel('Attenuation / Absorption  (m^{-1})')


% hx = xline([datetime('2026-02-13 18:40', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 18:57', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 18:34', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 19:30', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 20:09', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 20:50', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 21:30', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 22:06', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 22:51', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-13 23:32', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
% % hx = xline([datetime('2026-02-14 00:10', 'TimeZone', 'UTC')], linestyle=':', color=[.7 0 .7], linewidth=1)
legend(h,'c532','a532', 'location', 'NorthWest')
changeFontSize(12)
set(gca,'XGrid','off','YGrid','on')
xtickformat('HH:mm');
hold on;
%%

[a,c] = evalacs(T, '2026-05-01 15:44');
disp([a,c])


%%
hf = figure(2);clf;

h(1) = plot(T.DateTime, T.C401, 'b', 'LineStyle', 'none', 'Marker','.', 'MarkerSize',1 );
hold on;grid;
h(3) = plot(T.DateTime, T.C401f, 'k', 'LineWidth',1);
h(2) = plot(T.DateTime, T.A401, 'g.');
h(4) = plot(T.DateTime, T.A401f, 'k', 'LineWidth',1);

title(fname);
axis tight
ylim([0 1.5])
ylabel('Attenuation / Absorption  (m^{-1})')
legend(h,'c401','a401', 'location', 'NorthWest')
changeFontSize(12)
set(gca,'XGrid','off','YGrid','on')
xtickformat('HH:mm');

%%

% Fitting region is 10
% gt = find((T.DateTime >= datetime('30-Oct-2025 12:02:13', 'timezone', 'UTC')) & (T.DateTime <= datetime('30-Oct-2025 12:54:26', 'timezone', 'UTC')));
% [pc,s] = polyfit(T.ms(gt), T.C532(gt), 1);

% gt = find((T.DateTime >= datetime('27-Oct-2025 00:00:00', 'timezone', 'UTC')) & (T.DateTime <= datetime('30-Oct-2025 00:00:00', 'timezone', 'UTC')));
% gt = find((T.DateTime >= datetime('27-Oct-2025 00:00:00', 'timezone', 'UTC')) & (T.DateTime <= datetime('30-Oct-2025 12:54:26', 'timezone', 'UTC')));



% 1/20: 15:45 - 16:32  (slope close to 1/21)
% gt = find((T.DateTime >= datetime('20-Jan-2026 15:45:00', 'timezone', 'UTC')) & (T.DateTime <= datetime('20-Jan-2026 16:32:00', 'timezone', 'UTC')));
% pc = [ 1.1869e-08   1.0501e-01+0.009];

% 1/20: 16:32 - 16:45
% gt = find((T.DateTime >= datetime('20-Jan-2026 16:32:00', 'timezone', 'UTC')) & (T.DateTime <= datetime('20-Jan-2026 16:45:00', 'timezone', 'UTC')));
% [pc,s] = polyfit(T.epoch(gt), medfilt1(T.C532(gt),50), 1);
% pc = [ 2.4561e-08   1.1139e-01];

% 1/21: 
% gt = find((T.DateTime >= datetime('21-Jan-2026 15:00:00', 'timezone', 'UTC')) & (T.DateTime <= datetime('21-Jan-2026 16:00:00', 'timezone', 'UTC')));
% [pc,s] = polyfit(T.epoch(gt), medfilt1(T.C532(gt),5), 1);
% % pc = [8.7828e-09   6.5786e-02];

% 1/22: 13:30 -  
% gt = find((T.DateTime >= datetime('21-Jan-2026 15:00:00', 'timezone', 'UTC')) & (T.DateTime <= datetime('21-Jan-2026 16:00:00', 'timezone', 'UTC')));
% pc = [8.7828e-09   6.5786e-02];


% hold on;
% Ci = polyval(pc, T.epoch);
% plot(T.DateTime, Ci, 'c.')
%%

% Call fminsearch
% The anonymous function handles passing x and y to the objective function
% x = T.epoch(gt);
% xval = linspace(T.epoch(1), T.epoch(end), 200);
% xvalDT = datetime(xval+Tzero, 'ConvertFrom', 'epochtime', 'epoch', datetime(1970, 1, 1), 'TicksPerSecond', 100,'timezone', 'UTC');
% 
% % y = medfilt1(T.C532(gt), 2001);
% y = medfilt1(T.C532(gt), 5);
% skip = 1;
% x = x(1:skip:end);
% y = y(1:skip:end);



%%
% Initial guesses for [a, b, c]

% Cguess = min(y) - (max(y)-min(y)) / 2;
% guess = [ones(size(x)), -x] \ log(y - Cguess);
% Aguess = exp(guess(1));
% Bguess = guess(2);
% initial_guess = [Aguess, Bguess, Cguess]; %
% %  Adjust these based on your data's behavior
% 
% options = optimset('MaxFunEvals',4e8, 'MaxIter', 1e8);
% [params, min_sse] = fminsearch(@(p) exponential_model_sse(p, x, y), initial_guess, options);
% 
% % Extract fitted parameters
% a_fit = real(params(1));
% b_fit = real(params(2));
% c_fit = real(params(3));
% 
% fprintf('Fitted parameters:\n');
% fprintf('a = %.4e\n', a_fit);
% fprintf('b = %.4e\n', b_fit);
% fprintf('c = %.4e\n', c_fit);
% fprintf('Minimum SSE: %.4f\n', min_sse);
% 
% yval = expval(params, xval);
% xvalDT = datetime(xval+Tzero, 'ConvertFrom', 'epochtime', 'epoch', datetime(1970, 1, 1), 'TicksPerSecond', 100,'timezone', 'UTC');

% yval = polyval(pc,xval);


%%
% 
% T.C532_corr = T.C532 - polyval(pc, T.epoch) + 0.059;   % 0.2
% % Hack to correct a (use c regression because for som[e reason, a was decreasing)
% T.A532_corr = T.A532 - polyval(pc, T.epoch) + 0.115;    % 0.08 - manual offset to result in a=c=0.02 with no scatterers
% 
% % T.C532_corr = T.C532 - expval(params, T.epoch) + 0.062;
% % % Hack to correct a (use c regression because for some reason, a was decreasing)
% % T.A532_corr = T.A532 - expval(params, T.epoch) + 0.119;    % 0.08 - manual offset to result in a=c=0.02 with no scatterers
% 
% figure(3); clf;
% % plot(T.epoch, T.C532, 'b.');
% plot(T.DateTime, T.C532, 'b.');
% % hold on; plot(xval, yval, 'ro')
% ylim([0,1])

% hold on;
% h(2) = plot(T.DateTime(gt), T.C532(gt), 'r', 'LineStyle', 'none', 'Marker','.', 'MarkerSize',2);
% h(3) = plot(T.DateTime, T.C532_corr, 'm.');
% yline(0.046)
% % [pa,s] = polyfit(T.ms(gt), T.A532_5(gt), 1);
% h(4) = plot(T.DateTime, T.A532, 'g.');
% h(5) = plot(T.DateTime, T.A532_corr, 'k.');
% plot(xvalDT, yval, 'm:')
% 
% legend('C532','Correction fit region','C532\_corrected', 'c = 0.046 m^{-1}', 'A532', 'A532\_correctected', 'location', 'SouthEast')

%%
function Xi = interpX(X1, X2, w1, w2, wi)
    
Xi = ((wi-w1)/(w2-w1))*(X2-X1) + X1 ;

end
%%
function sse = exponential_model_sse(params, x, y)
    % Fit y = a * exp(b*x) + c

    % params(1) = a, params(2) = b, params(3) = c
    a = params(1);
    b = params(2);
    c = params(3);
    
    % Your model: a*exp(b*x) + c
    fitted_y = a * exp(b * x) + c;
    
    % Calculate Sum of Squared Errors (SSE)
    sse = sum((fitted_y - y).^2); 
end
%%
function yi = expval(params, xi)
    a = params(1);
    b = params(2);
    c = params(3);
    
    yi = a * exp(b * xi) + c;
end

%%
function [a,c] = evalacs(T, dtqueryStr)

    dt = datetime(dtqueryStr, 'TimeZone','UTC');
    a = interp1(T.DateTime, T.A532f, dt);
    c = interp1(T.DateTime, T.C532f, dt);

end
