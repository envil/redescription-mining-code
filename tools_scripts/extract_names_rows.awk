## Usage awk -f <this file> <ordered selected ids> <org names> > <ordered selected names preceded by id>
## Each line of the output contains new id, old id, name
BEGIN {
  FS="\t"
}
{
    if (ARGIND == 1) ids[$0+1] = i++ ;
    else if (ARGIND == 2) {
	if (FNR in ids) {
	    print  ids[FNR] "\t" FNR-1 "\t" $0
	}

    }
}
{
    if (ARGIND == 1) ids[$0+1] = i++ ;
    else if (ARGIND == 2) {
	for(i=1;i<NF;i++)
	{
		if ($i in ids) {
	    		print  ids[$i] "\t" FNR-1 "\t" $0
		}
	}

    }
}
# 'BEGIN { FS="\t"; i=0; while ((getline item_id < "'${SUB_IDS_F}'") > 0)
#                     { i++; ids[item_id+1] = i; } }
#             FNR in ids {print  ids[FNR] "\t" FNR-1 "\t" $0}
# '
# cat /group2/home/hiit_bru/duplicateDescriptors/dblp/orig/coauthor-map | cut -f 1 | sed "s/'/??/g" | awk '{printf "auth\(%i,:\)=_% 20.20s_;\n", NR, $0 }' | sed "s/_/'/g"  > auth_names.m
# cat /group2/home/hiit_bru/duplicateDescriptors/dblp/orig/conference-map | cut -f 1 | sed "s/'/??/g" | awk '{printf "conf\(%i,:\)=_% 100.100s_;\n", NR, $0 }' | sed "s/_/'/g"  > conf_names.m

