    function [T, wa, wc, a c] = readACSfile(acsname)
%READACSFILE Read an ACS data file (version 3 format) into a MATLAB table
%
%   T = READACSFILE(ACSNAME) reads the file named ACSNAME and returns
%   a table T containing all data columns, with headers assigned based on
%   line (N + 14) of the file.
%
%   Adds a new datetime column "DateTime" = StartDateTime + milliseconds.
%
%   Data columns (as per ACS format v3):
%     [time_offset_ms, N attenuations, N absorptions,
%      instrument_temp_C, wheel_speed, pressure, ext_temp,
%      4 dark values]

    % Read all lines once
    fid = fopen(acsname, 'r');
    if fid < 0
        error('Cannot open file: %s', acsname);
    end
    C = textscan(fid, '%s', 'Delimiter', '\n', 'Whitespace', '');
    fclose(fid);
    lines = C{1};

    % --- Extract metadata ---
    versionLine = strtrim(lines{4});
    version = str2double(regexp(versionLine, '\d+', 'match', 'once'));
    if version ~= 3
        error('Unsupported ACS structure version (%s). Expected version 3.', versionLine);
    end

    N = str2double(regexp(lines{9}, '\d+', 'match', 'once'));
    if isnan(N)
        error('Failed to read N (number of wavelengths) from line 9.');
    end

    % --- Identify header and data start line ---
    headerLineNum = N + 14;
    headerLine = lines{headerLineNum};
    headerLine = ['ms ', headerLine];   % ensure first col name is 'ms'

    % Determine data start line (one after header)
    dataStart = headerLineNum + 1;

    % --- Parse header names ---
    headerNames = strsplit(strtrim(headerLine), {' ', '\t', ','});
    headerNames = headerNames(~cellfun(@isempty, headerNames)); % remove empties

    % --- Read data block ---
    dataLines = lines(dataStart:end);
    tmpFile = [tempname '.txt'];
    fid = fopen(tmpFile, 'w');
    fprintf(fid, '%s\n', dataLines{:});
    fclose(fid);

    % Read numeric data as table
    opts = detectImportOptions(tmpFile, 'NumHeaderLines', 0);
    opts.VariableNames = matlab.lang.makeValidName(headerNames);
    T = readtable(tmpFile, opts);
    delete(tmpFile);

    % --- Store metadata ---
    endStr = strsplit(lines{1}, '\t');
    endStr = [endStr{2} ' ' endStr{3}];
    T.Properties.Description = sprintf('ACS v3 data file: %s', acsname);
    T.Properties.UserData.EndDateTime = endStr;
    T.Properties.UserData.N_Wavelengths = N;

    % --- Add DateTime column ---
    try
        % Try parsing various common ACS date formats
        startDT = datetime(endStr, 'InputFormat', 'MM-dd-yyyy HH:mm:ss', 'TimeZone', 'UTC');
    catch
        try
            startDT = datetime(endStr, 'InputFormat', 'yyyy-MM-dd HH:mm:ss', 'TimeZone', 'UTC');
        catch
            startDT = datetime(endStr); % fallback
        end
    end

    % Add ms offset (convert milliseconds to seconds)
    if any(strcmp('ms', T.Properties.VariableNames))
        % startSec = seconds(T.ms(1)   / 1000);
        % endSec   = seconds(T.ms(end) / 1000);
        % T.DateTime = startDT - (endSec-startSec) + seconds(T.ms / 1000);
        T.DateTime = startDT + seconds(T.ms / 1000);
    else
        warning('No ''ms'' column found—DateTime not added.');
    end
    fprintf(1, "Start-End: %s-$s\n", T.DateTime(1), T.DateTime(end))

    T.epoch = double(convertTo(T.DateTime,'epochtime','Epoch','1970-1-1', 'TicksPerSecond',100));

    % Move DateTime to first column
    T = movevars(T, 'DateTime', 'Before', 1);
    T = renamevars(T, {'ExtraVar1', 'ExtraVar3','ExtraVar4'}, {'Tint', 'P', 'Text'});

    % Extract wavelengths, a, and c
    hd = T.Properties.VariableNames;
    for i = 3:((2*N)+2)
        ww = hd{i};
        w(i-2) = str2double(ww(2:end-2)+"."+ww(end));
    end

    % Extract wavelengths and data into arrays for convenience.
    wc = w(1:N);
    wa = w((N+1):(2*N));
    c = T{:,3:(N+2)};
    a = T{:,(N+3):(2*N+2)};