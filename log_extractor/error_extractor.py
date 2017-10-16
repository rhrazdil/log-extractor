#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import user
import subprocess
import click
import constants as const
import yaml
from itertools import izip
#from collections import defaultdict

class ErrorExtractor(object):
    """
    Class to find and parse tracebacks and errors in parsed logs
    """

    def __init__(self, job, build, team):
        self.job = job
        self.build = build
        self.team = team
        self.path = user.home + "/" + "art-tests-logs" + "/" + job + "/" + str(build) + "/" + team + "/"
        

    def _get_tracebacks(self):
        cmd = [
            'grep', '-R', 'Traceback', str(self.path)
        ]
        output = subprocess.check_output(["grep", "-R", "Traceback", self.path])
        return output.split('\n')

    def _get_errors(self):
        cmd = [
            'grep', '-R', 'ERROR', str(self.path)
        ]
        output = subprocess.check_output(cmd)
        output = output.split('\n')
        return [x for x in output if len(x) < 400] # take only reasonably long errors

    def _get_file_paths(self, input_list):
        output = []
        for line in input_list:
            output.append(line.split(":")[0])
        return output
    
    def _get_file_path(self, line):
        return line.split(":")[0]

    def _get_traceback_messages(self, filenames):
        messages = []
        for filename in filenames:
            if filename:
                with open(filename, 'r') as file:
                    messages.append(self._find_traceback_message(file))
        return messages
            
    def _find_traceback_message(self, input):
        in_traceback = 0
        message = ""
        fileline = ""

        for line in input:
            if in_traceback:
                if line.strip().startswith('File'):
                    fileline = line.strip()
                if line.startswith("20"):
                    message = prevline
                    break
            else:    
                if line.startswith("Traceback"):
                    in_traceback = 1
            prevline = line
        return (fileline, message.strip())

    def _remove_special_chars(self, line):
        chars_to_remove = [':', '\n', '\r', "'", '"']
        return line.translate(None, ''.join(chars_to_remove))

    def _strip_filepath(self, filepath):
        return filepath.split(str(self.build)+"/")[1]

    def _create_list_of_tracebacks(self):
        tracebacks = self._get_tracebacks()
        filepaths = self._get_file_paths(tracebacks)
        stripped_filepaths = [self._strip_filepath(filepath) for filepath in filepaths if filepath]
        messages = self._get_traceback_messages(filepaths) 

        data = {files:[] for files in stripped_filepaths}
        for filepath, (last_line, error_message) in izip(stripped_filepaths, messages):
            data[filepath].append(
                {
                    "type":"traceback",
                    "last_line":self._remove_special_chars(last_line),
                    "error_message":self._remove_special_chars(error_message)
                }
            )
        return data

    def _parse_error(self, error_line):
        path = error_line.split(":")[0]
        error_msg = error_line.split("ERROR")[1]
        return path + ":" + "[ERROR] " + error_msg
        
    def _get_error_message(self, error_line):
        return error_line.split(":")[1]
    
    def _add_list_of_errors(self, data):
        errors = self._get_errors()
        parsed_errors = [self._parse_error(error) for error in errors if error]
        #import pdb; pdb.set_trace()
        # remove duplicates
        parsed_errors = list(set(parsed_errors))
        
        for error in parsed_errors:
            filepath = self._strip_filepath(self._get_file_path(error))
            print filepath
            err = {
                "type":"error",
                "error_msg":self._remove_special_chars(self._get_error_message(error))
            }
            if filepath in data:
                data[filepath].append(
                    err
                )
            else:
                data[filepath] = [
                    err
                ]
        return data

@click.command()
@click.option("--job", help="Job name", required=True)
@click.option(
    "--build", help="build number of the job", required=True, type=int
)
@click.option(
    "--team",
    type=click.Choice(const.TEAMS),
    help=(
        "Team logs to collect errors in"
    )
)
def run(job, build, team):
    extractor = ErrorExtractor(job, build, team)
    data = extractor._create_list_of_tracebacks()
    data = extractor._add_list_of_errors(data)
    import pdb; pdb.set_trace()
    
    with open(user.home + '/data.yml', 'w+') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
    #print tracebacks

if __name__ == "__main__":
    run()