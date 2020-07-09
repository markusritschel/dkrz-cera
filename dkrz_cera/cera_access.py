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
                          entry.topic_name_ss,
                          entry.variable_s,
                          entry.frequency_s,
                          entry.entry_name_s,
                          entry.project_acronym_ss,
                          entry.format_acronym_s]
                results_dict[entry.entry_acronym_s.replace(' ', '.')] = entry

            start += rows
            if start > entries_found:
                break

        print("{} results found\n".format(len(results_dict)))

        return results_dict


if __name__=='__main__':
    cera = Cera()
    cs = cera.search(variable_s='tas', model_s='ACCESS1-0', qc_experiment_s='historical')
    print(cs)
