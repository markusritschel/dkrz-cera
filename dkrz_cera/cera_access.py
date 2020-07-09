#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   17/06/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import os
import re
import shutil
import pandas as pd
import requests


CERA_URL = "https://cera-www.dkrz.de/WDCC/ui/cerasearch/cerarest/login/"
DOWNLOAD_DIR = os.path.join(os.getenv('HOME'), "work/cmip5-download")


class JSONObject(object):
    def __init__(self, d):
        self.__dict__ = d


class Cera(object):
    def __init__(self):
        self.login_url = CERA_URL
        self.__username = None  # os.getenv('CERA_USER')
        self.__password = None  # os.getenv('CERA_PASS')

    def check_access(self):
        """Validates credentials for accessing CERA database"""
        self.__get_credentials()
        # TODO: checking the actual access is not possible at the moment

    def __get_credentials(self, netrc_file='.netrc'):
        try:
            with open(os.path.join(os.getenv('HOME'), netrc_file)) as f:
                x = re.findall(r"login\s+(\w+)\s+password\s+(\w+)", f.read())
                if len(x)==1:
                    self.__username, self.__password = x[0]
                    print("CERA credentials (user: {}) found in {}".format(self.__username, f.name))
                elif len(x) > 1:
                    print("More than one pair of username and password found. Please check your {}.".format(f.name))
                else:
                    print("Cannot find user credentials in {}".format(f.name))
        except:
            print("Cannot find user credentials. Make sure you have a .netrc file in your home directory "
                  "matching the requirements under \n'Supplying username and password' "
                  "at https://cera-www.dkrz.de/WDCC/ui/cerasearch/info?site=jblob")

    def search(self, **query):
        """Performs a search in the CERA database.

        Parameters
        ----------
        query : dict
            Dictionary containing the search parameters and values to search. Must be one of
                variable_s,
                frequency_s,
                entry_name_s,
                model_s,
                qc_experiment_s,
                format_acronym_s,
                project_acronym_s

        Returns
        -------
        query_obj : CeraQuery
        """
        valid_kwargs = ['variable_s',
                        'frequency_s',
                        'entry_name_s',
                        'model_s',
                        'qc_experiment_s',
                        'format_acronym_s',
                        'project_acronym_s']

        for key, val in query.items():
            if not key in valid_kwargs:
                print(
                    '{} is not a valid search key. Search keys must be one of {}'.format(key, ', '.join(valid_kwargs)))
            if isinstance(val, (list, tuple)):
                query[key] = f"+OR+{key}:".join(val)

        query_str = '+'.join(['{}:{}'.format(k, v) for k, v in query.items()])

        rows = 100
        start = 0
        results_dict = dict()
        while True:
            url2scrape = 'https://cera-www.dkrz.de/WDCC/ui/cerasearch/solr/select?wt=json&facet.mincount=1&' \
                         'q={}&start={}&rows={}'.format(query_str, start, rows)
            r = requests.get(url2scrape)
            json_dict = r.json(object_hook=JSONObject)

            entries_found = json_dict.response.numFound

            if not entries_found:
                print("Zero entries found.")
                return None

            for entry in json_dict.response.docs:
                # write entry_acronym_s into jblob_file
                values = [entry.entry_acronym_s,
                          entry.model_s,
                          entry.qc_experiment_s,
                          # entry.topic_name_ss,
                          entry.variable_s,
                          entry.frequency_s,
                          entry.entry_name_s,
                          entry.project_acronym_ss,
                          entry.format_acronym_s]
                results_dict[entry.entry_acronym_s.replace(' ', '.')] = entry

            start += rows
            if start > entries_found:
                break

        query_obj = CeraQuery(self, results_dict)
        print("{} results found\n".format(len(results_dict)))

        return query_obj


