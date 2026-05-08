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

__all__ = ["Cera", "CeraQuery"]


class JSONObject:
    """A helper class to access the JSON elements from the CERA request like attributes"""

    def __init__(self, d):
        self.__dict__ = d


class Cera:
    def __init__(self):
        self.login_url = "https://cera-www.dkrz.de/WDCC/ui/cerasearch/login"
        self.__username = None
        self.__password = None

    def check_access(self):
        """Validates credentials for accessing CERA database.

        Credential resolution order: environment variables → .env file → ~/.netrc.

        Raises
        ------
        PermissionError
            If no credentials are found or the server rejects them.
        """
        self.__get_credentials()

        if not self.__username or not self.__password:
            raise PermissionError(
                "No CERA credentials found. Set CERA_USER and CERA_PASSWORD environment variables, "
                "add them to a .env file, or create a ~/.netrc entry. "
                "See https://cera-www.dkrz.de/WDCC/ui/cerasearch/info?site=jblob for details."
            )

        # Attempt a lightweight POST to the login endpoint to verify the credentials.
        # Spring Security redirects to a non-login URL on success and back to login?error on failure.
        try:
            resp = requests.post(
                self.login_url,
                data={"j_username": self.__username, "j_password": self.__password},
                allow_redirects=False,
                timeout=10,
            )
            location = resp.headers.get("Location", "")
            if resp.status_code in (301, 302) and "error" in location:
                raise PermissionError(
                    f"CERA rejected credentials for user '{self.__username}'. "
                    "Please check your username and password."
                )
        except PermissionError:
            raise
        except requests.RequestException as exc:
            # Network issues — warn but don't block usage
            print(
                f"Warning: could not verify CERA credentials online ({exc}). "
                "Proceeding with the stored credentials."
            )

    def __get_credentials(self, netrc_file=".netrc"):
        # Resolution order: env vars → .env file → ~/.netrc

        # 1. Environment variables
        env_user = os.getenv("CERA_USER")
        env_pass = os.getenv("CERA_PASSWORD") or os.getenv("CERA_PASS")
        if env_user and env_pass:
            self.__username, self.__password = env_user, env_pass
            print(
                f"CERA credentials (user: {self.__username}) found in environment variables."
            )
            return

        # 2. .env file (cwd first, then home directory)
        try:
            from dotenv import dotenv_values

            for dotenv_path in [".env", os.path.join(os.path.expanduser("~"), ".env")]:
                env_vars = dotenv_values(dotenv_path)
                dot_user = env_vars.get("CERA_USER")
                dot_pass = env_vars.get("CERA_PASSWORD") or env_vars.get("CERA_PASS")
                if dot_user and dot_pass:
                    self.__username, self.__password = dot_user, dot_pass
                    print(
                        f"CERA credentials (user: {self.__username}) found in {dotenv_path}."
                    )
                    return
        except ImportError:
            pass  # python-dotenv not installed; skip

        # 3. ~/.netrc fallback
        try:
            netrc_path = os.path.join(os.path.expanduser("~"), netrc_file)
            with open(netrc_path) as f:
                x = re.findall(r"login\s+(\w+)\s+password\s+(\w+)", f.read())
                if len(x) == 1:
                    self.__username, self.__password = x[0]
                    print(
                        f"CERA credentials (user: {self.__username}) found in {f.name}."
                    )
                elif len(x) > 1:
                    print(
                        f"More than one pair of username and password found. Please check your {f.name}."
                    )
                else:
                    print(f"Cannot find user credentials in {f.name}.")
        except OSError:
            print(
                "Cannot find CERA credentials. Set CERA_USER and CERA_PASSWORD environment variables, "
                "add them to a .env file, or create a ~/.netrc entry. "
                "See https://cera-www.dkrz.de/WDCC/ui/cerasearch/info?site=jblob for details."
            )

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
        valid_kwargs = [
            "variable_s",
            "frequency_s",
            "entry_name_s",
            "model_s",
            "qc_experiment_s",
            "format_acronym_s",
            "project_acronym_s",
        ]

        for key, val in query.items():
            if key not in valid_kwargs:
                print(
                    f"{key} is not a valid search key. Search keys must be one of {', '.join(valid_kwargs)}"
                )
            if isinstance(val, (list, tuple)):
                query[key] = f"+OR+{key}:".join(val)

        # Example: "model_s:bcc-*+variable_s:tas+qc_experiment_s:historicalGHG+OR+qc_experiment_s:historicalNat"
        query_str = "+".join([f"{k}:{v}" for k, v in query.items()])

        rows = 100
        start = 0
        results_dict = dict()
        while True:
            url2scrape = (
                "https://cera-www.dkrz.de/WDCC/ui/cerasearch/solr/select?wt=json&facet.mincount=1&"
                f"q={query_str}&start={start}&rows={rows}"
            )
            r = requests.get(url2scrape)
            json_dict = r.json(object_hook=JSONObject)

            entries_found = json_dict.response.numFound

            if not entries_found:
                print("Zero entries found.")
                return None

            for entry in json_dict.response.docs:
                # write entry_acronym_s into jblob_file
                values = [
                    entry.entry_acronym_s,
                    entry.model_s,
                    entry.qc_experiment_s,
                    # entry.topic_name_ss,
                    entry.variable_s,
                    entry.frequency_s,
                    entry.entry_name_s,
                    entry.project_acronym_ss,
                    entry.format_acronym_s,
                ]
                results_dict[entry.entry_acronym_s.replace(" ", ".")] = entry

            start += rows
            if start > entries_found:
                break

        query_obj = CeraQuery(self, results_dict)
        print(f"{len(results_dict)} results found\n")

        return query_obj


