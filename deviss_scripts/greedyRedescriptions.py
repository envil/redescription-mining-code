#!/usr/bin/python

import ConfigParser
import sys, re, datetime
from classLog import Log
from classSettings import Settings
from classData import Data
from classRedescription import Redescription
from classConstraints import Constraints
from classQuery import Query, Term, NumItem
import pdb
import pickle

# def writeOut(setts, tmpCurrGen):
#     if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_queries']) > 0:
#         queriesOutFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_queries'], 'w')
#     else: queriesOutFp = sys.stdout

#     if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_support']) > 0:
#         supportOutFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_support'], 'w')
#     else:
#         supportOutFp = None

#     for red in tmpCurrGen:
#         red.write(queriesOutFp, supportOutFp)

#     queriesOutFp.close()
#     supportOutFp.close()


def writeDown(setts, serie, step, tmpCurrGen, tmpExtKeys):
    pic = open(setts.param['result_rep']+'pickles_' + serie + '_step' + step + '.sav', 'w')
    pickle.dump(tmpExtKeys, pic)
    pic.close()

    queriesOutFp = open(setts.param['result_rep']+'queries_' + serie + '_step' + step + '.sav', 'w')
    for red in tmpCurrGen:
        queriesOutFp.write("%s\t%s\t%s\n" % (red[0][0].disp(), red[0][1].disp(), ' '.join([ "%s:%f" % (key, val) for (key, val) in red[1].items()])))
    queriesOutFp.close()

def readUp(data, setts, serie, step):
    pic = open(setts.param['result_rep']+'pickles_' + serie + '_step' + step + '.sav', 'r')
    tmpExtKeys = pickle.load(pic)
    pic.close()

    queriesInFp = open(setts.param['result_rep']+'queries_' + serie + '_step' + step + '.sav', 'r')
    tmpCurrGen = []
    for line in queriesInFp:
        parts = line.strip().split('\t')
        if len(parts) == 3:
            queryL = Query.parse(parts[0])
            queryR = Query.parse(parts[1])
            scores = {}
            for scoreP in parts[2].strip().split(' '):
                scorePP = scoreP.split(':')
                scores[scorePP[0]] =  float(scorePP[1])
            tmpCurrGen.append(([queryL, queryR], scores))
        else:
            break
    queriesInFp.close()
    return (tmpCurrGen, tmpExtKeys)


# def readUp(data, setts, serie, step):
#     pic = open(setts.param['result_rep']+'pickles_' + serie + '_step' + step + '.sav', 'r')
#     tmpExtKeys = pickle.load(pic)
#     pic.close()

#     queriesInFp = open(setts.param['result_rep']+'queries_' + serie + '_step' + step + '.sav', 'r')
#     supportInFp = open(setts.param['result_rep']+'support_' + serie + '_step' + step + '.sav', 'r')
#     tmpCurrGen = []
#     while True:
#         (currentR, comment, commentSupp)= Redescription.load(queriesInFp, supportInFp, data)
#         if len(currentR) == 0 and comment == '':
#                 break
#         else:
#             tmpCurrGen.append(currentR)
#     queriesInFp.close()
#     supportInFp.close()
#     return (tmpCurrGen, tmpExtKeys)

def main():
    setts = Settings('mine', sys.argv)
    if setts.getParams() == 0:
        print setts.dispHelp()
        sys.exit(2)
    logger = Log(setts.param['verbosity'], setts.param['logfile'])
    logger.printL(5,'Settings:\n' + setts.dispParams())

    tic = datetime.datetime.now()
    logger.printL(1,"TIC... Started: %s" % tic)

    Data.logger = logger; Redescription.logger = logger; 
    
    data = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
    logger.printL(2, data)

    constraints = Constraints(data, setts)
    Redescription.settings(setts)

    serie = "%d_%d" % (100*constraints.maxOvP(), 100*constraints.maxBestAccRP())

    data.selectUncorr(0)
    data.selectUncorr(1)

    (tmpCurrGen, tmpIdsSets) = data.initializeRedescriptions(setts.param['nb_pairs'], constraints )
    writeDown(setts, serie, "%d" % constraints.redLength(), tmpCurrGen, tmpIdsSets)

#    (tmpCurrGen, tmpIdsSets) = readUp(data, setts, serie, "%d" % constraints.redLength())
    ## FIRST GEN
    (tmpCurrGen, tmpExtKeys) = data.firstGen(tmpCurrGen, tmpIdsSets, constraints)
    writeDown(setts, serie, "%d" % constraints.redLength(), tmpCurrGen, tmpExtKeys)
    
    pdb.set_trace()

    for i in range(3):
        (tmpCurrGen, tmpExtKeys) = data.nextGen(tmpCurrGen, tmpExtKeys, constraints)
        writeDown(setts, serie, "%d" % constraints.redLength(), tmpCurrGen, tmpExtKeys)
        
    # constraints.setRedLength(1)

    # ## SECOND GEN
    # 
    # writeDown(setts, serie, "%d" % constraints.redLength(), tmpCurrGen, tmpExtKeys)
    # # writeOut(setts, tmpCurrGen)
    # constraints.setRedLength(2)
    # (tmpCurrGen, tmpExtKeys) = readUp(data, setts, serie, "%d" % constraints.redLength())
    # ## THIRD GEN
    # for i in range(2):
    #     (tmpCurrGen, tmpExtKeys) = data.nextGen(tmpCurrGen, tmpExtKeys, constraints)
    #     writeDown(setts, serie, "%d" % constraints.redLength(), tmpCurrGen, tmpExtKeys)
    # # writeOut(setts, tmpCurrGen)


    tac = datetime.datetime.now()
    logger.printL(1,"TAC... Ended: %s" % tac)
    logger.printL(1,"TIC-TAC Elapsed: %s" % (tac-tic))

    logger.printL(1, 'THE END')
## END of main()

if __name__ == "__main__":
    main()


    
