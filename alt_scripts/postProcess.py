#!/usr/bin/python

import sys, getopt, numpy , utilsIO
from classSettings import Settings
from classConstraints import Constraints
from classLog import Log
from classRedescription import *
from classData import *
from classRedescriptionsDraft import *
import pdb
## Ignore future warning for the hist function
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

def main():

    setts = Settings('post', sys.argv)
    if setts.getParams() == 0:
        print setts.dispHelp()
        sys.exit(2)
    logger = Log(setts.param['verbosity'], setts.param['logfile'])
    logger.printL(5,'Settings:\n' + setts.dispParams())
    if setts.param['ext_l'] != '' and setts.param['ext_r'] != '' :
        data = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
        dataRed = Data([setts.param['data_rep']+setts.param['data_l']+setts.param['ext_l'], setts.param['data_rep']+setts.param['data_r']+setts.param['ext_r']])
    else:
        data = None
        dataRed = None
    constraints = Constraints(data, setts)
    Redescription.methodpVal = setts.param['method_pval'].capitalize()

    setts.param['name'] = False
    names = [None, None]
    if len(setts.param['labels_l']) > 0 and len(setts.param['labels_r']) >0:
        names[0] = utilsIO.getNames(setts.param['data_rep']+setts.param['data_l']+setts.param['labels_l'], data.nbCols(0), data.nbCols(0)==0)
        names[1] = utilsIO.getNames(setts.param['data_rep']+setts.param['data_r']+setts.param['labels_r'], data.nbCols(1), data.nbCols(1)==0)
        if  names[0] == None or names[1] == None  :
            logger.printL(1,'Labels are missing or incorrect, will not be able to print named queries ...')
        else:
            setts.param['name'] = True
        
    suff = ''
    if setts.param['recompute']:
        suff = '_recomputed'
    if setts.param['filtrate']:
        suff = '_filtrated'
    if setts.param['redundancy_mark']:
        suff = '_marked'
    if setts.param['redundancy_prune']:
        setts.param['redundancy_mark'] = False
        suff = '_pruned'

    readyDraft = None
    if setts.param['duplicate_mark']>0:
        suff = '_dupmarked'
        setts.param['max_side_identical']=setts.param['duplicate_mark']
        readyDraft = RedescriptionsDraft()
    if setts.param['duplicate_prune']>0:
        suff = '_duppruned'
        setts.param['max_side_identical']=setts.param['duplicate_prune']
        readyDraft = RedescriptionsDraft()
    
        
    queriesInFp = None
    queriesOutFp = None
    supportInFp = None
    supportOutFp = None
    namesOutFp = None
    printOutFp = None

    if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_queries']) > 0:
        queriesInFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_queries'], 'r')
        if suff != '':
            queriesOutFp = open(setts.param['result_rep']+setts.param['out_base']+suff+setts.param['ext_queries'], 'w')

        if setts.param['name']:
            namesOutFp = open(setts.param['result_rep']+setts.param['out_base']+suff+setts.param['ext_names'], 'w')

        if setts.param['ext_print']!='':
            printOutFp = open(setts.param['result_rep']+setts.param['out_base']+suff+setts.param['ext_print'], 'w')
            printOutFp.write('\\begin{tabular}{@{\\hspace*{0.5ex}}p{0.027\\textwidth}@{}p{0.35\\textwidth}@{\\hspace*{1em}}p{0.4\\textwidth}@{\\hspace*{1em}}rrr@{\\hspace*{0.5ex}}}\n')
            printOutFp.write('\\topquery\n'+Redescription.dispPrintHeader()+'\n\\midquery\n')
            

    else:
        queriesInFp = sys.stdin
        if suff != None:
            if setts.param['name']:
                namesOutFp = sys.stdout
            else:
                queriesOutFp = sys.stdout

    if setts.param['out_base'] != "-"  and len(setts.param['out_base']) > 0  and len(setts.param['ext_support']) > 0:
        if not setts.param['recompute']:
            supportInFp = open(setts.param['result_rep']+setts.param['out_base']+setts.param['ext_support'], 'r')
        if len(setts.param['ext_support']) > 0 and suff != '':
            supportOutFp = open(setts.param['result_rep']+setts.param['out_base']+suff+setts.param['ext_support'], 'w')

    queryNro = 1
    while True:

        (currentR, comment, commentSupp)= Redescription.load(queriesInFp, supportInFp, data)
        if len(currentR) == 0 and comment == '':
                break
        else:
            logger.printL(2,'Reading query # %i'%queryNro)
