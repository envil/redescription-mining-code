function [mat_bin, bounds] = bin_matrix(mat_real, N, how)

if nargin < 3, how = 'means'; end
if nargin < 2, N = 10; end

[n,m] = size(mat_real);
if (length(N) ~= m)
    N = N(1)*ones(m,1);
end
eps = 0.001;
mat_bin = sparse(n,sum(N));
bounds = cell(m,1);

if strcmp(how, 'width')
    for i=1:m
        mi = min(mat_real(:,i));
        ma = max(mat_real(:,i))+eps;
        width = (ma-mi)/N(i);
        bounds{i} = mi + (1:N(i)-1)*width;
        for j=1:N(i)
            mat_bin(((mat_real(:,i)>=(mi+(j-1)*width)) & (mat_real(:,i)<(mi+(j)*width))),sum(N(1:i-1))+j) = 1;
        end
    end

elseif strcmp(how, 'height')
    for i=1:m
        ptiles = prctile(mat_real(:,i), [0:N(i)]*100/N(i));
        ptiles(end) = ptiles(end)+eps;
        bounds{i} = ptiles(2:end-1);
        for j=1:N(i)
            mat_bin(((mat_real(:,i)>=ptiles(j)) & (mat_real(:,i)<ptiles(j+1))),sum(N(1:i-1))+j) = 1;
        end
    end
    
elseif strcmp(how, 'means')
    warning('OFF','stats:kmeans:EmptyCluster')
    warning('OFF','stats:kmeans:FailedToConverge')
    for i=1:m
        [ids_tmp, c] = kmeans(mat_real(:,i), N(i), 'Start', 'uniform', 'EmptyAction', 'singleton');
        [y,clust_id] = sort(c);
        for j=1:length(clust_id)
            mat_bin(ids_tmp==clust_id(j),sum(N(1:i-1))+j) = 1;
        end
        bounds{i} = y(1:end-1) + diff(y)/2;
    end

 elseif strcmp(how, 'segments')
    max_N = N;
    for i=1:m
        [assign, bounds{i}, cost, N(i)] = segment(mat_real(:,i),max_N(i));
        mat_bin(sub2ind(size(mat_bin), [1:n],assign+sum(N(1:i-1))))=1;
    end     

else
    error('How do you want to bin the data (width/height/means/segments)?')
end
