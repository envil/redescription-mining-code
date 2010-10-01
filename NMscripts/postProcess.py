#!/usr/bin/python

import ConfigParser
import sys, getopt, numpy, utilsIO
from classRedescription import *
from classData import *
import pdb
## Ignore future warning for the hist function
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)


def getOpts(conf_filename):
    
    # Default settings
    setts = { 'verbosity': 1, 'logfile': '-',
              'data_rep': './',
              'data_l': 'left', 'ext_l':'.bdat', 'labels_l': '',
              'data_r': 'right', 'ext_r':'.bdat', 'labels_r': '',
              'result_rep': './', 'out_base': 'out' , 'ext_rules': '.rul', 'ext_support': '.supp', 'ext_names': '.names',
              'min_length':2, 'min_suppin': 0.1, 'min_suppout': 0.7, 'min_acc': 0.0, 'max_pval': 0.05, 'method_pval' : 'marg',
              'sanity_check': False,'recompute': False, 'filtrate': False, 'redundancy_mark': False, 'redundancy_prune': False
              }

    # Sections to read in the config file
    sections_read = ['log', 'files', 'post']

    config = ConfigParser.ConfigParser() 
    config.read(conf_filename)
    for sect in sections_read: 
        if config.has_section(sect):
            for (opti,val) in config.items(sect):
                if setts.has_key(opti):
                    try:
                        setts[opti] = type(setts[opti])(val)
                    except ValueError:
                        raise Exception('Unexpected value for %s %s, default is %s.' %(opti, val, setts[opti]))
    return setts

def main():
    if len(sys.argv) > 1:
        conf_filename = sys.argv[1]
    else:
        conf_filename = ''
    setts = getOpts(conf_filename)
    logger = Log(setts['verbosity'], setts['logfile'])
    logger.printL(2,"Settings:\n %s" % (setts))
    data = Data([setts['data_rep']+setts['data_l']+setts['ext_l'], setts['data_rep']+setts['data_r']+setts['ext_r']])
    dataRed = Data([setts['data_rep']+setts['data_l']+setts['ext_l'], setts['data_rep']+setts['data_r']+setts['ext_r']])


    setts['name'] = False
    names = [None, None]
    if len(setts['labels_l']) > 0 and len(setts['labels_r']) >0:
        names[0] = utilsIO.getNames(setts['data_rep']+setts['data_l']+setts['labels_l'], data.nbCols(0), data.nbCols(0)==0)
        names[1] = utilsIO.getNames(setts['data_rep']+setts['data_r']+setts['labels_r'], data.nbCols(1), data.nbCols(1)==0)
        if  names[0] == None or names[1] == None  :
            logger.printL(1,'Labels are missing or incorrect, will not be able to print named rules ...')
        else:
            setts['name'] = True
        
    suff = None
    if setts['recompute']:
        suff = '_recomputed'
    if setts['filtrate']:
        suff = '_filtrated'
    if setts['redundancy_mark']:
        suff = '_marked'
    if setts['redundancy_prune']:
        setts['redundancy_mark'] = False
        suff = '_pruned'
        
    rulesInFp = None
    rulesOutFp = None
    supportInFp = None
    supportOutFp = None
    namesOutFp = None

    if setts['out_base'] != "-"  and len(setts['out_base']) > 0  and len(setts['ext_rules']) > 0:
        rulesInFp = open(setts['result_rep']+setts['out_base']+setts['ext_rules'], 'r')
        if suff != None:
            rulesOutFp = open(setts['result_rep']+setts['out_base']+suff+setts['ext_rules'], 'w')
            if setts['name']:
                namesOutFp = open(setts['result_rep']+setts['out_base']+suff+setts['ext_names'], 'w')
    else:
        rulesInFp = sys.stdin
        if suff != None:
            if setts['name']:
                namesOutFp = sys.stdout
            else:
                rulesOutFp = sys.stdout

    if setts['out_base'] != "-"  and len(setts['out_base']) > 0  and len(setts['ext_support']) > 0:
        supportInFp = open(setts['result_rep']+setts['out_base']+setts['ext_support'], 'r')
        if suff != None:
            supportOutFp = open(setts['result_rep']+setts['out_base']+suff+setts['ext_support'], 'w')
        
    ruleNro = 1
    while True:

        (currentR, comment, commentSupp)= Redescription.load(rulesInFp, supportInFp, data)
        if len(currentR) == 0 and comment == '':
                break
        else:
            logger.printL(2,'Reading rule # %i'%ruleNro)
