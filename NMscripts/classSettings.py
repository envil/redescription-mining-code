import re
import ConfigParser

class Settings:
    
    setts_help = {'log': {'verbosity' : 'INT level of verbosity, 0: silent, 10:verbose',
                          'logfile':'(-|+|FILENAME) logfile, -:stdout, +:result_rep/outbase.runlog, FILENAME'},
                  'files': {'data_rep': 'STRING data repertory',
                            'data_l': 'STRING left data filename',
                            'ext_l':'STRING left data extension',
                            'data_r': 'STRING right data filename',
                            'ext_r':'STRING right data extension',
                            'result_rep': 'STRING results repertory',
                            'out_base': 'STRING results base filename' ,
                            'ext_rules': 'STRING results rule extension',
                            'ext_support': 'STRING results support extension'},
                  'mine': { 'nb_variables': 'INT number of variables per query',
                            'min_length': 'INT minimum length of redescription, i.e., sum of the lengths of the queries',
                            'contribution': 'INT minimum contribution, i.e., nb of entities contributed by an appended variable',	                
                            'min_suppin': '(INT|FLOAT) minimum support, i.e., nb of entities for which both queries hold, if 0<=float<1 interpreted as ratio of total nb of entities',
                            'min_suppout': '(INT|FLOAT) minimum uncovered, i.e., nb of entities for which neither of the queries hold, if 0<=float<1 interpreted as ratio of total nb of entities',
                            'min_acc': 'FLOAT minimum accuracy, i.e., Jaccard coefficient',
                            'max_pval': 'FLOAT maximum p-value',
                            'method_pval' : '(marg|supp|over) method to compute the p-value',
                            'nb_pairs': 'INT number of initial pairs, 0=unlimited',
                            'method_pairs': '(overall|alternate) method to order the initial pairs',
                            'div_l': 'INT only pairs with left variable id  multiples of this number will be expanded, quick exploration of the data',
                            'div_r': 'INT only pairs with right variable id multiple of this number will be expanded, quick exploration of the data',
                            'min_score': 'FLOAT minimum score for a pair to be expanded',
                            'draft_capacity': 'INT draft capacity, number of different redescriptions retained at each step',
                            'draft_output': 'INT draft output, number of different redescriptions finally output from the draft',
                            'min_improvement': 'FLOAT minimum score improvement over parent redescription for an extension to be added to the draft',
                            'coeff_impacc': 'FLOAT coefficient in the score for the accuracy improvement',
                            'coeff_relimpacc': 'FLOAT coefficient in the score for the relative accuracy improvement',
                            'coeff_pvrule': 'FLOAT negative value: coefficient in the score for the querie\'s p-value, positive value: acceptable p-value threshold',
                            'coeff_pvred': 'FLOAT negative value: coefficient in the score for the redescription\'s p-value, positive value: acceptable p-value threshold',
                            'amnesic': 'BOOL do not record redescriptions already explored',
                            'max_side_identical': 'INT maximum number of redescription sharing an identical query',
                            'forbid_rules': '(nots|ands|ors|andnots|ornots and comma or _ separated combinations thereof) forbidden types of queries'},
                  'post': { 'min_length': 'length',
                            'min_suppin': 'mini supp',
                            'min_suppout': 'mini supp out',
                            'min_acc': 'mini acc',
                            'max_pval': 'mac p-val',
                            'method_pval' : 'Supp',
                            'min_length': 'length',
                            'min_suppin': 'minsupp in',
                            'min_suppout': 'minsupp out',
                            'min_acc': 'min acc',
                            'max_pval': 'max pval',
                            'method_pval' : 'marg',
                            'sanity_check': 'sanity check',
                            'recompute': 'recompute',
                            'filtrate': 'filtrate',
                            'redundancy_mark': 'redundancy',
                            'redundancy_prune': 'redundancy prune',
                            'duplicate_mark': 'duplicate',
                            'duplicate_prune': 'duplicate prune'}
                  }

    programs_specifics={}
    default_setts={}
    # Default settings for mine
    ###########################
    programs_specifics['mine'] = {
        'help_mess':'###  ReReMi\n### ========\n'+ \
        '### Real-Valued Redescription Mining\n'+ \
        '### To run: %(script_name)s config_file [place_holders]\n\n'+ \
        '### place_holders:\n'+ \
        '### (parameter_name=default_value  ## parameter description)'
        '### Default settings:\n'+ \
        '### -----------------\n'+ \
        '### Below is a list of all possible parameters and their default values, this can be copied to a file, tuned and fed to the algorithm.'+ \
        '### The description of minor parameters which  \n'+ \
        '### (parameter_name=default_value  ## parameter description)',

        'sections_read':['log', 'files', 'mine'],
        'substitutions':{'::SERIES::':'out', '::HOME::':'~/' },
        'additional_methods':['setRules', 'setLogfile'],
        'log_ext':'.minelog'
        }
    default_setts['mine']= {'verbosity': 1, 'logfile': '-',
                              'data_rep': './',
                              'data_l': 'left', 'ext_l':'.bdat',
                              'data_r': 'right', 'ext_r':'.bdat',
                              'result_rep': './', 'out_base': '::SERIES::' , 'ext_rules': '.rul', 'ext_support': '.supp',
                              'nb_variables': 4, 'min_length': 2, 'contribution': 3,	                
                              'min_suppin': 0.1, 'min_suppout': 0.7, 'min_acc': 0.0, 'max_pval': 0.05, 'method_pval' : 'Supp',
                              'nb_pairs': 0, 'method_pairs': 'overall', 'div_l': 1, 'div_r': 1, 'min_score': 0.01,
                              'draft_capacity': 4, 'draft_output': 1, 'min_improvement': 0.0,
                              'coeff_impacc': 1.0, 'coeff_relimpacc': 0.0, 'coeff_pvrule': 1.0, 'coeff_pvred': 1.0,
                              'amnesic': False, 'max_side_identical': 2, 'forbid_rules': ''
                          }
    
    # Default settings for postprocessing
    #####################################
    programs_specifics['post'] = {
        'help_mess':'###  ReReMi\n### ========\n'+ \
        '### Real-Valued Redescription Mining\n'+ \
        '### To run:  %(script_name)s config_file [place_holders]\n\n'+ \
        '### place_holders:\n'+ \
        '### (parameter_name=default_value  ## parameter description)'
        '### Default settings:\n'+ \
        '### -----------------\n'+ \
        '### Below is a list of all possible parameters and their default values, this can be copied to a file, tuned and fed to the algorithm.'+ \
        '### The description of minor parameters which  \n'+ \
        '### (parameter_name=default_value  ## parameter description)',

        'sections_read':['log', 'files', 'post'],
        'substitutions':{'::SERIES::':'out', '::HOME::':'~/' },
        'log_ext':'.postlog',
        'additional_methods':['setRules', 'setLogfile']
        }
    default_setts['post']= { 'verbosity': 1, 'logfile': '-',
                             'data_rep': './',
                             'data_l': 'left', 'ext_l':'.datbool', 'labels_l': '.names',
                             'data_r': 'right', 'ext_r':'.datbool', 'labels_r': '.names',
                             'result_rep': './', 'out_base': '::SERIES::' , 'ext_rules': '.rul', 'ext_print': '', 'ext_support': '.supp', 'ext_names': '.names',
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
        return (self.specifics['help_mess'] % {'script_name': self.script_name} )+'\n'+ self.dispParams()
        
    def dispParams(self):
        ## Display all parameters for the program
        str_par = ''
        for section in self.specifics['sections_read']:
            str_par += ( '\n[%s]\n' % section)
            for (item,help_str) in Settings.setts_help[section].iteritems():
                str_par += ( '%-35s## %s\n' % (item +'='+ str(self.param[item]), help_str))
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


    def setRules(self):
        self.param['rule_types'] = {False: set([False, True]), True: set([False, True])}
        if re.search('(^|_|,)andnots($|_|,)', self.param['forbid_rules']): self.param['rule_types'][False].remove(True)
        if re.search('(^|_|,)ornots($|_|,)', self.param['forbid_rules']): self.param['rule_types'][True].remove(True)
        if re.search('(^|_|,)nots($|_|,)', self.param['forbid_rules']): self.param['rule_types'][False].remove(True); self.param['rule_types'][True].remove(True)
        if re.search('(^|_|,)ands($|_|,)', self.param['forbid_rules']): self.param['rule_types'][False]=set()
        if re.search('(^|_|,)ors($|_|,)', self.param['forbid_rules']): self.param['rule_types'][True]=set()

    def setLogfile(self):
        if self.param['logfile'] == '+': self.param['logfile'] = self.param['result_rep']+self.param['out_base']+self.specifics['log_ext']
