# Debugging Cross Compiled Executables

In order to debug cross compiled excutables effectively on Windows, you need to
convert the GDB debugging data embedded in non-stripped executables using a
tool called ``cv2pdb.exe``.  Building this tool is difficult.  The easiest way
to get a function build of the tool is to install *Visual D*.  Then you can find
to at ``C:\Program Files (x86)\VisualD\cv2pdb\cv2pdb.exe``.

To extract a ``.pdb`` file from a cross compiled ``.exe`` run the following:

    cv2pdb.exe -n <target.exe>

This should produce ``target.pdb`` in the same directory as the original
executable.

In order to use the ``.pdb`` file you also need to isntall ``windbg.exe`` from
*Debugging Tools for Windows*.  Then you can debug a crash dump like this:

    windbg -sflags 0x80030377 -g -y <path containing .pdb> -z <target.dmp>

Loading the ``.pdb`` symbols can take a long time.

## Using windbg

 * ``~`` - List threads.
 * ``k`` - Print stack trace for current thread.
 * ``~#s`` - Switch to thread ``#``.
 * ``~#k`` - Print stack trace of thread ``#``.
 * ``~*k`` - Print stack trace of every thread.

See also https://theartofdev.com/windbg-cheat-sheet/

## Using DrMinGW
Download and install DrMinGW from https://github.com/jrfonseca/drmingw/releases.
Install it with:

    drmingw -i

Then select **Debug the program** when a program crashes.  DrMinGW should
display a stack trace.

Alternative you can run DrMinGW on a running or hung process like this:

    drmingw -b -p target.exe

See https://github.com/jrfonseca/drmingw
