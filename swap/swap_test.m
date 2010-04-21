base_rep = '/fs-1/3/galbrun/redescriptors/sandbox/';
path(path,[ base_rep 'scripts/']);
Xcoauth = load_matrix([ base_rep 'dblp/coauthor_filtered'], 'bdat');
Xconf = load_matrix([ base_rep 'dblp/conference_filtered'], 'bdat');

Dcoauth = sparse(triu(Xcoauth(1:3000,1:3000)+1));

figure(1)
subplot(2,1,1)
imagesc(Dcoauth)
subplot(2,1,2)
imagesc(Xconf)


for i = 1:1
    [Xconf_r,accRatem,realChangesm,attemptsm,Pm] = swap(Xconf);
    realChangesm/attemptsm
    [Dcoauth_r,accRatew,realChangesw,attemptsw,Pw] = swap(Dcoauth);
    realChangesw/attemptsw
    figure(i+1)
    subplot(2,2,1)
    imagesc(Xconf_r-Xconf)
    colorbar
    subplot(2,2,2)
    imagesc(Dcoauth_r-Dcoauth)
    colorbar
    subplot(2,2,3)
    imagesc(Xconf)
    subplot(2,2,4)
    imagesc(Dcoauth_r)
end

% X = rand(10,5);
% DX = discretize(X);
% DY = swap(DX);
% Y = undiscretize(DY,X);

% base_rep = '/fs-1/3/galbrun/redescriptors/sandbox/';
% path(path,[ base_rep 'scripts/']);
% Xmam = load_matrix([ base_rep 'rajapaja/mammals'], 'bdat');
% Xwc_tp = load_matrix([ base_rep 'rajapaja/worldclim_tp'], 'num');
% 
% 
% Swc_tp = scale_data(Xwc_tp);
% Dwc_tp = discretize(Swc_tp);
% 
% figure(1)
% subplot(2,1,1)
% imagesc(Xmam)
% subplot(2,1,2)
% imagesc(Swc_tp)
% 
% for i = 1:5
%     [Xmam_r,accRatem,realChangesm,attemptsm,Pm] = swap(Xmam);
%     realChangesm/attemptsm
%     [Dwc_tp_r,accRatew,realChangesw,attemptsw,Pw] = swap(Dwc_tp);
%     Swc_tp_r = undiscretize(Dwc_tp_r, Swc_tp);
%     realChangesw/attemptsw
%     figure(i+1)
%     subplot(2,2,1)
%     imagesc(Xmam_r-Xmam)
%     colorbar
%     subplot(2,2,2)
%     imagesc(Swc_tp_r-Swc_tp)
%     colorbar
%     subplot(2,2,3)
%     imagesc(Xmam_r)
%     subplot(2,2,4)
%     imagesc(Swc_tp_r)
%     Xwc_tp_r = unscale_data(Swc_tp_r, Xwc_tp);
%     %save_matrix(Xmam_r, [ base_rep 'rand_rajapaja/A/data/mammals_' num2str(i)], 'bdat');
%     %save_matrix(Xwc_tp_r, [ base_rep 'rand_rajapaja/A/data/worldclim_tp_' num2str(i)], 'num');
% end
% 
% % Dwc_t = discretize(Xwc_tp(:,1:36));
% % Dwc_p = discretize(Xwc_tp(:,37:end));
% % 
% % for i = 1:5
% %     Xmam_r = swap(Xmam);
% %     Dwc_t_r = swap(Dwc_t);
% %     Dwc_p_r = swap(Dwc_p);
% %     Xwc_tp_r = [undiscretize(Dwc_t_r, Xwc_tp(:,1:36)) undiscretize(Dwc_p_r, Xwc_tp(:,37:end))];
% %     figure(i+1)
% %     subplot(2,1,1)
% %     imagesc(Xmam_r)
% %     subplot(2,1,2)
% %     imagesc(Xwc_tp_r)
% %     %save_matrix(Xmam_r, [ base_rep 'rand_rajapaja/A/data/mammals_' num2str(i)], 'bdat');
% %     %save_matrix(Xwc_tp_r, [ base_rep 'rand_rajapaja/A/data/worldclim_tp_' num2str(i)], 'num');
% % end
% 
