function [assign, bounds, cost, k] = segment(V,max_k)
%V = [1 3 5 6 7 8 9 9 10];
%T = [1 3 5 6 7 8 9 10];

%V = randi(10,[1,10]);
%V = [10     6     1     5     2    10     6     9     7     5];
%max_k = 5
[T,I,J] = unique(V);
occurences = hist(J, max(J))';

n = length(T);
cumocc = [0; cumsum(occurences)];
cs = [0; cumsum(T.*occurences)];
css = [0; cumsum(T.^2.*occurences)];
sigma = zeros(length(T));

for i=1:length(T)
    for j=i+1:length(T)
        sigma(i,j) = (css(j+1) - css(i)) - (1/(cumocc(j+1)-cumocc(i)))*(cs(j+1)-cs(i)).^2;
    end
end

E = zeros(max_k,n);
E(1,:) = sigma(1,:);
B = zeros(max_k,n);

for k=2:max_k
    for cutp=k:n
        [E(k,cutp),B(k,cutp)]=min(E(k-1,[1:cutp-1])+sigma([2:cutp],cutp)');
    end
end

[cost,opt_k] = min(E(:,n));
cuts = [B(opt_k,n) n];
for j = opt_k-1:-1:2
    tmp = B(j,cuts(1));
    cuts = [tmp cuts];
end
cuts = [0 cuts];
buckets = zeros(1,n);
bounds = [];
for i=1:length(cuts)-1
    buckets(cuts(i)+1:cuts(i+1)) = i;
    bounds = [bounds T(cuts(i)+1)];
end

bounds = bounds(2:end);
assign = buckets(J);

% E
% B
% 
% T = [1 3 5 6 7 8 9 9 10];
% n = length(T);
%
% cs = [0 cumsum(T)];
% css = [0 cumsum(T.^2)];
% 
% sigma = zeros(n);
% 
% for i=1:n
%     for j=i+1:n
%         sigma(i,j) = (css(j+1) - css(i)) - (1/(j-i+1))*(cs(j+1)-cs(i)).^2;
%     end
% end
% 
% E = zeros(max_k,n);
% E(1,:) = sigma(1,:);
% B = zeros(max_k,n);
% 
% for k=2:max_k
%     for cutp=k:n
%         [E(k,cutp),B(k,cutp)]=min(E(k-1,[1:cutp-1])+sigma([2:cutp],cutp)');
%     end
% end
% 
% 
% E
% B
