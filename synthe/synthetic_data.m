function [log_info] = synthetic_data(params, setts, confs )
    %SYNTHETIC_BOOLEAN_DATA Generates synthetic boolean data for redescription
    %mining experiments with given parameters.
    % EXAMPLE PARAMETERS:
    % -------------------
    %      params = struct( 'directory_out', './data1/', ...
    %             'suffix','synthe', ...
    %             'differents', 10, ...
    %             'disp', true, ...
    %             'log_to_file', true, ...
    %             'side_place_holder', '::SIDE::', ...
    %             'dat_ext_L', 'bdat', ...
    %             'dat_ext_R', 'bdat', ...
    %             'info_ext', 'info');
    % 
    %     setts = struct( 'nb_rows', {100}, ... % total nb of rows
    %                 'nb_cols_L', {20}, ... % number of columns of the left hand side matrix
    %                 'nb_cols_R', {20}, ... % number of columns of the right hand side matrix
    %                 'supp_rows_L', {25}, ... % number of supporting rows of the left hand side matrix
    %                 'supp_rows_R', {25}, ... % number of supporting rows of the right hand side matrix
    %                 'nb_variables_L', {5}, ... % number of supporting variables of the left hand side matrix
    %                 'nb_variables_R', {5}, ... % number of supporting variables of the right hand side matrix
    %                 'c', {4}, ... % number of supporting variables of the right hand side matrix
    %                 'offset', {0}, ... % offset before support of right hand side matrix
    %                 'preserving', {true} , ... % boolean, is the original support of the rules perserved when adding noise
    %                 'margin_L', {1}, ... % margin left 1=boolean data
    %                 'margin_R', {1}, ... % margin right 1=boolean data
    %                 'density', {0.01}, ... % noise density
    %                 'density_blurr_OR', {0.8}, ... % supporting columns blurr OR
    %                 'density_blurr_AND', {0.2} ); % supporting columns blurr AND
    % 
    %     confs = struct( 'OR_L', {true, true, false, false}, ... 
    %                     'OR_R', {true, false, true, false}, ... 
    %                     'label', {'OO', 'OA', 'AO', 'AA'});
    
    
    titles_str = {'p:', 'd:', 'bd:', 'br'};
    if params.log_to_file
        log_info = [params.directory_out params.suffix  params.info_ext];
        fid = fopen(log_info,'w');
    else
        log_info = '-';
        fid = 1; % stdout
    end    
    for i = 1:length(setts)
        titles_fig = [setts(i).preserving setts(i).density setts(i).density_blurr_OR setts(i).density_blurr_AND];
        for l = 1:length(confs)
            for j = 0:params.differents-1
                [L, R, acc] = synthetic_boolean_data_pair(setts(i).nb_rows, setts(i).nb_cols_L, setts(i).nb_cols_R, ...
                            setts(i).supp_rows_L, setts(i).supp_rows_R, setts(i).nb_variables_L, setts(i).nb_variables_R, setts(i).c, confs(l).OR_L, confs(l).OR_R, setts(i).offset, ...
                            setts(i).preserving, setts(i).margin_L, setts(i).margin_R, setts(i).density, setts(i).density_blurr_OR, setts(i).density_blurr_AND);
                filename = [ params.side_place_holder num2str(i) confs(l).label '-' num2str(j) '_' params.suffix];
                to_log_setts = [i, l, j, acc, setts(i).nb_variables_L, setts(i).nb_variables_R, confs(l).OR_L, confs(l).OR_R, setts(i).offset, setts(i).supp_rows_L, setts(i).supp_rows_R, setts(i).preserving,  setts(i).margin_L, setts(i).margin_R, setts(i).density, setts(i).density_blurr_OR, setts(i).density_blurr_AND];
                format_setts = strrep([filename ' %i %i %i %f %i %i %i %i %i %i %i %i %f %f %f %f %f\n'], ' ', '\t');
                if length(params.directory_out) > 0
                    save_matrix(L, strrep([params.directory_out filename], params.side_place_holder, 'L'), params.dat_ext_L);
                    save_matrix(R, strrep([params.directory_out filename], params.side_place_holder, 'R'), params.dat_ext_R);
                end
                fprintf(fid, format_setts, to_log_setts);
            end
            if params.disp
                figure(i);
                subplot(1,length(confs),l); imagesc([L,R]); colormap(gray); %colorbar()
                title([titles_str{l} num2str(titles_fig(l)) ', acc:' num2str(acc)])
            end
        end
    end
    if params.log_to_file
        fclose(fid);
    end   

