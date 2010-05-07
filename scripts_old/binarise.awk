## Usage awk -f <this file> <dat_data_with_cardinalities> > <binary_dat_data>
BEGIN {
    FS="\t"
}
{ 
    print $1 "\t" $2 "\t" ($3 != 0)
}