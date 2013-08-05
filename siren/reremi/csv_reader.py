import csv
import sys
import pdb

def read_csv(filename, csv_params={}, unknown_string=None):
    with open(filename, 'rb') as f:
        dialect = csv.Sniffer().sniff(f.read(2048))
        f.seek(0)
        #header = csv.Sniffer().has_header(f.read(2048))
        #f.seek(0)
        header = True
        csvreader = csv.reader(f, dialect=dialect, **csv_params)
        if header:
            head = csvreader.next()
            data = dict(zip(head, [[] for i in range(len(head))]))
            no_of_columns = len(head)
        else:
            head = None
        for row in csvreader:
            if head is None:
                head = [str(i) for i in range(len(row))]
                no_of_columns = len(head)
                data = dict(zip(head,
                                [[] for i in range(len(row))]))
            if len(row) != no_of_columns:
                raise ValueError('number of columns does not match (is '+
                                 str(len(row))+', should be '+
                                 str(no_of_columns)+')')
            for i in range(len(row)):
                if row[i] != unknown_string:
                    data[head[i]].append(row[i])
                else:
                    data[head[i]].append(None)
    return (head, data)

def has_coord(D):
    latitude = ('lat', 'latitude', 'Lat', 'Latitude')
    longitude = ('long', 'longitude', 'Long', 'Longitude')

    hasCoord = False
    coord = (None, None)
    for s in latitude:
        if s in D['headers']:
            for t in longitude:
                if t in D['headers']:
                    hasCoord = True
                    coord = (D['data'][s], D['data'][t])
                    del D['data'][s]
                    del D['data'][t]
                    D['headers'].remove(s)
                    D['headers'].remove(t)
                    break
        if hasCoord:
            break

    return (hasCoord, coord)

def has_ids(D):
    identifiers = ('id', 'identifier', 'Id', 'Identifier', 'ids', 'identifiers', 'Ids', 'Identifiers')

    hasIds = False
    ids = None
    for s in identifiers:
        if s in D['headers']:
            if not hasIds:
                hasIds = True
                ids = D['data'][s]
            del D['data'][s]
            D['headers'].remove(s)
            break

    return (hasIds, ids)    

def row_order(L, R):
    (LhasCoord, Lcoord) = has_coord(L)
    (RhasCoord, Rcoord) = has_coord(R)
    (LhasIds, Lids) = has_ids(L)
    (RhasIds, Rids) = has_ids(R)

    order_keys = [[],[]]
    if (LhasCoord and RhasCoord):
        order_keys = [Lcoord, Rcoord]
    if (LhasIds and RhasIds):
        order_keys[0].append(Lids)
        order_keys[1].append(Rids)

    if len(order_keys[0]) > 0:
        # Both have coordinates
        # Llat = Lcoord[0]
        # Llong = Lcoord[1]
        # Rlat = Rcoord[0]
        # Rlong = Rcoord[1]
        # sort per concatenated lat & long
        Lll = ["::".join(map(str, p)) for p in zip(*order_keys[0])]
        Rll = ["::".join(map(str, p)) for p in zip(*order_keys[1])]
        # Lll = map(lambda x,y: str(x)+str(y), Llat, Llong)
        # Rll = map(lambda x,y: str(x)+str(y), Rlat, Rlong)
        Lorder= sorted(range(len(Lll)), key=Lll.__getitem__)
        Rorder= sorted(range(len(Rll)), key=Rll.__getitem__)
        both = set(Lll).intersection(Rll)
        
        # Remove from Lorder and Rorder the parts that aren't in both
        i = 0
        while i < len(Lorder):
            if Lll[Lorder[i]] not in both:
                del Lorder[i]
            else:
                i += 1

        while i < len(Rorder):
            if Rll[Rorder[i]] not in both:
                del Rorder[i]
            else:
                i += 1

        # Order Lcoord according to Lorder
        coord = [(Lcoord[0][Lorder[i]], Lcoord[1][Lorder[i]]) for i in range(len(Lorder))]
        ids = None
        if LhasIds:
            ids = [Lids[Lorder[i]] for i in range(len(Lorder))]
        elif RhasIds:
            ids = [Rids[Rorder[i]] for i in range(len(Rorder))]
        return (Lorder, Rorder, coord, ids)
    else:
    # if not (LhasCoord or RhasCoord):
    #     # Neither has coordinates
    #     raise ValueError('At least one data file must have coordinates')
    # elif not (LhasCoord and RhasCoord):
        # Only one has coordinates, do not re-order rows
        data = L['data']
        head = L['headers']
        # extract the coordinates
        if LhasCoord:
            coord = Lcoord
        elif RhasCoord:
            coord = Rcoord
        else:
            coord = None

        ids = None
        if LhasIds:
            if len(L["data"].values()[0]) == len(Lids):
                ids = Lids
        elif RhasIds:
            if len(R["data"].values()[0]) == len(Rids):
                ids = Rids


        # Sanity check
        if len(data.values()[0]) != len(R['data'].values()[0]):
            raise ValueError('The two data sets are not of same size')
        return (range(len(data[head[0]])), range(len(data[head[0]])), coord, ids)


def importCSV(left_filename, right_filename, csv_params={}, unknown_string=None):
    (Lh, Ld) = read_csv(left_filename, csv_params, unknown_string)
    (Rh, Rd) = read_csv(right_filename, csv_params, unknown_string)
    data = ({'data': Ld, 'headers': Lh}, {'data': Rd, 'headers': Rh})
    (Lorder, Rorder, coord, ids) = row_order(data[0], data[1])
    data[0]['order'] = Lorder
    data[1]['order'] = Rorder
    return {'data': data, 'coord': coord, "ids": ids}


def main(argv=[]):
    rep = "/home/galbrun/redescriptors/data/vaalikone/"
    res = importCSV(rep+"vaalikone_profiles_re.csv", rep+"vaalikone_questions_re.csv", unknown_string='NA')
    #res = importCSV('mammals.csv', 'worldclim.csv', unknown_string='NA')
    print res.keys()
    print res['data'][0].keys()
    print "Left data has", len(res['data'][0]['data'][res['data'][0]['headers'][0]]), "rows"
    print "Left data has", len(res['data'][1]['data'][res['data'][1]['headers'][0]]), "rows"
    if res['coord'] is not None:
        print "Coord has", len(res['coord']), "rows"
    if res['ids'] is not None:
        print "Ids has", len(res['ids']), "rows"


if __name__ == '__main__':
    main(sys.argv)
