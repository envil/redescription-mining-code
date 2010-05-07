function display_map(coordinates_file, supp_file, figures_patt, format)
    coordinates = load(coordinates_file);
    mask = zeros(size(coordinates,1),1);
    supp_fid = fopen(supp_file);
    tline = fgets(supp_fid);
    idx = strfind(tline, ';');
    i = 0;
    while ~ isempty(idx)
        i = i+1;
        s = line_supp(tline, idx, mask);
        figure(1)
	    clf
        display_red(coordinates, s==0, s==1, s==2, s==3);
	    saveas(gcf, strrep(figures_patt, '__RULEID__', num2str(i)), format);
        tline = fgetl(supp_fid); 
        idx = strfind(tline, ';');
    end
    fclose(supp_fid);
end

function display_red(coordinates, suppO, suppL, suppR, suppI)
    scatter([ -30; coordinates(suppO,2)], [80; coordinates(suppO,1)],15, 'k.')
    hold on
    scatter([ -30; coordinates(suppL,2)], [80; coordinates(suppL,1)],10, 'c+');
    scatter([ -30; coordinates(suppR,2)], [80; coordinates(suppR,1)],10, 'mx');
    scatter([ -30; coordinates(suppI,2)], [80; coordinates(suppI,1)],10,'b*');
    %% BLACK AND WHITE
%     scatter([ -30; coordinates(suppO,2)], [80; coordinates(suppO,1)],15, 'k.')
%     hold on
%     scatter([ -30; coordinates(suppL,2)], [80; coordinates(suppL,1)],10, 'k+');
%     scatter([ -30; coordinates(suppR,2)], [80; coordinates(suppR,1)],10, 'kx');
%     scatter([ -30; coordinates(suppI,2)], [80; coordinates(suppI,1)],10, 'k*');
    legend('European continent','Left query holds','Right query holds','Both queries hold',2)
end

function s = line_supp(line, idx, mask)
    L = textscan(line(1:idx),'%u');
    R = textscan(line(idx+1:end),'%u');
    if (max(L{1})+1 > length(mask)) | (max(R{1})+1 > length(mask))
        error('Size of supports and coordinates do not match !')
    end
    s = mask;
    s(L{1}+1) = s(L{1}+1) + 1;
    s(R{1}+1) = s(R{1}+1) + 2;
end
