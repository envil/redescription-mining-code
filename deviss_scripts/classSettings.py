import re, pdb
import ConfigParser

class Settings:
    
    setts_help = {'log': {'verbosity' : '    INT level of verbosity, 0: silent, 10:verbose',
                          'logfile':'    (-|+|FILENAME) logfile, -:stdout, +:result_rep/outbase.xxxlog, FILENAME'},
                  'files': {'data_rep':  ' >< STRING data repertory',
                            'data_l': ' >< STRING left data filename',
                            'ext_l':' >< STRING left data extension',
                            'data_r': ' >< STRING right data filename',
                            'ext_r':' >< STRING right data extension',
                            'result_rep': ' >< STRING results repertory',
                            'out_base': '    STRING results base filename' ,
                            'ext_queries': '    STRING results queries extension',
                            'ext_support': '    STRING results supports extension'},
                  'mine': { 'nb_variables': ' >< INT number of variables per query',
                            'min_length': '    INT minimum length of redescription, i.e., sum of the lengths of the queries',
                            'contribution': '    INT minimum contribution, i.e., nb of entities contributed by an appended variable',	                
                            'min_suppin': ' >< (INT|FLOAT) minimum support, i.e., nb of entities for which both queries hold, if 0<=float<1 interpreted as ratio of total nb of entities',
                            'min_suppout': ' >< (INT|FLOAT) minimum uncovered, i.e., nb of entities for which neither of the queries hold, if 0<=float<1 interpreted as ratio of total nb of entities',
                            'min_acc': ' >< FLOAT minimum accuracy, i.e., Jaccard coefficient',
                            'max_pval': ' >< FLOAT maximum p-value',
                            'method_pval' : '    (marg|supp|over) method to compute the p-value',
                            'nb_pairs': ' >< INT number of initial pairs, 0=unlimited',
                            'method_pairs': '    (overall|alternate) method to order the initial pairs',
                            'div_l': '    INT only pairs with left variable id  multiples of this number will be expanded, quick exploration of the data',
                            'div_r': '    INT only pairs with right variable id multiple of this number will be expanded, quick exploration of the data',
                            'min_score': '    FLOAT minimum score for a pair to be expanded',
                            'draft_capacity': '    INT draft capacity, number of different redescriptions retained at each step',
                            'draft_output': '    INT draft output, number of different redescriptions finally output from the draft',
                            'min_improvement': '    FLOAT minimum score improvement over parent redescription for an extension to be added to the draft',
                            'coeff_impacc': '    FLOAT coefficient in the score for the accuracy improvement',
                            'coeff_relimpacc': '    FLOAT coefficient in the score for the relative accuracy improvement',
                            'coeff_pvquery': '    FLOAT negative value: coefficient in the score for the querie\'s p-value, positive value: acceptable p-value threshold',
                            'coeff_pvred': '    FLOAT negative value: coefficient in the score for the redescription\'s p-value, positive value: acceptable p-value threshold',
                            'amnesic': '    BOOL do not record redescriptions already explored',
                            'track_histo': '    BOOL track the history of expansion for each redescription',
                            'max_side_identical': '    INT maximum number of redescription sharing an identical query',
                            'forbid_queries_l': ' >< (nots|ands|ors|andnots|ornots and comma or _ separated combinations thereof) >< forbidden types of queries on the left-hand side',
                            'forbid_queries_r': ' >< (nots|ands|ors|andnots|ornots and comma or _ separated combinations thereof) >< forbidden types of queries on the right-hand side',
                            'max_ovp': '    FLOAT maximum overlap on same variable for identical initial pairs',
                            'max_accrp':'    FLOAT ratio of decrease for acceptable initial pairs',},
                  'post': { 'ext_names': '    STRING results labelled queries extension',
                            'ext_print': '    STRING results queries formatted as LaTeX table extension',
                            'labels_l': ' >< STRING left data labels extension, leave empty if there is no labels file',
                            'labels_r': ' >< STRING left data labels extension, leave empty if there is no labels file',
                            'min_length': '    INT minimum length of redescription, i.e., sum of the lengths of the queries',
                            'min_suppin': '    (INT|FLOAT) minimum support, i.e., nb of entities for which both queries hold, if 0<=float<1 interpreted as ratio of total nb of entities',
                            'min_suppout': '    (INT|FLOAT) minimum uncovered, i.e., nb of entities for which neither of the queries hold, if 0<=float<1 interpreted as ratio of total nb of entities',
                            'min_acc': '    FLOAT minimum accuracy, i.e., Jaccard coefficient',
                            'max_pval': '    FLOAT maximum p-value',
                            'method_pval' : '    (marg|supp|over) method to compute the p-value',
                            'sanity_check': '    BOOL sanity check',
                            'recompute': '    BOOL recompute the redescriptions, needs data files',
                            'filtrate': ' >< BOOL filtrate the redescriptions based on given criteria',
                            'redundancy_mark': ' >< BOOL mark redundant redescriptions',
                            'redundancy_prune': '    BOOL prune redundant redescriptions',
                            'duplicate_mark': ' >< INT mark duplicate redescriptions, maximum number of redescription sharing an identical query',
                            'duplicate_prune': '    INT prune duplicate redescriptions, maximum number of redescription sharing an identical query'}
                  }

    programs_specifics={}
    default_setts={}
    # Default settings for mine
    ###########################
    programs_specifics['mine'] = {
        'help_mess':'###  ReReMi\n### ========\n'+ \
        '### Real-Valued Redescription Mining\n'+ \
        '### usage: %(script_name)s [config_file] [place_holders]\n###\n'+ \
        '### Default settings:\n'+ \
        '### -----------------\n'+ \
        '### Below is the list of all possible parameters and their default values,\n'+ \
        '### this can be copied to a file, tuned and fed to the algorithm.\n'+ \
        '### Most parameters do not need to be tuned, the most important parameters are marked with ><.\n'+ \
        '### (parameter_name=default_value  ## parameter description)\n###\n'+ \
        '### -----8<------------------8<------------------8<------------------8<----\n'+ \
        '%(default_parameters)s \n'+ \
        '### ----->8------------------>8------------------>8------------------>8----\n###\n'+ \
        '### Place holders:\n'+ \
        '### --------------\n'+ \
        '### PH1_name=PH1_value,PH2_name=PH2_value ...\n'+ \
        '### Place holders are special parameters that are substituted before execution.\n'+ \
        '### This can be used to perfom series of runs using the same settings except for one or two parameters.\n'+ \
        '### For example, write in the configuration file\n'+ \
        '### out_base=results_::MSIN::-::MSOUT::\n### min_suppin=::MSIN::\n### min_suppout=::MSOUT::\n'+ \
        '### and run'+ \
        '### "%(script_name)s config_file ::MSIN::=100,::MSOUT::=500"\n'+ \
        '### "%(script_name)s config_file ::MSIN::=200,::MSOUT::=400"\n'+ \
        '### "%(script_name)s config_file ::MSIN::=100,::MSOUT::=500" etc.\n'+ \
        '### to test different supports with all other parameters remaining equal and save\n'+ \
        '### the results in files with corresponding names (results_100-50.query, results_200-400.query, etc.).\n###',

        'sections_read':['log', 'files', 'mine'],
        'substitutions':{'::SERIES::':'out', '::HOME::':'~/' },
        'additional_methods':['setQueries', 'setLogfile'],
        'log_ext':'.minelog'
        }
    default_setts['mine']= {'verbosity': 1, 'logfile': '-',
                              'data_rep': './',
                              'data_l': 'left', 'ext_l':'.bdat',
                              'data_r': 'right', 'ext_r':'.bdat',
                              'result_rep': './', 'out_base': '::SERIES::', 'ext_queries': '.queries', 'ext_support': '.supports',
                              'nb_variables': 4, 'min_length': 2, 'contribution': 3,	                
                              'min_suppin': 0.1, 'min_suppout': 0.7, 'min_acc': 0.0, 'max_pval': 0.05, 'method_pval' : 'Supp',
                              'nb_pairs': 0, 'method_pairs': 'overall', 'div_l': 1, 'div_r': 1, 'min_score': 0.01,
                              'draft_capacity': 4, 'draft_output': 1, 'min_improvement': 0.0,
                              'coeff_impacc': 1.0, 'coeff_relimpacc': 0.0, 'coeff_pvquery': 1.0, 'coeff_pvred': 1.0,
                              'amnesic': False, 'track_histo': False, 'max_side_identical': 2,
                              'forbid_queries_l': '', 'forbid_queries_r': '',
                              'max_ovp': 0.0, 'max_accrp': 0.75
                            }
    
    # Default settings for postprocessing
    #####################################
    programs_specifics['post'] = {
        'help_mess':'###  ReReMi Post-processing tool\n### =============================\n'+ \
        '### Real-Valued Redescription Mining post-processing: label, filtrate, recompute support, etc.\n'+ \
        '### usage: %(script_name)s [config_file] [place_holders]\n###\n'+ \
        '### Default settings:\n'+ \
        '### -----------------\n'+ \
        '### Below is the list of all possible parameters and their default values,\n'+ \
        '### this can be copied to a file, tuned and fed to the algorithm.\n'+ \
        '### Most parameters do not need to be tuned, the most important parameters are marked with ><.\n'+ \
        '### (parameter_name=default_value  ## parameter description)\n###\n'+ \
        '### -----8<------------------8<------------------8<------------------8<----\n'+ \
        '%(default_parameters)s \n'+ \
        '### ----->8------------------>8------------------>8------------------>8----\n###\n'+ \
        '### Place holders:\n'+ \
        '### --------------\n'+ \
        '### PH1_name=PH1_value,PH2_name=PH2_value ...\n'+ \
        '### Place holders are special parameters that are substituted before execution.\n'+ \
        '### This can be used to perfom series of runs using the same settings except for one or two parameters.\n'+ \
        '### For example, write in the configuration file\n'+ \
        '### out_base=results_::MSIN::-::MSOUT::\n### min_suppin=::MSIN::\n### min_suppout=::MSOUT::\n'+ \
        '### and run'+ \
        '### "%(script_name)s config_file ::MSIN::=100,::MSOUT::=500"\n'+ \
        '### "%(script_name)s config_file ::MSIN::=200,::MSOUT::=400"\n'+ \
        '### "%(script_name)s config_file ::MSIN::=100,::MSOUT::=500" etc.\n'+ \
        '### to test different supports with all other parameters remaining equal and save\n'+ \
        '### the results in files with corresponding names (results_100-50.query, results_200-400.query, etc.).\n###',

        'sections_read':['log', 'files', 'post'],
        'substitutions':{'::SERIES::':'out', '::HOME::':'~/' },
        'log_ext':'.postlog',
        'additional_methods':['setLogfile', 'defaultUnused']
        }
    default_setts['post']= { 'verbosity': 1, 'logfile': '-',
                             'data_rep': './',
                             'data_l': 'left', 'ext_l':'.datbool', 'labels_l': '.names',
                             'data_r': 'right', 'ext_r':'.datbool', 'labels_r': '.names',
                             'result_rep': './', 'out_base': '::SERIES::' , 'ext_queries': '.queries', 'ext_print': '', 'ext_support': '.supports', 'ext_names': '.names',
                             'min_length':2, 'min_suppin': 0.1, 'min_suppout': 0.7, 'min_acc': 0.0, 'max_pval': 0.05, 'method_pval' : 'marg',
                             'sanity_check': False,'recompute': False, 'filtrate': False, 'redundancy_mark': False, 'redundancy_prune': False,
                             'duplicate_mark': 0, 'duplicate_prune': 0
                             }

    def __init__(self,  program, arguments):
        if not Settings.programs_specifics.has_key(program):
            raise Error('Error in getting the parameters, program unknown!')

        self.specifics=Settings.programs_specifics[program]
        self.param = Settings.default_setts[program]
        self.script_name=arguments[0]
        if len(arguments) > 2:
            self.substitutions_str = arguments[2]
        else:
            self.substitutions_str = ''
        if len(arguments) > 1:
            self.conf_filename = arguments[1]
        else:
            self.conf_filename = '-h'

    def getParams(self):
        # Display help
        if self.conf_filename in ( '-h', '--help'):
            return 0
        else:
            self.subsPlaceHolders()
            self.parseParams()
            for addiMethod in self.specifics['additional_methods']:
                eval('self.'+addiMethod+'()')
            return len(self.param)

    def dispHelp(self):
        return self.specifics['help_mess'] % {'script_name': self.script_name, 'default_parameters': self.dispParams()}
        
    def dispParams(self):
        ## Display all parameters for the program
        str_par = ''
        for section in self.specifics['sections_read']:
            str_par += ( '\n[%s]\n' % section)
            for (item,help_str) in Settings.setts_help[section].iteritems():
                str_par += ( '%-35s##%s\n' % (item +'='+ str(self.param[item]), help_str))
        return str_par

    def subsPlaceHolders(self):
        ## Substituting series place holder
        if len(self.substitutions_str) > 0:
            parts = self.substitutions_str.split(',')
            for substi in parts:
                tmp = substi.split('=')
                if len(tmp) == 2:
                    self.specifics['substitutions'][tmp[0]] = tmp[1]
                else:
                    self.specifics['substitutions']['::SERIES::']=tmp[0]


    def parseParams(self):
        ## Parse parameters
        for (place_holder, token) in self.specifics['substitutions'].iteritems():
            for opti in self.param.keys():
                if type(self.param[opti])== str :
                    self.param[opti] = self.param[opti].replace(place_holder, token)
        
        config = ConfigParser.ConfigParser() 
        config.read(self.conf_filename)
        for sect in self.specifics['sections_read']: 
            if config.has_section(sect):
                for (opti,val) in config.items(sect):
                    if self.param.has_key(opti):
                        try:
                            valclean = val.split('#')[0].strip()
                            for (place_holder, token) in self.specifics['substitutions'].iteritems():
                                valclean = valclean.replace(place_holder, token)    

                            self.param[opti] = type(self.param[opti])(valclean)
                        except ValueError:
                            raise Exception('Unexpected value for %s %s, default is %s.' %(opti, val, self.param[opti]))


    def setQueries(self):
        self.param['query_types'] = {}
        self.param['query_types'][0] = {False: set([False, True]), True: set([False, True])}
        if re.search('(^|_|,)andnots($|_|,)', self.param['forbid_queries_l']): self.param['query_types'][0][False].remove(True)
        if re.search('(^|_|,)ornots($|_|,)', self.param['forbid_queries_l']): self.param['query_types'][0][True].remove(True)
        if re.search('(^|_|,)nots($|_|,)', self.param['forbid_queries_l']): self.param['query_types'][0][False].remove(True); self.param['query_types'][0][True].remove(True)
        if re.search('(^|_|,)ands($|_|,)', self.param['forbid_queries_l']): self.param['query_types'][0][False]=set()
        if re.search('(^|_|,)ors($|_|,)', self.param['forbid_queries_l']): self.param['query_types'][0][True]=set()

        self.param['query_types'][1] = {False: set([False, True]), True: set([False, True])}
        if re.search('(^|_|,)andnots($|_|,)', self.param['forbid_queries_r']): self.param['query_types'][1][False].remove(True)
        if re.search('(^|_|,)ornots($|_|,)', self.param['forbid_queries_r']): self.param['query_types'][1][True].remove(True)
        if re.search('(^|_|,)nots($|_|,)', self.param['forbid_queries_r']): self.param['query_types'][1][False].remove(True); self.param['query_types'][1][True].remove(True)
        if re.search('(^|_|,)ands($|_|,)', self.param['forbid_queries_r']): self.param['query_types'][1][False]=set()
        if re.search('(^|_|,)ors($|_|,)', self.param['forbid_queries_r']): self.param['query_types'][1][True]=set()

    def setLogfile(self):
        if self.param['logfile'] == '+': self.param['logfile'] = self.param['result_rep']+self.param['out_base']+self.specifics['log_ext']


    def defaultUnused(self):
        self.param['query_types'] = {False: set([False, True]), True: set([False, True])}
        self.param['min_score'] = 0
        self.param['contribution'] = 0
            
