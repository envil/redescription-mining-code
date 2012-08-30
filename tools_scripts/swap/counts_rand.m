% awk -F'\t' '{print FILENAME "\t" $3 "\t" $0 }' rand_dblp/filtered_bb/results/*.rul | sed -e 's/rand_dblp.filtered_bb.results.random_//g' -e 's/.rul//g' > tmp_sort
load tmp_counts
for i = min(tmp_counts(:,1)):max(tmp_counts(:,1))
    [n(:,i+1), bins] = hist(tmp_counts(tmp_counts(:,1)==i,2), [0:0.05:1]);
end
 plot(bins, cumsum(n))
