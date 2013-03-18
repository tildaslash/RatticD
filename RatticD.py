#!/usr/bin/python
import cherrypy
import os
from subprocess import call

ENCVOL = '/dev/vg_daniel-laptop/rattic_encrypted'
LUKSVOL = 'rattic_encrypted'
MOUNTPOINT = '/opt/rattic_encrypted'
TMPFILE = '/tmp/rkey'
STARTCMD = ['service', 'mysqld', 'start']
STOPCMD = ['service', 'mysqld', 'stop']

def startdb(password):
    if not unlockfs(password):
        return False
    if not startmysql():
        return False
    return True

def startmysql():
    call(STARTCMD)
    return True

def unlockfs(password):
    # Get mapped directory
    mapped = os.path.join('/dev/mapper/', LUKSVOL)

    # Write the key to a file
    with open(TMPFILE, 'w') as f:
        f.write(password)
    f.closed

    # Open the encrypted FS
    call(['cryptsetup', '-d', TMPFILE, 'luksOpen', ENCVOL, LUKSVOL])
    if not os.path.exists(mapped):
        return False

    # Erase and remove temp file
    with open(TMPFILE, 'w') as f:
        f.write('OVERWRITETHEPASSWORDWITHSOMETHINGELSE')
    f.closed
    os.unlink(TMPFILE)

    # Make sure the mountpoint exists
    if not os.path.exists(MOUNTPOINT):
        os.mkdir(MOUNTPOINT)

    # Mount the filesystem
    call(['mount', mapped, MOUNTPOINT])
    return True

def checkunlock():
    mapped = os.path.join('/dev/mapper/', LUKSVOL)
    return os.path.exists(mapped)

def sendform(errormsg=None):
    return (
        "<form action=\"\" method=\"post\">"
        "    <h1>Appliance Locked</h1>"
        "    <p>The RatticB appliance is currently locked."
        "       Please enter the master password to continue.</p>"
        "    <input type=\"password\" name=\"password\" value=\"\""
        "        size=\"10\" maxlength=\"40\"/>"
        "    <p><input type=\"submit\" value=\"Unlock\"/></p>"
        "</form>")

class AppRoot:
    def unlock(self, password=None):
        if checkunlock():
            raise cherrypy.HTTPRedirect("/")
        if password is not None:
            if startdb(password):
                raise cherrypy.HTTPRedirect("/")
            else:
                return sendform('Incorrect password.')
        else:
            return sendform()
    unlock.exposed = True

cherrypy.quickstart(AppRoot())

