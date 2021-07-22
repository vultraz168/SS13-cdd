import subprocess

# CHANGE BELOW

PATH_TO_SS13 = "D:\mlpstation13"
#BRANCH = "Bleeding-Edge"
BRANCH = "main"

# ------------

def init():
    #os.chdir(PATH_TO_SS13) # UNCOMMENT THIS IN THE FINAL SCRIPT

# Check for new content on GitHub
def get_remote():
    subprocess.run(["git fetch"], shell=True)

    # Check for merge conflicts
    merge_check = subprocess.run(["git merge --no-commit --no-ff "+BRANCH], shell=True)
    subprocess.run(["git merge --abort"], shell=True)

    # Exit status is 0 if the merge is possible.
    # Rebase - don't use a merge commit.
    if (merge_check.returncode == 0):
        subprocess.run(["git rebase main"], shell=True)

    # check for divergence

    #print(up.stdout)
    pass

get_remote()
