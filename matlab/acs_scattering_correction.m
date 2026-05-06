function a_corr = acs_scattering_correction(wa, a, wc, c, method, varargin)
% ACS_SCATTERING_CORRECTION Corrects NxM ac-s spectra for scattering.
%
% Inputs:
%   wa, wc : Wavelength arrays (1 x M)
%   a, c   : Measured absorption and attenuation spectra (N x M)
%   method : 'flat', 'proportional', or 'kirk'
%   varargin: Reference wavelength (lambda_ref) for flat/proportional 
%             OR fractional value (w) for Kirk.

    % 1. Interpolate c to match absorption wavelengths (wa) if necessary
    if ~isequal(wa, wc)
        % Interpolate row-wise (dimension 2)
        c_interp = interp1(wc, c', wa, 'linear', 'extrap')';
    else
        c_interp = c;
    end
    
    % Calculate measured scattering coefficient (N x M)
    b_m = c_interp - a;

    switch lower(method)
        case 'flat'
            % Find reference index and subtract reference value for each realization
            lambda_ref = varargin{1};
            [~, idx] = min(abs(wa - lambda_ref));
            a_corr = a - a(:, idx); % Implicit expansion: N x M minus N x 1

        case 'proportional'
            % Variable scattering error (Zaneveld et al., 1994)
            lambda_ref = varargin{1};
            [~, idx] = min(abs(wa - lambda_ref));
            
            % Compute row-wise correction factors (N x 1)
            epsilon = a(:, idx) ./ b_m(:, idx);
            
            % Subtract proportional scattering (N x 1 .* N x M)
            a_corr = a - (epsilon .* b_m);

        case 'kirk'
            % Constant fraction of scattering (Kirk, 1992)
            w = varargin{1}; 
            a_corr = a - (w .* b_m);

        case 'none'
            a_corr = a;

        otherwise
            error('Unknown method. Choose ''flat'', ''proportional'', or ''kirk''.');
    end
end
