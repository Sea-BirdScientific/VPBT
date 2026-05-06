function a_corr_final = acs_scattering_correction_robust(wa, a, wc, c, lambda_range_nm)
% ACS_SCATTERING_CORRECTION_ROBUST Applies robust proportional correction and zeroing.
%
% Inputs:
%   wa, wc : Wavelength arrays (1 x M)
%   a, c   : Measured absorption and attenuation spectra (N x M)
%   lambda_range_nm : [min_wavelength, max_wavelength] for correction baseline

    % 1. Interpolate c to match absorption wavelengths (wa)
    if ~isequal(wa, wc)
        c_interp = interp1(wc, c', wa, 'linear', 'extrap')';
    else
        c_interp = c;
    end
    
    b_m = c_interp - a;

    % Define indices for the reference range
    min_idx = find(wa >= lambda_range_nm(1), 1, 'first');
    max_idx = find(wa <= lambda_range_nm(2), 1, 'last');
    
    % 2. Robust Proportional Method using a range median
    % Calculate the median 'a' and 'b_m' across the NIR range for each row
    a_ref_median = median(a(:, min_idx:max_idx), 2); % N x 1
    b_m_ref_median = median(b_m(:, min_idx:max_idx), 2); % N x 1
            
    % Compute row-wise correction factors (epsilon: N x 1)
    epsilon = a_ref_median ./ b_m_ref_median;
    
    % Apply proportional correction
    a_corr_prop = a - (epsilon .* b_m);

    % 3. Final Baseline Zeroing Step (corrects for tiny final offsets)
    % Calculate the median offset of the *corrected* data in the NIR range
    nir_baseline_offset = median(a_corr_prop(:, min_idx:max_idx), 2); 
    
    % Subtract the baseline offset from the entire spectrum
    a_corr_final = a_corr_prop - nir_baseline_offset;

end
