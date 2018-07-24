from fabric.api import *
import os
import re
import utility

@task
def get_latest_release_tag(module_name):
    url = "https://api.github.com/repos/ctsit/'%s'/releases/latest" %module_name
    tag_name = run("curl -s '%s' | grep tag_name | cut -d '\"' -f 4" %(url))

    return tag_name

@task
def enable(module_name, module_version="", pid=""):
    """
    Enables a REDCap module.
    """
    utility.write_remote_my_cnf()
    enable_module = """
        namespace ExternalModules\ExternalModules; require '/var/www/redcap/external_modules/classes/ExternalModules.php';
        #\\ExternalModules\\ExternalModules::initialize();
        \\ExternalModules\\ExternalModules::enableForProject('%s', '%s');
        """ %(module_name, module_version)
    run ('php -r \"%s\"' %enable_module)
    if pid != "":
        enable_module_for_pid = """
            namespace ExternalModules\ExternalModules; require '/var/www/redcap/external_modules/classes/ExternalModules.php';
            \\ExternalModules\\ExternalModules::enableForProject('%s', '%s', %s);
            """ %(module_name, module_version, pid)
        run ('php -r \"%s\"' %enable_module_for_pid)
    utility.delete_remote_my_cnf()


@task
def disable(module_name, pid=""):
    """
    Disables a REDCap module.
    """
    utility.write_remote_my_cnf()
    if pid != "":
        disable_module_for_pid = """
            namespace ExternalModules\ExternalModules; require '/var/www/redcap/external_modules/classes/ExternalModules.php';
            \\ExternalModules\\ExternalModules::setProjectSetting('%s', %s, 'enabled', false);
            """ %(module_name, pid)
        run ('php -r \"%s\"' %disable_module_for_pid)
    else:
        disable_module = """
            namespace ExternalModules\ExternalModules; require '/var/www/redcap/external_modules/classes/ExternalModules.php';
            \\ExternalModules\\ExternalModules::disable('%s');
            """ %module_name
        run ('php -r \"%s\"' %disable_module)
    utility.delete_remote_my_cnf()
