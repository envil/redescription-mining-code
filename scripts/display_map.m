function display_map(coordinates_file, supps_file, figures_patt, format)
    coordinates = load(coordinates_file);
    all_supps = load(supps_file);
    %rules_fid = fopen(rules_file);
    if size(all_supps,1) > size(coordinates,1) 
        error('Size of supports and coordinates do not match !')
    elseif mod(size(all_supps,2),2) == 1
        error('Not even number of supports !')
    else 
        for i=1:2:size(all_supps,2)
            %tti = fgets(rules_fid);
            figure(1)
	    clf
            s = all_supps(:,i)+2*all_supps(:,i+1);
            display_red(coordinates, s==0, s==1, s==2, s==3)
            %title(tti)
	    saveas(gcf, strrep(figures_patt, '__RULEID__', num2str((i+1)/2)), format)
        end
    end
    %fclose(rules_fid);
end

function display_red(coordinates, suppO, suppL, suppR, suppI)
    scatter([ -30; coordinates(suppO,2)], [80; coordinates(suppO,1)],25, 'k.')
    hold on
    scatter([ -30; coordinates(suppL,2)], [80; coordinates(suppL,1)],25, 'b.');
    scatter([ -30; coordinates(suppR,2)], [80; coordinates(suppR,1)],25, 'r.');
    scatter([ -30; coordinates(suppI,2)], [80; coordinates(suppI,1)],25, 'g.');
    legend('European continent','Left rule holds','Right rule holds','Both rules hold',2)
end
