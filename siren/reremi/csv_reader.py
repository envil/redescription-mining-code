import csv
import sys

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
    

def row_order(L, R):
    (LhasCoord, Lcoord) = has_coord(L)
    (RhasCoord, Rcoord) = has_coord(R)
    if not (LhasCoord or RhasCoord):
        # Neither has coordinates
        raise ValueError('At least one data file must have coordinates')
    elif not (LhasCoord and RhasCoord):
        # Only one has coordinates, do not re-order rows
        data = L['data']
        head = L['headers']
        # extract the coordinates
        if LhasCoord:
            coord = Lcoord
        else:
            coord = Rcoord
        # Sanity check
        if len(data[0]) != len(R['data'][0]):
            raise ValueError('The two data sets are not of same size')
        return (range(len(data[head[0]])), range(len(data[head[0]])), coord)
    else:
        # Both have coordinates
        Llat = Lcoord[0]
        Llong = Lcoord[1]
        Rlat = Rcoord[0]
        Rlong = Rcoord[1]
        # sort per concatenated lat & long
        Lll = map(lambda x,y: str(x)+str(y), Llat, Llong)
        Rll = map(lambda x,y: str(x)+str(y), Rlat, Rlong)
        Lorder= sorted(range(len(Llat)), key=Lll.__getitem__)
        Rorder= sorted(range(len(Rlat)), key=Rll.__getitem__)
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
        return (Lorder, Rorder, coord)

def importCSV(left_filename, right_filename, csv_params={}, unknown_string=None):
    (Lh, Ld) = read_csv(left_filename, csv_params, unknown_string)
    (Rh, Rd) = read_csv(right_filename, csv_params, unknown_string)
    data = ({'data': Ld, 'headers': Lh}, {'data': Rd, 'headers': Rh})
    (Lorder, Rorder, coord) = row_order(data[0], data[1])
    data[0]['order'] = Lorder
    data[1]['order'] = Rorder
    return {'data': data, 'coord': coord}


def main(argv=[]):
    res = importCSV('mammals.csv', 'worldclim.csv', unknown_string='NA')
    print res.keys()
    print res['data'][0].keys()
    print "Left data has", len(res['data'][0]['data'][res['data'][0]['headers'][0]]), "rows"
    print "Left data has", len(res['data'][1]['data'][res['data'][1]['headers'][0]]), "rows"
    print "Coord has", len(res['coord']), "rows"
        

if __name__ == '__main__':
    main(sys.argv)
