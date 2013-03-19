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

SERVICES = {
    'mysql': {
      'mount': [('mysql', '/var/lib/mysql')],
      'initscript': '/etc/init.d/mysqld',
    },
}


def _checkmount(mountpoint):
    return os.path.ismount(mountpoint)

def _domount(device, mountpoint, bind=False):
    if _checkmount(mountpoint):
        return True

    if not os.path.exists(mountpoint):
        os.mkdir(mountpoint)
    
    if bind:
        call(['mount', '--bind', device, mountpoint])
    else:
        call(['mount', device, mountpoint])

    return _checkmount(mountpoint)

def _checkdecrypt(clearpath):
    return os.path.exists(clearpath)

def _dodecrypt(encvol, password, clearvol):
    # Get mapped directory
    clearpath = os.path.join('/dev/mapper/', clearvol)

    if _checkdecrypt(clearpath):
        return True

    # Write the key to a file
    with open(TMPFILE, 'w') as f:
        f.write(password)
    f.closed

    # Open the encrypted FS
    call(['cryptsetup', '-d', TMPFILE, 'luksOpen', encvol, clearvol])
    # Erase and remove temp file
    with open(TMPFILE, 'w') as f:
        f.write('OVERWRITETHEPASSWORDWITHSOMETHINGELSE')
    f.closed
    os.unlink(TMPFILE)
    
    return _checkdecrypt(self, path)

def _checkservice(service):
    rtn = call([service['initscript'], 'status'])
    if rtn == 0:
      return True
    return False

def _startservice(service, mountpoint):
    if _checkservice(service):
        return True

    for mp in service['mount']
        location = os.path.join(mountpoint, mp[0])
        if _domount(location, mp[1], bind=True) == False:
            return False
    rtn = call([service['initscript'], 'start'])
    return _checkservice(service)

def startdb(password):
    # Get mapped directory
    clearpath = os.path.join('/dev/mapper/', LUKSVOL)

    if not _dodecrypt(ENCVOL, password, LUKSVOL):
        return False

    if not _domount(clearpath, MOUNTPOINT):
        return False

    for svc in SERVICES.keys():
        if not _startservice(SERVICES[svc]):
            return False

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
    def index(self):
      if startdb(''):
            return "Unlocked and running..."
        else:
            raise cherrypy.HTTPRedirect("/unlock")

    def unlock(self, password=None):
        if startdb(''):
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

