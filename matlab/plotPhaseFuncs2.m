% Plot 0.1 and 2.0 um phase functions

dataDir = '../../theory';

w = [355, 532];
color = [0.7*[ 0 1 0];0.7*[1 0 1]];


hf = figure(10); clf;
hold on;

for i = 2:-1:1
    T01 = readtable(fullfile(dataDir, "phase_beads_"+w(i)+"_0.1_0.003.csv"));
    T01.Properties.VariableNames = {'theta', 'P'};
    
    T20 = readtable(fullfile(dataDir, "phase_beads_"+w(i)+"_2.0_0.022.csv"));
    T20.Properties.VariableNames = {'theta', 'P'};

    if i == 1
        h = plot(T20.theta, (0.0302/0.0422)*T20.P, '-', 'Color', color(i,:), 'LineWidth',2);
    else
        h = plot(T01.theta, T01.P, '-', 'Color', color(i,:), 'LineWidth',2);
    end

end

set(gca, 'yscale', 'log')
ylim([1e-3,30])

legend("532: 0.1 μm  (ThermoFisher 3100A)", "532: 2.0 μm  (ThermoFisher 4202A" )
title('Polystyrene Beads Phase Functions (bhmie)')
ylabel('Phase function (sr^{-1})');
xlabel('\theta')
grid
changeFontSize(12)