function [L, R, acc] = synthetic_boolean_data_pair( nb_rows, nb_cols_L, nb_cols_R, supp_rows_L, supp_rows_R, nb_variables_L, nb_variables_R, c, opOR_L, opOR_R, offset, preserving, margin_L, margin_R, density, density_blurr_OR, density_blurr_AND)
    %SYNTHETIC_BOOLEAN_DATA Generates a pair of synthetic boolean matrices for redescription
    %mining experiments.
    
    
    %% skeleton    
    if opOR_L
        [ NL, ML, QL ] = makeRuleSkeleton(nb_variables_L,  supp_rows_L-c*nb_variables_L, nb_rows-supp_rows_L, c, density_blurr_OR, false);
    else
        [ NL, QL, ML ] = makeRuleSkeleton(nb_variables_L,  nb_rows-supp_rows_L-c*nb_variables_L, supp_rows_L, c, density_blurr_AND, true);
    end

    if opOR_R
        [ NR, MR, QR ] = makeRuleSkeleton(nb_variables_R,  supp_rows_R-c*nb_variables_R, nb_rows-supp_rows_R, c, density_blurr_OR, false);
    else
        [ NR, QR, MR ] = makeRuleSkeleton(nb_variables_R,  nb_rows-supp_rows_R-c*nb_variables_R, supp_rows_R, c, density_blurr_AND, true);
    end

    %% compose the matrices
    if opOR_L
        if opOR_R
            rulec_L = [ML; NL; QL];
            rulec_R = [QR([1:offset],:); NR(:,end:-1:1); MR(:,end:-1:1); QR(1 + offset:end,:)];
        else
            rulec_L = [QL([1:offset],:); NL; ML; QL(1 + offset:end,:)];
            rulec_R = [MR; QR; NR];
        end
    else
        if opOR_R
            rulec_L = [ML; QL; NL];
            rulec_R = [QR([1:offset],:); NR; MR; QR(1 + offset:end,:)];
        else
            if c*nb_variables_L > size(QR,1)
                error('QR too small !')
            end
            rulec_L = [ML; QL(:,end:-1:1); NL];
            rulec_R = [QR(c*nb_variables_L + [1:offset],:); MR; QR(c*nb_variables_L + 1 + offset:end,:); NR; QR(1:c*nb_variables_L,:)];
        end

    end
    

    n = full(sprand(nb_rows, nb_cols_L+nb_cols_R,density) > 0); 
    if not(mod(preserving,2) ) 
        rulec_L = bitxor(rulec_L, n(:, 1:nb_variables_L));
        rulec_R = bitxor(rulec_R, n(:, nb_cols_L+1:nb_cols_L+nb_variables_R));
    end
    L = [rulec_L n(:, nb_variables_L+1:nb_cols_L)];
    R = [rulec_R n(:, nb_cols_L+nb_variables_R+1:end)];
    if preserving > 1
        idsEL = find(sum(L,2)==0);
        colsAddL = randi(nb_cols_L-nb_variables_L, [length(idsEL), 1]);
        maskL = sparse(idsEL,colsAddL,ones(size(colsAddL)),nb_rows, nb_cols_L-nb_variables_L);
        L(:, nb_variables_L+1:nb_cols_L) = L(:, nb_variables_L+1:nb_cols_L) + maskL;
        idsER = find(sum(R,2)==0);
        colsAddR = randi(nb_cols_R-nb_variables_R, [length(idsER), 1]);
        maskR = sparse(idsER,colsAddR,ones(size(colsAddR)),nb_rows, nb_cols_R-nb_variables_R);
        R(:, nb_variables_R+1:nb_cols_R) = R(:, nb_variables_R+1:nb_cols_L) + maskR;
    end
    

    prec_L=100;
    prec_R=100;

    acc = computeAcc(L, nb_variables_L, opOR_L, R, nb_variables_R, opOR_R);
    if margin_L < 1
        L =round(prec_L*abs(L-((1-max(margin_L, eps))/2*rand(size(L)))))/prec_L;
    end
    if margin_R < 1
        R =round(prec_R*abs(R-((1-max(margin_R, eps))/2*rand(size(R)))))/prec_R;  
    end

function acc = computeAcc(L, nb_variables_L, opOR_L, R, nb_variables_R, opOR_R)
    suppL = computeSuppVect(L, nb_variables_L, opOR_L);
    suppR = computeSuppVect(R, nb_variables_R, opOR_R);
    inter_c = sum(suppL & suppR);
    union_c = sum(suppL | suppR);
    acc = inter_c(1,1)/union_c(1,1);
        
function suppV = computeSuppVect(M, nb_variables, opOR)
    suppV = M(:,1)>0;
    if  opOR
        for i = 2:nb_variables
            suppV = suppV | M(:,i)>0;
        end
    else
        for i = 2:nb_variables
            suppV = suppV & M(:,i)>0;
        end
    end

function [ N, M, Q ] = makeRuleSkeleton(rows_N,  rows_M, rows_Q, c, density_add, invert)    

    if rows_N == 0 
        N = [];
        M = zeros(rows_M,0);
        Q = zeros(rows_Q,0);
    else
        N = repmat(eye(rows_N),c,1);
        diags = repmat(eye(rows_N), ceil(rows_M/rows_N),1);
        ids = randperm(rows_M*rows_N);
        nb_vals = round(rows_M*rows_N*density_add); %  max(0,min(1,normrnd(density_add, 0.05))));
        mask = zeros(rows_M*rows_N,1);
        mask(ids(1:nb_vals)) = 1;
        M = diags(randperm(rows_M),:) | reshape(mask, rows_M, rows_N);
        Q = zeros(rows_Q, rows_N);
        if invert
            N = 1-N;
            M = 1-M;
            Q = 1-Q;
        end
    end
