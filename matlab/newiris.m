%
% newiris.m
%

dataDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/355_532 VPBT';

% trialDir = ''; ipart = 2;
`trialDir = 'iris_test_1mm'; ipart = 3;

fullDir = fullfile(dataDir, trialDir, '*.csv');

files = dir(fullDir);
Nfiles = length(files);
cmap = lines(Nfiles);

csw = 2.25e8;
t0 = 1.305e-8;
xmark = 1.3; % m
filter_width = 11;

figure(1+ipart*10); clf;

legstr = [];

for i = 1:Nfiles
    trial = files(i).name;
    fnparts = split(trial, '_');
    iris_mm = fnparts{ipart};
    legstr = [legstr; iris_mm];

    fn = fullfile(dataDir, trialDir, trial);
    tt = readtable(fn);

    r = (tt.time_s - t0) * csw / 2;

    col = cmap(i,:);
    subplot(2,1,1)
    hold on;
    h = plot(r, tt.ch1Voltage_v, 'Color', col);
    subplot(2,1,2)
    hold on;
    h = plot(r, tt.ch3Voltage_v, 'Color', col);

    % fprintf(trial)
    % pause;


    
end


subplot(2,1,1)
xline(xmark, ':')
xlim([0,4])
legend(legstr, 'Location','southeast')
subplot(2,1,2)
xline(xmark, ':')
xlim([0,4])


figure(2+ipart*10);clf;

legstr = [];
mave = ones(1,filter_width);

for i = 2:Nfiles
    trial = files(i).name;
    fnparts = split(trial, '_');
    iris_mm = fnparts{ipart};
    legstr = [legstr; iris_mm];

    fn = fullfile(dataDir, trialDir, trial);
    tt = readtable(fn);

    ch1 = conv(tt.ch1Voltage_v, mave, 'same');
    ch3 = conv(tt.ch3Voltage_v, mave, 'same');
    r = (tt.time_s-t0) * csw / 2;

    if (i == 2)
        norm532 = ch1;
        norm355 = ch3;
    end

    col = cmap(i,:);
    subplot(2,1,1)
    hold on;
    h = plot(r, ch1./norm532, 'Color', col);
    subplot(2,1,2)
    hold on;
    h = plot(r, ch3./norm355, 'Color', col);

end



figure(2+ipart*10);
subplot(2,1,1)
xline(xmark, ':')
xlim([0,4])
legend(legstr, 'Location','southeast')
subplot(2,1,2)
xline(xmark, ':')
xlim([0,4])

figure(1+ipart*10)


