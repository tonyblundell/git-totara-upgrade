"""
Totara upgrade module.

Supplies function 'upgrade' for upgrading a Totara codebase from one version
to another.

Automatically accepts the remote version of conflicted files that weren't
modified outside of Totara.

Can be run as a program. Requires the name of a git remote containing core
Totara, a source tag and a target tag.

Should be run from within the source directory with a clean git head.

Example usage:
python upg.py upstream totara-2.5.27 totara.2.7.3
python upg.py --help

Tested with Python 2.7.6 on Ubuntu 14.04.
"""

import argparse
import subprocess
import sys


def upgrade(remote, fro, to):
    """Upgrade a Totara codebase from one version to another.
    Assumes core totara is available on the given git remote.
    Works by starting a git merge, and automatically accepting safe conflicts.
    Safe means we didn't modify the file. It was modified as part of core
    Totara and thus the remote version can safely be accepted.
    Should be run from within the source directory and with a clean git head.
    """
    fetch(remote, [fro, to])
    modified = get_modified(fro)
    merge(to)
    conflicted = get_conflicted()
    safe = get_safe(conflicted, modified)
    accept(safe)
    print_advice(len(conflicted) - len(safe))


def fetch(remote, tags):
    """Git fetch the given tags.
    Ensures we have the latest code and also serves to validate user params.
    """
    call(['git', 'fetch', remote, '--tags'])
    for tag in tags:
        call(['git', 'fetch', remote, tag])


def get_modified(tag):
    """Return a list of tags that have been modified.
    Works by comparing the current head to the source tag (core Totara).
    """
    s = call(['git', 'diff', tag, '--name-only'])
    return s.splitlines()


def merge(tag):
    """Git merge the target tag into the current head."""
    call(['git', 'merge', '--no-ff', tag], die_on_error=False)


def get_conflicted():
    """Return a list of files that currently contain conflicts."""
    s = call(['git', 'diff', '--name-only', '--diff-filter=U'])
    return s.splitlines()


def get_safe(conflicted, modified):
    """Return a list of files for which the remote version can be accepted.
    This means any file that has a conflict, but we didn't modify.
    Works by converting the given lists to sets, using Pythons set difference
    function, then converting the resulting set back to a list.
    """
    return list(set(conflicted).difference(set(modified)))


def accept(files):
    """Git checkout the remote version, then stage the given list of files."""
    for fil in files:
        call(['git', 'checkout', '--theirs', fil], die_on_error=False)
        call(['git', 'add', fil], die_on_error=False)


def print_advice(num_conflicted):
    """Prints some advice for the user on what to do after exit."""
    print 'Completed with {0} conflicts'.format(num_conflicted)
    if num_conflicted:
        print 'Use \'git mergetool\' to resolve, then \'git commit\''
    else:
        print 'Safe to \'git commit\''
    print 'Or use \'git merge --abort\' to pretend this never happened'


def call(cmd, die_on_error=True):
    """Calls an external command.
    If die_on_error is truthy will exit uncleanly with a nice error message.
    """
    pipe = subprocess.PIPE
    proc = subprocess.Popen(cmd, stdout=pipe, stderr=pipe)
    out, err = proc.communicate()
    status = proc.returncode
    if status and die_on_error:
        msg = 'SUBPROCESS EXITED WITH CODE {0}\n{1}\n{2}\n{3}'
        msg = msg.format(status, ' '.join(cmd), out, err)
        sys.exit(msg)
    return out


# If run as a program, kick off an upgrade with the given arguments.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('remote', help='Git remote where tags are held')
    parser.add_argument('fro', help='Git tag to upgrade from')
    parser.add_argument('to', help='Git tag to upgrade to')
    args = parser.parse_args()
    upgrade(args.remote, args.fro, args.to)