class CeraQuery(object):
    """This returns an instance similar to the intake-esm collection class. It provides a search() method as  well as an
    interfaces to Pandas to view the results as a pd.DataFrame"""

    def __init__(self, parent, results_dict):
        """Takes dictionary with lists as values as well as a reference to the parent object (an instance of Cera)"""
        self.parent = parent
        self.__results_dict = results_dict

    def __str__(self):
        self.__repr__()
        return ''

    def __repr__(self):
        from IPython.display import display
        display(pd.DataFrame(self.df.nunique(), columns=['nunique']))
        return ''

    def to_jblob(self, download_path, file=None, jblob_log_dir='/tmp/'):
        """
        Creates a shell script which downloads assets from CERA by using Jblob.

        Parameters
        ----------
        download_path : str
            Path to the download directory where downloaded assets shall be placed in.
        file : str
            Name of the shell file. If not given, default will fall to `jblob_cera_download.sh`
        jblob_log_dir : str
            Path to a directory where jblob shall create its log files.
        """
        self.parent.check_access()

        if not file:
            file = os.path.expanduser('~/jblob_cera_download.sh')
        else:
            file = os.path.expanduser(file)

        download_path = os.path.expanduser(download_path)
        os.makedirs(download_path, exist_ok=True)

        jblob_path = shutil.which('jblob')
        if jblob_path:
            jblob_install_dir = os.path.dirname(jblob_path)
            jblob_log_dir = os.path.join(jblob_install_dir, 'logs')
            os.makedirs(jblob_log_dir, exist_ok=True)
        else:
            jblob_install_dir = ''
            print(
                "\nCouldn't find jblob. Make sure jblob is installed and change the JBLOB_HOME value in {} accordingly.".format(
                    file))

        jblob_log_file = os.path.join(jblob_log_dir, '$0.log')

        with open(file, 'w') as jblob_file:
            jblob_file.write(
                """#!/bin/bash
                
                # This script requires a local Jblob installation. Jblob is a java
                # based tool for data download from the CERA database available from
                # https://cera-www.dkrz.de/WDCC/ui/cerasearch/info?site=jblob
                
                # If you experience problems when using this script or have questions please
                # contact data@dkrz.de.
                
                # Please prepare your .netrc file to contain the necessary entry for
                # CERA database access, for more information see "Supplying username and
                # password" at https://cera-www.dkrz.de/WDCC/ui/cerasearch/info?site=jblob
                
                # Edit JBLOB_HOME to match your Jblob installation directory if the
                # 'jblob' executable cannot be found in $PATH.
                JBLOB_HOME={0:}
                
                # Locate jblob executable
                if [[ -z $JBLOB_HOME ]]; then
                JBLOB=$(which jblob 2> /dev/null)
                RC=$?
                if [[ $RC -ne 0 ]]; then
                    echo "Cannot locate jblob executable, please edit JBLOB_HOME and re-run this script!"
                    exit 1
                fi
                else
                JBLOB=$JBLOB_HOME/jblob
                fi
                
                # Logfile
                LOG={1:}\n\n""".format(jblob_install_dir, jblob_log_file))

            for entry_name, entry_acronym in zip(self.df['entry_name_s'], self.df['entry_acronym_s']):
                dataset_dir = os.path.join(download_path, *entry_name.split(' '))
                jblob_file.write('mkdir -p {}\n'.format(dataset_dir))
                jblob_file.write('$JBLOB --dataset {} --dir {}\n'.format(entry_acronym, dataset_dir))
                jblob_file.write('echo "{}: $?" >> $LOG\n'.format(entry_acronym))

            jblob_file.write('\necho "' + '-'*40 + '" >> $LOG')
            jblob_file.write('\necho "All done..." >> $LOG')
            jblob_file.write('\necho `/bin/date "+%Y-%m-%d %H:%M:%S "` >> $LOG')
            jblob_file.write('\necho "' + '='*40 + '" >> $LOG\n')

            print('\njblob file "{1:}" successfully created in {0:}\n'.format(*os.path.split(jblob_file.name)))

            print("For downloading data from the CERA database, run the created jblob file in the shell.\n"
                  "Since the download might take a while, it is recommended to start a `screen` environment to run it in the background.\n"
                  "With `screen` one can start a virtual terminal environment. After starting the file in there, you can easily\n"
                  "detach yourself from the environment by pressing `Ctrl+A, D`. You will notice a '[detached]' message in the terminal.\n"
                  "To return to the environment simply type `screen -r` or first list your running screen environments with `screen -list` \n"
                  "if you have multiple running.\n"
                  "Check `man screen` for further information.\n")

    @property
    def df(self):
        """Returns a pd.DataFrame of"""
        df_dict = dict()
        for key, entry in self.__results_dict.items():
            values = [entry.entry_acronym_s,
                      entry.model_s,
                      entry.qc_experiment_s,
                      entry.variable_s,
                      entry.frequency_s,
                      entry.entry_name_s,
                      entry.project_acronym_ss[0],
                      entry.format_acronym_s]
            df_dict[key] = values

        columns = ['entry_acronym_s',
                   'model_s',
                   'qc_experiment_s',
                   'variable_s',
                   'frequency_s',
                   'entry_name_s',
                   'project_acronym_ss',
                   'format_acronym_s']
        df = pd.DataFrame.from_dict(df_dict, orient='index', columns=columns)

        return df


if __name__=='__main__':
    cera = Cera()
    # SEARCH_PATTERN = dict(q="cmip5*historicalNat *mon*tas")
    cs = cera.search(variable_s='tas', model_s='ACCESS1-0', qc_experiment_s='historical')
    # cs.to_jblob('~/work/cmip5_download')
    print(cs)