class CeraQuery:
    """This returns an instance similar to the intake-esm collection class. It provides a search() method as  well as an
    interfaces to Pandas to view the results as a pd.DataFrame
    """

    def __init__(self, parent, results_dict):
        """Takes dictionary with lists as values as well as a reference to the parent object (an instance of Cera)"""
        self.parent = parent
        self.__results_dict = results_dict

    def __str__(self):
        self.__repr__()
        return ""

    def __repr__(self):
        from IPython.display import display

        display(pd.DataFrame(self.df.nunique(), columns=["nunique"]))
        return ""

    def to_jblob(self, download_path, file=None, jblob_log_dir="/tmp/"):
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
            file = os.path.expanduser("~/jblob_cera_download.sh")
        else:
            file = os.path.expanduser(file)

        download_path = os.path.expanduser(download_path)
        os.makedirs(download_path, exist_ok=True)

        jblob_path = shutil.which("jblob")
        if jblob_path:
            jblob_install_dir = os.path.dirname(jblob_path)
            jblob_log_dir = os.path.join(jblob_install_dir, "logs")
            os.makedirs(jblob_log_dir, exist_ok=True)
        else:
            jblob_install_dir = ""
            print(
                f"\nCouldn't find jblob. Make sure jblob is installed and change the JBLOB_HOME value in {file} accordingly."
            )

        jblob_log_file = os.path.join(jblob_log_dir, "$0.log")

        with open(file, "w") as jblob_file:
            jblob_file.write(
                f"""#!/bin/bash
                
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
                JBLOB_HOME={jblob_install_dir}
                
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
                LOG={jblob_log_file}\n\n"""
            )

            for entry_name, entry_acronym in zip(
                self.df["entry_name_s"], self.df["entry_acronym_s"]
            ):
                dataset_dir = os.path.join(download_path, *entry_name.split(" "))
                jblob_file.write(f"mkdir -p {dataset_dir}\n")
                jblob_file.write(
                    f"$JBLOB --dataset {entry_acronym} --dir {dataset_dir}\n"
                )
                jblob_file.write(f'echo "{entry_acronym}: $?" >> $LOG\n')

            jblob_file.write('\necho "' + "-" * 40 + '" >> $LOG')
            jblob_file.write('\necho "All done..." >> $LOG')
            jblob_file.write('\necho `/bin/date "+%Y-%m-%d %H:%M:%S "` >> $LOG')
            jblob_file.write('\necho "' + "=" * 40 + '" >> $LOG\n')

            print(
                '\njblob file "{1:}" successfully created in {0:}\n'.format(
                    *os.path.split(jblob_file.name)
                )
            )

            print(
                "For downloading data from the CERA database, run the created jblob file in the shell.\n"
                "Since the download might take a while, it is recommended to start a `screen` environment to run it in the background.\n"
                "With `screen` one can start a virtual terminal environment. After starting the file in there, you can easily\n"
                "detach yourself from the environment by pressing `Ctrl+A, D`. You will notice a '[detached]' message in the terminal.\n"
                "To return to the environment simply type `screen -r` or first list your running screen environments with `screen -list` \n"
                "if you have multiple running.\n"
                "Check `man screen` for further information.\n"
            )

    @property
    def df(self):
        """Returns a pd.DataFrame of"""
        df_dict = dict()
        for key, entry in self.__results_dict.items():
            values = [
                entry.entry_acronym_s,
                entry.model_s,
                entry.qc_experiment_s,
                entry.variable_s,
                entry.frequency_s,
                entry.entry_name_s,
                entry.project_acronym_ss[0],
                entry.format_acronym_s,
            ]
            df_dict[key] = values

        columns = [
            "entry_acronym_s",
            "model_s",
            "qc_experiment_s",
            "variable_s",
            "frequency_s",
            "entry_name_s",
            "project_acronym_ss",
            "format_acronym_s",
        ]
        df = pd.DataFrame.from_dict(df_dict, orient="index", columns=columns)

        return df


if __name__ == "__main__":
    cera = Cera()
    # SEARCH_PATTERN = dict(q="cmip5*historicalNat *mon*tas")
    cs = cera.search(
        variable_s="tas", model_s="ACCESS1-0", qc_experiment_s="historical"
    )
    # cs.to_jblob('~/work/cmip5_download')
    print(cs)
