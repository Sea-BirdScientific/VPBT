R_full = 1.5;
C0 = 299792458.0;  % speed of light in vacuum [m/s]
n_group = 1.33;
t0 = 5e-9;
t = T.time;

softness_frac = 0.05;

R = (C0 / (2.0 * n_group)) * (t - t0);

if R_full <= 0
    overlap = ones(length(R),1);
else
    width = max(1e-6, softness_frac * max(R_full, 1e-6));
    x = (R - R_full) / width;
    overlap =  1.0 ./ (1.0 + exp(-x));  % ~0 for R<<R_full; ~1 for R>>R_full
end

figure(10)
plot(R, overlap, 'r.')
xline(R_full, ':')
ylim([-2, 2])