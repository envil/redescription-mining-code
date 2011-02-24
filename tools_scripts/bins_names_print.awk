## Usage awk -f <this file> sparseg=1|0 <original_names> <bins bounds> > <binned_names>
## Generate the names for binned data from original names (one column name per line),
## bin bounds (one column's bounds per line, nb_bins-1 )
BEGIN {
  FS="\t"
}
{
    if (FILENAME == ARGV[2]) ids[++i] = $0 ;
    else if (FILENAME == ARGV[3]) {
	if ( sparseg == 0){
	    print ids[FNR] " $\\in (-\\infty," $1 "]$"
	}
	for(i=1;i<NF;i++)
	{
	    print ids[FNR] "$\\in [" $i "," $(i+1) "]$"
	}
	print  ids[FNR] "$\\in [" $i ",+\\infty)$"
    }
}
