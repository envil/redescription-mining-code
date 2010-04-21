function [X] = unscale_data(XS, Xo)
% unscale_data Unscale each column of the data, using scale such that columns from Xo gets linearly scaled to [0-1]
    Xmin = repmat(min(Xo), size(Xo, 1), 1);
    Xsc = max(Xo)-min(Xo);
    Xsc(Xsc==0) = 1;
    X = (XS*diag(Xsc) + Xmin);
end