This is one half of the continuous delivery daemare system for /mlp/station13.
The other half are some modifications made to the /mlp/station code itself to
allow communication with this system.

# Usage
Variables in `daemare.py` should be configured to intended values. Instead of
launching Dream Daemon directly, `python daemare.py` should be used to launch
the BYOND server, because the daemare will now be responsible for starting and
stopping the server as needed. No manual changes to tracked files should be
made to the repo containing the .dme and .dmb files, as this could cause merge
conflicts; instead, all changes should be made via a commit to the GitHub
remote.

