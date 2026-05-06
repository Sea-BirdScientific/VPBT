% Plot 0.1 and 2.0 um phase functions

dataDir = '../../theory';

w = [355, 532];
color = [0.7*[1 0 1];0.7*[0 1 0]];


hf = figure(1);clf;
hold on;

for i = 1:2

    T01 = readtable(fullfile(dataDir, "phase_beads_"+w(i)+"_0.1_0.003.csv"));
    T01.Properties.VariableNames = {'theta', 'P'};
    
    T20 = readtable(fullfile(dataDir, "phase_beads_"+w(i)+"_2.0_0.022.csv"));
    T20.Properties.VariableNames = {'theta', 'P'};

    h = plot(T01.theta, T01.P, '-', 'Color', color(i,:), 'LineWidth',2)
    h = plot(T20.theta, T20.P, ':', 'Color', color(i,:), 'LineWidth',2);
end

set(gca, 'yscale', 'log')
legend("355: 0.1 μm  (ThermoFisher 3100A)", "355: 2.0 μm  (ThermoFisher 4202A", ...
    "532: 0.1 μm  (ThermoFisher 3100A)", "532: 2.0 μm  (ThermoFisher 4202A")
title('Polystyrene Beads Phase Functions (bhmie)')
ylabel('Phase function (sr^{-1})');
xlabel('\theta')
ylim([1e-3, 1e2])
grid