# Copyright 2014 0xc0170
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from optparse import OptionParser
import yaml
import logging
import os
from yaml_parser import YAML_parser, _finditem
from os.path import join
import sys
from os.path import basename
from tool import export, build


class ProjectGenerator():

    def run_generator(self, dic, project, tool):
        """ Generates one project. """
        project_list = []
        yaml_files = _finditem(dic, project)
        if yaml_files:
            for yaml_file in yaml_files:
                try:
                    file = open(yaml_file)
                except IOError:
                    raise RuntimeError("Cannot open a file: %s" % yaml_file)
                else:
                    loaded_yaml = yaml.load(file)
                    yaml_parser = YAML_parser()
                    project_list.append(
                        yaml_parser.parse_yaml(loaded_yaml, tool))
                    file.close()
            yaml_parser_final = YAML_parser()
            process_data = yaml_parser_final.parse_yaml_list(project_list)
            yaml_parser_final.set_name(project)
        else:
            raise RuntimeError("Project record is empty")

        logging.info("Generating project: %s" % project)
        export(process_data, tool)

    def process_all_projects(self, dic, tool):
        """ Generates all project. """
        projects = []
        yaml_files = []
        for k, v in dic.items():
            projects.append(k)

        for project in projects:
            self.run_generator(dic, project, tool)
        return projects

    def scrape_dir(self):
        exts = ['s', 'c', 'cpp', 'h', 'inc', 'sct', 'ld']
        found = {x: [] for x in exts}  # lists of found files
        ignore = '.'
        for dirpath, dirnames, files in os.walk(os.getcwd()):
            # Remove directories in ignore
            # directory names must match exactly!
            for idir in ignore:
                if idir in dirnames:
                    dirnames.remove(idir)
            # Loop through the file names for the current step
            for name in files:
                # Split the name by '.' & get the last element
                ext = name.lower().rsplit('.', 1)[-1]
                # Save the full name if ext matches
                if ext in exts:
                    relpath = dirpath.replace(os.getcwd(), "")
                    found[ext].append(os.path.join(relpath, name))
        # The body of our log file
        logbody = ''
        # loop thru results
        for search in found:
            # Concatenate the result from the found dict
            logbody += "<< Results with the extension '%s' >>" % search
            logbody += '\n\n%s\n\n' % '\n'.join(found[search])
        # Write results to the logfile
        source_list_path = join(os.getcwd(), 'tools', 'join')
        if not os.path.exists(source_list_path):
            os.makedirs(source_list_path)
        target_path = join(source_list_path, 'scrape.log')
        logging.debug("Generating: %s" % target_path)
        with open(target_path, 'w') as logfile:
            logfile.write('%s' % logbody)

    def list_projects(self, dic):
        """ Print all defined project. """
        for k, v in dic.items():
            print k

    def run(self, options):
        if not options.file:
            # create a list of all files in the dir that we're interested in
            self.scrape_dir()
            # print help menu
            parser.print_help()
            sys.exit()

        print "Processing projects file."
        project_file = open(join('tools', options.file))
        config = yaml.load(project_file)

        if options.list:
            print "Projects defined in the %s" % options.file
            self.list_projects(config)
            sys.exit()

        projects = []
        if options.project:
            self.run_generator(
                config, options.project, options.tool)  # one project
            projects.append(options.project)
        else:
            # all projects within project.yaml
            projects = self.process_all_projects(config, options.tool)

        project_file.close()
        return projects


class ProjectBuilder():

    def __init__(self):
        self.project_path = "generated_projects"

    def build_project_list(self, options, projects):
        projects_list = []
        for dirpath, dirnames, files in os.walk(self.project_path):
            for d in dirnames:
                for project_name in projects:
                    proj = options.tool + '_' + project_name
                    if project_name in d:
                        projects_list.append(project_name)
                        break
        return projects_list

    def run(self, options, projects):
        project_list = self.build_project_list(options, projects)
        logging.info("Building all defined projects.")
        build(self.project_path, project_list, options.tool)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Should be launched from root/tools but all scripts are referenced to root
    root = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    os.chdir(root)
    logging.debug('This should be the project root: %s', os.getcwd())

    # Parse Options
    parser = OptionParser()
    parser.add_option("-f", "--file", help="YAML projects file")
    parser.add_option("-p", "--project", help="Project to be generated")
    parser.add_option(
        "-t", "--tool", help="Create project files for provided tool (uvision by default)")
    parser.add_option("-l", "--list", action="store_true",
                      help="List projects defined in the project file.")
    parser.add_option(
        "-b", "--build", action="store_true", help="Build defined projects.")

    (options, args) = parser.parse_args()

    if not options.tool:
        options.tool = "uvision"

    # Generate projects
    projects = ProjectGenerator().run(options)

    # Build all exported projects
    if options.build:
        ProjectBuilder().run(options, projects)
