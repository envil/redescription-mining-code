import numpy
import pdb

def withen(mat):
    tt = numpy.std(mat, 0)
    tt[numpy.where(tt == 0)] = 1
    return (mat - numpy.tile(numpy.mean(mat, 0), (mat.shape[0], 1)))/numpy.tile(tt, (mat.shape[0], 1))

def withenR(mat):
    tt = numpy.std(mat, 1)
    tt[numpy.where(tt == 0)] = 1
    return (mat - numpy.tile(numpy.mean(mat, 1), (mat.shape[1], 1)).T)/numpy.tile(tt, (mat.shape[1], 1)).T
