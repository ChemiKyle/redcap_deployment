from fabric.api import *
import os
import re
import utility
import urllib.request

def module_exists(module_name, repo_base="ctsit"):
    url = "https://api.github.com/repos/%s/%s" %(repo_base, module_name)
    with hide('output', 'running', 'warnings'):
        output = run("curl -s %s | grep message | cut -d '\"' -f 4" %(url)) != 'Not Found'
    if(not output): print("The module %s/%s doesn't exist." %(repo_base, module_name))
    else: print("The module %s/%s does exist." %(repo_base, module_name))
    return output

def get_latest_release_tag(module_name, repo_base="ctsit"):
    """
    Defaults to latest release
    """
    tag = ""

    url = "https://api.github.com/repos/%s/%s/tags" %(repo_base, module_name)

    with hide('output', 'running', 'warnings'):
        tags = run("curl -s %s | grep name | cut -d '\"' -f 4 | sort --version-sort -r" %(url))
        tag = tags.split('\n')[0]
        tag = tag.rstrip()

    if(tag == ""):
        print("The module %s/%s hasn't been tagged." %(repo_base, module_name))
    else:
        print("The tag for module %s/%s is %s." %(repo_base, module_name, tag))
    return tag

def get_latest_release_zip(module_name, repo_base="ctsit"):
    if(module_exists(module_name, repo_base)):
        tag = get_latest_release_tag(module_name, repo_base)
        if(tag == ""): # The module hasn't been released. Aborting.
            abort("The module %s/%s has not been released yet." %(repo_base, module_name))

        url = "https://github.com/%s/%s/archive/%s.zip" %(repo_base, module_name, tag)
        file_name = "%s_v%s" %(module_name, re.sub('[^\d^\.]', '', tag)) # regex replace anything in tag except x.y.z
        urllib.request.urlretrieve(url, file_name + '.zip')

        return file_name
    else:
        abort("The module %s/%s doesn't exist." %(repo_base, module_name))

@task
def deploy_module(module_input, module_version="", upload_module_version = ""):
    """
    Deploy module to the specified host without enabling it.
    If no module_version is provided the latest version is deployed.
    """
    module_input = module_input.split('github.com/')[-1]
    module_array = module_input.split('/')
    if (len(module_array) == 2):
        repo_base, module_name = module_array
    else:
        module_name = module_input
        repo_base = "ctsit"

    file_name = get_latest_release_zip(module_name, repo_base)

    with settings(user=env.deploy_user):
    # Make a temp folder to upload the tar to
        temp_dir = run('mktemp -d')
        zip_file = file_name + '.zip'
        put(zip_file, temp_dir)
        run('unzip %s/%s -d %s' % (temp_dir, zip_file, temp_dir))
        run('rm %s/*.zip' %(temp_dir))
        run("mv %s/* %s/%s" %(temp_dir, temp_dir, file_name))
        run('rsync -rc %s/%s %s/modules' % (temp_dir, file_name, env.live_project_full_path))
        # Remove the temp directories
        run('rm -rf %s' % (temp_dir))

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
