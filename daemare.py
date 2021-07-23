# Continuous delivery daemare for mlpstation13.
# Requires: pip install uvicorn
# Requires the following to be on PATH:
#   git
#   DreamDaemon
#   DreamMaker

# CHANGE BELOW

PATH_TO_SS13 = "D:/mlpstation13"
ACTIVE_BRANCH = "main2"
DME_NAME = "vgstation13.dme"
DMB_NAME = "vgstation13.dmb"
DAEMARE_PORT = 6158
DREAM_DAEMON_PORT = 49933
VOTE_PLAYER_THRESHOLD = 3 # If less than or equal to threshold, call vote to restart

# ----------------------------------------

import subprocess
import traceback
import asyncio
import logging
import os
import signal
import sys

# The virgin "select library because of ease of use, documentation, and
# performance" vs. the chad "select library because of the name"
import uvicorn

# -------------------- GLOBALS --------------------

DREAM_DAEMON = None # The dream daemon process
UPDATE_NEEDED = False
EVENT_LOOP = asyncio.get_event_loop()
LOGGER = logging.getLogger("uvicorn.error")

def log(msg):
    LOGGER.info(msg)

# -------------------- GITHUB STUFF --------------------

# Check for new content on GitHub and rebase if needed. Returns True if rebased.
def check_remote_and_update():
    log("Checking for new content on GitHub.")
    fetch_process = subprocess.run(["git","fetch"], shell=True)

    # Check for merge conflicts
    merge_check = subprocess.run([
        "git","merge","--no-commit","--no-ff",ACTIVE_BRANCH],
        shell=True, capture_output=True)
    # Check if nothing needs to be done:
    if "up to date" in merge_check.stdout.decode("utf-8"):
        log("Up to date.")
        return False

    log("Updates available on GitHub. Checking for merge conflicts.")

    abort_process = subprocess.run(["git","merge","--abort"],
        shell=True)
    if not (abort_process.returncode == 0):
        raise Exception("Error occurred while aborting dry merge.")

    # Exit status is 0 if the merge is possible.
    if merge_check.returncode == 0:
        log("No merge conflicts. Starting rebase.")
        rebase_process = subprocess.run(["git","rebase",ACTIVE_BRANCH],
            shell=True)
        if not (rebase_process.returncode == 0):
            raise Exception("Error occurred while rebasing.")
        log("Successfully rebased.")
    else:
        LOGGER.error('Merge error, or merge conflict present. '
            'Manual resolution required.')
        raise Exception('Merge error, or merge conflict present. '
            'Manual resolution required.')

    return True

async def update_task():
    global UPDATE_NEEDED
    try:
            UPDATE_NEEDED |= check_remote_and_update()
    except Exception as e:
        traceback.print_exc()
    pass 

async def update_loop():
    while True:
        await update_task()
        await asyncio.sleep(60)

# -------------------- INTERNAL SERVER --------------------

# On the BYOND end, world.Export() to the daemare, delivering player count
# Respond if we must shut down the server.

# [ Curb Your Enthusiasm ]
def terminate_byond():
    global DREAM_DAEMON
    if (DREAM_DAEMON):
        DREAM_DAEMON.terminate()
        log("Dream Daemon terminated.")
    else:
        log("Dream Daemon is not running.")
    DREAM_DAEMON = None
    pass

def compile_dme():
    log("Beginning compilation.")
    compile_process = subprocess.run(["dm.exe",DME_NAME], shell=True)
    if not (compile_process.returncode == 0):
        raise Exception('Compiler error.')
    pass
    log("Ending compilation.")

def start_dream_daemon():
    global DREAM_DAEMON
    DREAM_DAEMON = subprocess.Popen(["DreamDaemon",DMB_NAME,
        str(DREAM_DAEMON_PORT),"-safe"])
    log("Dream Daemon started.")
    pass

def startup():
    os.chdir(PATH_TO_SS13) 
    start_dream_daemon()
    pass

def restart():
    terminate_byond()
    log("Waiting 20 seconds...")
    await asyncio.sleep(20)
    if (UPDATE_NEEDED):
        try:
            compile_dme()
        except Exception as e:
            traceback.print_exc()
    start_dream_daemon()
    UPDATE_NEEDED = False

async def daemare_server(scope, receive, send):
    global UPDATE_NEEDED
    # Handles GET requests made by BYOND end.
    # If the number of players has dipped below a certain threshold,
    # return a response to tell BYOND to start a restart vote.

    # Query string: players=1
    if not ("query_string" in scope):
        await send({
            'type': 'http.response.start',
            'status': 400,
            'headers': [[b'content-type', b'text/plain'],]
        })
        await send({
            'type' : 'http.response.body',
            'body' : b'input error'
        })
        return

    query_string = scope["query_string"].decode("utf-8")
    if (query_string.startswith("players")):
        qsplit = query_string.split("=")
        if not (len(qsplit) == 2):
            return
        player_count = int(qsplit[1])

        # do we need an update?
        if (player_count <= VOTE_PLAYER_THRESHOLD) and (
            UPDATE_NEEDED == True):
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', b'text/plain'],]
            })
            await send({
                'type' : 'http.response.body',
                'body' : b'restart'
            })
            return

    elif (query_string.startswith("shutdown")):
        log("BYOND shutdown signal received. Terminating DreamDaemon in 10 seconds.")
        await asyncio.sleep(10)
        restart()

    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain'],]
    })
    await send({
        'type' : 'http.response.body',
        'body' : b'ok'
    })

def interrupt_handler():
    if (DREAM_DAEMON):
        terminate_byond()
    EVENT_LOOP.stop()
    sys.exit(0)

def main():
    startup()
    EVENT_LOOP.create_task(update_loop())
    uvicorn.run("daemare:daemare_server", host="127.0.0.1",
            port=DAEMARE_PORT, log_level="info")

signal.signal(signal.SIGINT, interrupt_handler)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        interrupt_handler()

# TODO Actual test with DD.
