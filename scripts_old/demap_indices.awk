## Usage awk -f <this file> sym=1|0 <indices_from_map> > <dat_data>
BEGIN {
    FS=" "
}
{
for (i=1; i<=NF; i++) {
     if (NR > $i || sym == 0) 
        nb_co[$i+1 "\t" NR]++;
     }
} 
END {
     for (auth in nb_co) 
         printf "%s\t%i\n", auth, nb_co[auth];
}