#            pdb.set_trace()
            ################# SANITY CHECK
            if setts['sanity_check'] :
                res = currentR.check(data)
                if res == None:
                    logger.printL(0,'Rule has toy supports !')
                elif type(res) == tuple and len(res)==3:
                    if res[0] *res[1] *res[2] == 1:
                        logger.printL(0,"Rule %i OK !" % ruleNro)
                    else:
                        logger.printL(0,"Rule %i WRONG ! (%s)" % (ruleNro, res))
                else:
                    logger.printL(0,"Something happend while analysing rule %i !" % ruleNro)

            ################# RECOMPUTE
            if setts['recompute'] and data != None :
                currentR.recompute(data)

            ################# FILTRATE
            if setts['filtrate'] and \
                   ( currentR.length(0) + currentR.length(1) < setts['min_length'] \
                   or currentR.N - currentR.lenU() < setts['min_suppout'] \
                   or currentR.lenI() < setts['min_suppin'] \
                   or currentR.acc()  < setts['min_acc'] \
                   or currentR.pVal() > setts['max_pval']):
                currentR = None

            ################# REDUNDANCY
	    if currentR != None and (setts['redundancy_prune'] or setts['redundancy_mark']) and data != None :
                currentRedun = currentR.copy()
                currentRedun.recompute(dataRed)
                if currentRedun.lenU() == 0 :
                    if setts['redundancy_mark']:
                        comment = '# REDUNDANT RULE NO SUPPORT LEFT ' + comment
                        commentSupp = '# REDUNDANT RULE NO SUPPORT LEFT ' + commentSupp
                    else:
                        currentR = None
                elif ( currentRedun.length(0) + currentRedun.length(1) < setts['min_length'] \
                   or currentRedun.N - currentRedun.lenU() < setts['min_suppout'] \
                   or currentRedun.lenI() < setts['min_suppin'] \
                   or currentRedun.acc()  < setts['min_acc'] \
                   or currentRedun.pVal() > setts['max_pval']):
                    if setts['redundancy_mark']:
                        comment = '# REDUNDANT RULE ' + currentRedun.dispCaracteristiquesSimple() + comment
                        commentSupp = '# REDUNDANT RULE ' + commentSupp
                    else:
                        currentR = None
                else:
                    if setts['redundancy_mark']:
                        comment = '# ' + currentRedun.dispCaracteristiquesSimple() + comment
                    dataRed.addRedunRows(currentRedun.suppI())

            ################# WRITING OUT
            if currentR != None and rulesOutFp != None:
                rulesOutFp.write(currentR.dispSimple()+' '+comment+'\n')
            if currentR != None and supportOutFp != None:
                supportOutFp.write(currentR.dispSupp()+' '+commentSupp+'\n')
            if currentR != None and namesOutFp != None:
                namesOutFp.write(currentR.dispSimple(0, names)+' '+comment+'\n')

            ruleNro += 1
    logger.printL(2,'Read all %i rules.'%(ruleNro-1))
 
    if rulesOutFp != None :
        rulesOutFp.close()     
 
    if namesOutFp != None :
        namesOutFp.close()     
 
    if supportOutFp != None :
        supportOutFp.close()     
    logger.printL(1,'THE END')
        
## END of main()

if __name__ == "__main__":
    main()
