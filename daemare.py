# Continuous delivery daemare for ss13.
# Requires: pip install cherrypy
# Requires the following to be on PATH:
#   git
#   dreamdaemon
#   dreammaker

# CHANGE BELOW

PATH_TO_SS13 = "D:\mlpstation13"
ACTIVE_BRANCH = "main2"

# ------------

import subprocess
import traceback

import cherrypy

def log(msg):
    print(msg)

# -------------------- GITHUB STUFF --------------------

def startup():
    #os.chdir(PATH_TO_SS13) # UNCOMMENT THIS IN THE FINAL SCRIPT
    pass

# Check for new content on GitHub and rebase if needed. Returns 1 if rebased.
def check_remote_and_update():
    fetch_process = subprocess.run(["git fetch"], shell=True)

    # Check for merge conflicts
    merge_check = subprocess.run(["git merge --no-commit --no-ff "+ACTIVE_BRANCH],
        shell=True, capture_output=True)
    # Check if nothing needs to be done:
    if "up to date" in merge_check.stdout.decode("utf-8"):
        return 0

    log("Updates available on GitHub.")

    subprocess.run(["git merge --abort"], shell=True, capture_output=True)

    # Exit status is 0 if the merge is possible.
    if merge_check.returncode == 0:
        # Rebase.
        subprocess.run(["git rebase"+ACTIVE_BRANCH], shell=True)
    else:
        raise Exception('Merge conflict present. Manual resolution required.')

    return 1

def update_task():
    try:
        if check_remote_and_update() == 1:
            pass
    except Exception as e:
        traceback.print_exc()
    pass 

# -------------------- INTERNAL SERVER --------------------

# On the BYOND end, world.Export() to the daemare, delivering player count
# Respond if we must shut down the server.

startup()