#            pdb.set_trace()
            ################# SANITY CHECK
            if setts.param['sanity_check'] :
                (res, details) = currentR.check(data)
                if res == 0:
                    logger.printL(0,'Query has toy supports !')
                elif res == 1:
                    logger.printL(0,"Query %i Sanity check OK !" % queryNro)
                elif res == -1:
                    logger.printL(0,"Query %i Sanity check KO ! (%s)" % (queryNro, details))
                else:
                    logger.printL(0,"Something happend while analysing query %i !" % queryNro)

            ################# RECOMPUTE
            if setts.param['recompute'] and data != None :
                currentR.recompute(data)

            ################# FILTRATE
            if setts.param['filtrate'] and  constraints.checkFinalConstraints(currentR):
                currentR = None
                logger.printL(0,"Query %i filtered out!" % queryNro)

            ################# REDUNDANCY
	    if currentR != None and (setts.param['redundancy_prune'] or setts.param['redundancy_mark']) and data != None :
                currentRedun = currentR.copy()
                currentRedun.recompute(dataRed)
                if currentRedun.lenU() == 0 :
                    if setts.param['redundancy_mark']:
                        comment = '# REDUNDANT RULE NO SUPPORT LEFT ' + comment
                        commentSupp = '# REDUNDANT RULE NO SUPPORT LEFT ' + commentSupp
                    else:
                        currentR = None
                        logger.printL(0,"Query %i redundant no support left, pruned!" % queryNro)
                elif not constraints.checkFinalConstraints(currentRedun):
                    if setts.param['redundancy_mark']:
                        comment = '# REDUNDANT RULE ' + currentRedun.dispCaracteristiquesSimple() + comment
                        commentSupp = '# REDUNDANT RULE ' + commentSupp
                    else:
                        currentR = None
                        logger.printL(0,"Query %i redundant do not comply with filtering, pruned!" % queryNro)                    
                else:
                    if setts.param['redundancy_mark']:
                        comment = '# ' + currentRedun.dispCaracteristiquesSimple() + comment
                    dataRed.addRedunRows(currentRedun.suppI())


            ################# DUPLICATES
	    if currentR != None and readyDraft != None:
                insertedIds = readyDraft.updateCheckOneSideIdentical([currentR], setts.param['max_side_identical'])
                if len(insertedIds) == 0 :
                    if setts.param['duplicate_prune'] > 0:
                        currentR = None
                        logger.printL(0,"Query %i duplicate, pruned!" % queryNro)
                    else:
                        comment = '# DUPLICATE RULE ' + comment
                        commentSupp = '# DUPLICATE RULE ' + commentSupp


            ################# WRITING OUT
            if currentR != None and queriesOutFp != None:
                queriesOutFp.write(currentR.dispSimple()+' '+comment+'\n')
            if currentR != None and supportOutFp != None:
                supportOutFp.write(currentR.dispSupp()+' '+commentSupp+'\n')
            if currentR != None and namesOutFp != None:
                namesOutFp.write(currentR.dispSimple(0, names)+' '+comment+'\n')
            if currentR != None and printOutFp != None:
                printOutFp.write(currentR.dispPrint(queryNro, names)+' '+comment+'\n')


            queryNro += 1
    logger.printL(2,'Read all %i queries.'%(queryNro-1))
 
    if queriesOutFp != None :
        queriesOutFp.close()     
 
    if namesOutFp != None :
        namesOutFp.close()     

    if printOutFp != None :
        printOutFp.write('\\bottomquery\n\\end{tabular}\n\n')
        printOutFp.close()
 
    if supportOutFp != None :
        supportOutFp.close()     
    logger.printL(1,'THE END')
        
## END of main()

if __name__ == "__main__":
    main()
