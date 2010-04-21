function [XS] = scale_data(X)
% scale_data Scale each column of the data linearly to [0-1]
    Xmin = repmat(min(X), size(X, 1), 1);
    Xsc = max(X)-min(X);
    if (sum(Xsc==0) > 0)
        warning('Column with all identical values !')
        Xsc(Xsc==0) = 1;
    end
    XS = (X - Xmin)*diag(1./Xsc);

end

