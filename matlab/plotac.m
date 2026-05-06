rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/vpbt-20260120/spectral_acs_20260127/';
% fname = 'spectral_acs_in_bucket.dat';
fname = 'spectral_acs_in_ROWater.dat';

rootDir = '/Users/erehm/Library/CloudStorage/Box-Box/BeamSeaBird/data/acs/DIW run (non-ELGA)/';
fname   = 'SBS_DIW1-outside bath.dat';

ff = fullfile(rootDir,fname);
[T, wa, wc, a, c] = readACSfile(ff);

a_corr = acs_scattering_correction(wa, a, wc, c, 'none', [700,730]);
% a_corr = acs_scattering_correction_robust(wa, a, wc, c, [700,730]);

[aw, ~] = PureWater(wa);
[xx, cw] = PureWater(wc);
at = mean(a_corr,1) + aw;
ct = mean(c,1) + cw;


plotAll = false;

figure;
ha = plot(wa, a_corr, 'r');
hold on;
hc = plot(wc, c, 'b');
legend([ha(1); hc(1)], 'ap', 'cp');

if plotAll
    hw = plot(wa, aw, 'm', wc, cw, 'c');
    set(hw, 'LineWidth', 2)
    ylim([0,.5])
    
    ht = plot(wa, at, 'r:', wc, ct, 'b:');
    set(ht, 'LineWidth', 2)
    legend([ha(1); hc(1); hw(:); ht(:)], 'ap', 'cp', 'aw', 'cw', 'at', 'ct');
end
title(regexprep(fname, '_', '\\_'));
ylabel('absorption / attenuation (m^{-1})');
xlabel('Wavelength (nm)');
ylim([0, 0.5]);



% Your ap and cp values are typical for Type III water: Standard RO water
% is less pure than the Type I water used for the ideal Pope & Fry
% standard. Your positive "additional" values confirm the presence of trace
% contaminants (particulates, bacteria, dissolved organic matter).The extra
% attenuation (\(c_{p+g}\)) is significant: An additional \(0.06\
% \text{m}^{-1}\) is a measurable, reasonable baseline for general-grade
% DI/RO water that has not undergone final polishing with a mixed-bed
% deionizer or rigorous degassing to remove microbubbles.Values are
% consistent with field observations: Oceanographic literature often
% references these varying baseline measurements depending on lab water
% quality, and your numbers fall into an expected range of variability.



% At 532 nm (green laser light), reverse osmosis (RO) water has extremely
% low optical absorption, behaving very similarly to pure water. The
% optical properties are dominated by low absorption, with attenuation
% caused primarily by scattering rather than absorption. [1, 2] Typical
% values for RO water at 532 nm are:
% 
% • Absorption Coefficient (): Approximately 0.04 to 0.05 m⁻¹ (or
% $\sim$0.0004–0.0005 cm⁻¹). • Attenuation Coefficient (): Generally ranges
% from 0.13 to 0.14 m⁻¹ in
% high-quality freshwater, with scattering accounting for the majority of
% the attenuation. [3, 4, 5]
% 
% Key Details: 
% 
% • Absorption Behavior: The absorption of pure water is very low in the
% visible spectrum, with a minimum around 420 nm, and slightly higher, yet
% still minimal, in the green region (532 nm). 
% 
% • RO Water Quality: Typical RO water has a conductivity of 5–50 µS/cm.
% While not as pure as deionized (DI) water (0.055 µS/cm), the remaining
% impurities have a negligible effect on the absorption coefficient at 532
% nm compared to the water molecules themselves.
% 
% • Scattering vs. Absorption: At 532 nm, scattering is a significant
% contributor to the total attenuation coefficient, which is why the
% attenuation ($c$) is higher than the absorption ($a$). [6, 7, 8, 9, 10]
% 
% Note: These values are for pure/purified water. If the RO water is
% contaminated with organic matter, the absorption values could increase.
% [11]
% 
% AI responses may include mistakes.
% 
% [1] https://www.sciencedirect.com/science/article/pii/S2213597920300392
% [2] https://pmc.ncbi.nlm.nih.gov/articles/PMC4435242/
% [3] https://opg.optica.org/ao/abstract.cfm?uri=ao-55-25-7163
% [4] https://opg.optica.org/viewmedia.cfm?r=1&rwjcode=josa&uri=josa-67-5-622&html=true
% [5] https://www.researchgate.net/publication/364299822_Measurement_of_the_Attenuation_Coefficient_in_Fresh_Water_Using_the_Adjacent_Frame_Difference_Method
% [6] https://www.ampac1.com/blog/conductivity-of-ro-water/
% [7] https://opg.optica.org/abstract.cfm?uri=ao-36-24-6035
% [8] https://core.ac.uk/download/pdf/593762318.pdf
% [9] https://www.researchgate.net/figure/Absorption-spectrum-of-pure-distilled-water-6_fig1_49279750
% [10] https://omlc.org/spectra/water/abs/index.html
% [11] https://pmc.ncbi.nlm.nih.gov/articles/PMC5233748/
% 
