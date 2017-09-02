#!/usr/bin/env python3

import os
import re
import uuid
from subprocess import Popen, PIPE # Subprocess management
from sys import platform as _platform
import socket       # Low-level networking interface 
import psutil as ps
import datetime as dt
import json
import argparse
import math
import platform # Access to underlying platform's identifying data 

# ---------------Dictionaries---------------#
#  https://wiki.archlinux.org/index.php/Color_Bash_Prompt
# escape[ x;y   x-{0 normal 1 bold} y-color
CLR = "\033[0;0m"   # normal color scheme
BK = "\033[0;30m"   # black
BL = "\033[0;34m"   # blue
GR = "\033[0;32m"   # green
CY = "\033[0;36m"   # cyan
RD = "\033[0;31m"   # red
PL = "\033[0;35m"   # purple
YW = "\033[0;33m"   # yellow
GY = "\033[0;30m"   # grey
LG = "\033[0;37m"   # light grey

# Bold colors (note be 'B' before the color name)
BBK = "\033[1;30m"   # black
BBL = "\033[1;34m"   # blue
BGR = "\033[1;32m"   # green
BCY = "\033[1;36m"   # cyan
BRD = "\033[1;31m"   # red
BPL = "\033[1;35m"   # purple
BYW = "\033[1;33m"   # yellow
BGY = "\033[1;30m"   # grey
BLG = "\033[1;37m"   # light grey

colorDict = {
	'Ubuntu':           [RD, BRD, BYW],
        'Mac OS X':         [GR, YW, RD, BL],
	'Raspbian':         [RD, BRD, GR],
	'Linux':            [CLR, BBL],
        'Sensors':          [BRD, BGR, BYW],
        'Clear':            [CLR]
}

logosDict = {'Raspbian':"""{color[0]}
{color[2]}        .~~.   .~~.      {results[0]}
{color[2]}       '. \ ' ' / .'     {results[1]}
{color[0]}        .~ .~~~..~.      {results[2]}
{color[0]}       : .~.'~'.~. :     {results[3]}
{color[0]}      ~ (   ) (   ) ~    {results[4]}
{color[0]}     ( : '~'.~.'~' : )   {results[5]}
{color[0]}      ~ .~ (   ) ~. ~    {results[6]}
{color[0]}       (  : '~' :  )     {results[7]}
{color[0]}        '~ .~~~. ~'      {results[8]}
{color[0]}            '~'          {results[9]}
{color[0]}                         {results[10]}
{color[0]}                         {results[11]}
{color[0]}                         {results[12]}
\x1b[0m"""
,'Ubuntu':"""{color[0]}
{color[0]}                          .oyhhs:   {results[0]}
{color[1]}                 ..--.., {color[0]}shhhhhh-   {results[1]}
{color[1]}               -+++++++++`:{color[0]}yyhhyo`  {results[2]}
{color[2]}          .--  {color[1]}-++++++++/-.-{color[0]}::-`    {results[3]}
{color[2]}        .::::-   {color[1]}:-----:/+++/++/.   {results[4]}
{color[2]}       -:::::-.          {color[1]}.:++++++:  {results[5]}
{color[1]}  ,,, {color[2]}.:::::-`             {color[1]}.++++++- {results[6]}
{color[1]}./+++/-{color[2]}`-::-                {color[1]}./////: {results[7]}
{color[1]}+++++++ {color[2]}.::-                        {color[1]}{results[8]}
{color[1]}./+++/-`{color[2]}-::-                {color[0]}:yyyyyo {results[9]}
{color[1]}  ``` `{color[2]}-::::-`             {color[0]}:yhhhhh: {results[10]}
{color[2]}       -:::::-.         {color[0]}`-ohhhhhh+  {results[11]}
{color[2]}        .::::-` {color[0]}-o+///+oyhhyyyhy:   {results[12]}
{color[2]}         `.--  {color[0]}/yhhhhhhhy+{color[2]},....
{color[0]}               /hhhhhhhhh{color[2]}-.-:::;
{color[0]}               `.:://::- {color[2]}-:::::;
{color[2]}                         `.-:-'
{color[2]}
\x1b[0m"""
, 'Mac OS X':"""{color[0]}
{color[0]}                              Here's              {results[0]}
{color[0]}                             to the               {results[1]}
{color[0]}             crazy ones,    the      misfits,     {results[2]}
{color[0]}       the rebels, the troublemakers.The round    {results[3]}
{color[1]}     pegs in the square holes. They're not fond   {results[4]}
{color[1]}    of rules, and they have no respect            {results[5]}
{color[1]}    for the status quo. You can quote             {results[6]}
{color[1]}    them. Disagree with them. Glarify             {results[7]}
{color[2]}    or vilify them. About the only thing          {results[8]}
{color[2]}     you can't do is ignore them, because they    {results[9]}
{color[2]}      change things.   And while some may see     {results[10]}
{color[3]}        them as the crazy ones, we see genius.    {results[11]}
{color[3]}          Because the people who are crazy e-     {results[12]}
{color[3]}           nough to think they can change the
{color[3]}             world are the      ones who do.
\x1b[0m"""
, 'Linux':"""{color[0]}
{color[0]}              a8888b.            {results[0]}
{color[0]}             d888888b.           {results[1]}
{color[0]}             8P"YP"Y88           {results[2]}
{color[0]}             8|o||o|88           {results[3]}
{color[0]}             8'    .88           {results[4]}
{color[0]}             8`._.' Y8.          {results[5]}
{color[0]}            d/      `8b.         {results[6]}
{color[0]}          .dP   .     Y8b.       {results[7]}
{color[0]}         d8:'   "   `::88b.      {results[8]}
{color[0]}        d8"           `Y88b      {results[9]}
{color[0]}       :8P     '       :888      {results[10]}
{color[0]}        8a.    :      _a88P      {results[11]}
{color[0]}      ._/"Yaa_ :    .| 88P|      {results[12]}
{color[0]}      \    YP"      `| 8P  `.
{color[0]}      /     \._____.d|    .'
{color[0]}      `--..__)888888P`._.'
\x1b[0m"""
}

def autoSize(used, total):
    mem = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    for x in range(1,6):
        if total > 1000:
            used = math.ceil(used / 1024)
            total = math.ceil(total / 1024)
            size = mem[x]
    return used,total,size

#--------------------Classes--------------#
class Output(object):
    results = []

    def __init__(self):
        self.distro, self.pname = self.detectDistro()
        self.json = {}

    def detectDistro(self):
        """
        Attempts to determine the distribution and draw the logo.However, if it
        can't, then it defaults to 'Linux' and draws a simple linux penguin.
        """
        dist = _platform.lower() # lowcase 
        pname = ''

        if dist == 'darwin':
            dist = 'Mac OS X'
        elif dist == 'freebsd':
            dist = 'FreeBSD'
        elif dist == 'Arch':
            dist = 'Arch Linux'
        elif dist == 'openSUSE project':
            dist = 'openSUSE'
        else:
            dist, pname = self.readDistro()
        
        return dist, pname

    def readDistro(self, f='/etc/os-release'):
        """
        1. Checks if a file exists, if so, reads it
        2. looks for distribution name in file
        3. return name and if not successful, just says 'Linux' which is the default

        $ cat /etc/os-release
        NAME="Ubuntu"
        VERSION="16.04.3 LTS (Xenial Xerus)"
        ID=ubuntu
        ID_LIKE=debian
        PRETTY_NAME="Ubuntu 16.04.3 LTS"
        VERSION_ID="16.04"
        HOME_URL="http://www.ubuntu.com/"
        ORT_URL="http://help.ubuntu.com/"
        BUG_REPORT_URL="http://bugs.launchpad.net/ubuntu/"
        VERSION_CODENAME=xenial
        UBUNTU_CODENAME=xenial
        """

        try:
            txt = open(f).readlines()
            pretty_name = ''
            name = ''
            for line in txt:
                if line.startswitch('PERTTY_NAME'):
                    pretty_name = line.split('=')[1].replace('"', '').replace('\n', '').replace('GNU/Linux ', '').replace('LTS', '')
                if line.startswith('NAME'):
                    name = line.split('=')[1].replace('"', '').replace('\n', '').replace(' GNU/Linux', '')

            if not name:
                name = 'Linux'
            return name, pretty_name
        except:
            name = Popen(['lsb_release', '-is'], stdout=PIPE).communicate()[0].decode('Utf-8').rstrip('\n')
            if not name:
                name = 'Linux'
            return name, ''
        
    def getDistro(self):
        """
        Ideally returns the pretty distro name instead of the short distro name.
        If we weren't able to figure out the distro,it defaults to Linux 
        """
        if self.pname:
            return self.pname
        else:
            return self.distro

    def append(self, display):
        """
        Sets up the printing
        """
        self.results.append('%s%s: %s%s' % (colorDict[self.distro][1], display.key, colorDict['Clear'][0], display.value))
        self.json[display.key] = display.value

    def output(self, js=False):
        """
        Does the printing. Either picture and info to screen or dumps json.
        """
        if js:
            print(json.dumps(self.json))
        else:
            print(logosDict[self.distro].format(color=colorDict[self.distro], results=self.results))

class User(object):
    def __init__(self):
        self.key = 'User'
        self.value = os.getenv('USER')
    
class Hostname(object):
    def __init__(self):
        self.key = 'Hostname'
        self.value = platform.node() # '15-MBP-Chyi.local'

class OS(object):
    def __init__(self, dist):
        OS = dist
        if dist == 'Mac OS X':
            v = platform.mac_ver() # ('10.12.6', ('', '', ''), 'x86_64')
            OS = OS + ' ' + v[0] + ' ' + v[2]
        else:
            OS = OS + ' ' + platform.machine()

        self.key = 'OS'
        self.value = OS

class Kernel(object):
    def __init__(self):
        self.key = 'Kernel'
        self.value = platform.release()

class Uptime(object):
    def __init__(self):
        up = ps.boot_time()
        up = dt.datetime.fromtimestamp(up)
        now = dt.datetime.now() 
        diff = now - up
        uptime = '%d days %d hrs %d mins' % (diff.days, diff.seconds / 3600, (diff.seconds % 3600) / 60)
        self.key = 'Uptime'
        self.value = uptime

class Shell(object):
    def __init__(self):
        self.key = 'Shell'
        self.value = os.getenv('SHELL')

class Processes(object):
    def __init__(self):
        self.key = 'Processes'
        self.value = str(len(ps.pids())) + ' running'

class Packages(object):
    def __init__(self, dist):
        try:
            if dist == 'Mac OS X':
                p1 = Popen(['brew', 'list', '-1'], stdout=PIPE).communicate()[0].decode("Utf-8")
            elif dist == 'Ubuntu' or dist == 'Debian' or dist == 'Raspbian':
                p0 = Popen(['dpkg', '--get-selections'], stdout=PIPE)
                p1 = Popen(['grep', '-v', 'deinstall'], stdin=p0.stdout, stdout=PIPE).communicate()[0].decode("Utf-8")
            packages = len(p1.rstrip('\n').split('\n'))
        except:
            packages = 0
        self.key = 'Packages'
        self.value = packages

class CPU(object):
    def __init__(self, dist):
        try:
            if dist == 'Mac OS X':
                cpu = Popen(['sysctl', '-n', 'machdep.cpu.brand_string'], stdout=PIPE).communicate()[0].decode('Utf-8').split('\n')[0]
                c = cpu.replace('(R)', '').replace('(TM)', '').replace('CPU', '').split()
                cpuinfo = ' '.join(c)
            else:
                txt = open('/proc/cpuinfo').readlines()
                cpuinfo = ''
                for line in txt:
                    if line.find('model name') >= 0:
                        cpuinfo = line.split(': ')[1].strip('\n')
        except:
            cpuinfo = 'unknown'

        self.key = 'CPU'
        self.value = cpuinfo

class RAM(object):
    def __init__(self):
        ram = ps.virtual_memory()
        used = ram.used
        total = ram.total

        used, total, size = autoSize(used, total)
        ramdisplay = '%s %s/ %s %s' %(used, size, total, size)

        self.key = 'RAM'
        self.value = ramdisplay 

class Disk(object):
    def __init__(self, json=False):
        disk = ps.disk_usage('/')
        total = disk.total
        used = disk.used 

        used, total, size = autoSize(used, total)
        usedpercent = math.ceil(float(used) / float(total) * 100.0)

        if json:
            disk = '%s / %s %s' % (used, total, size)
        else:
            if usedpercent <= 33:
                disk = '%s%s %s/ %s %s' %(colorDict['Sensors'][1], used, colorDict['Clear'][0], total, size)
            elif usedpercent > 33 and usedpercent < 67:
                disk = '%s%s %s/ %s %s' % (colorDict['Sensors'][2], used, colorDict['Clear'][0], total, size)
            else:
                disk = '%s%s %s/ %s %s' % (colorDict['Sensors'][0], used, colorDict['Clear'][0], total, size)

        self.key = 'Disk'
        self.value = disk

class IP(object):
    def __init__(self, zeroconfig=False):
        """
        This tries to get the host name and deterine the IP address from it.
        It also tries to handle zeroconfig well. Also, there is an issue with getting
        the MAC address, so this uses uuid to get that too. However, using the UUID is
        not reliable, because it can return any MAC address (bluetooth, wired, wireless, etc)
        or even make a random one.
        """
        ip = '127.0.0.1'
        # uuid.getnode() Get the hardware address as a 48-bit positive integer.
        mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        #mac = ':'.join(uuid.UUID(int = uuid.getnode()).hex[-12:])

        try:
            host = socket.gethostname()
            if zeroconfig:
                if host.find('.local') < 0:
                    host = host + '.local'

            ip = socket.gethostbyname(host)
        except:
            print('Error in IP()')

        self.key = 'IP'
        self.value = ip + ' / MAC: ' + mac.upper()
class CPU2(object):
    def __init__(self):
        # psutil.cpu_percent(interval=1, percpu=True)
        #   interval is > 0.0 compares system cpu times elapsed before and after
        #   percpu=True return a list of floats representing the utilization each CPU
        cpu = ps.cpu_percent(interval=1, percpu=True)
        self.key = 'CPU Usage'
        self.value = str(cpu)

def handleArgs():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""
Display system info and a logo for OS


Currently, it displays:
        Username
        Hostname
        IP Address / MAC address
        OS Name
        Kernel Version
        Uptime: days hrs mins
        Shell
        Processes Running
        Package Installed
        CPU
        CPU Usage
        RAM
        Disk Usage""", epilog="""Package info at: https://pypi.python.org/pypi/archey3
Submit issues to: https://github.com/Chyiyaqing/archey3""")

    parser.add_argument('-d', '--display', help='displays all ascii logs and exits', action='store_true')
    parser.add_argument('-j', '--json', help='instead of printing to screen, returns system as json', action='store_true')
    parser.add_argument('-v', '--version', help='prints version number', action='store_true')
    parser.add_argument('-z', '--zeroconfig', help='assume a zeroconfig network and adds .local to the hostname', action='store_true')

    args = vars(parser.parse_args())

    return args

def main():
    args = handleArgs()

    if args['display']:
        for i in logosDict:
            print(i)
            print(logosDict[i].format(color=colorDict[i], results=list(range(0,13))))
        return 0

    # Need a good way to display version number, there seems to be no standard
    if args['version']:
        print('archey3 V.0.1')
        return 0

    out = Output()
    out.append(User())
    out.append(Hostname())
    out.append(IP(args['zeroconfig']))
    out.append(OS(out.getDistro()))
    out.append(Kernel())
    out.append(Uptime())
    out.append(Shell())
    out.append(Processes())
    out.append(Packages(out.distro))
    out.append(CPU(out.distro))
    out.append(CPU2())
    out.append(RAM())
    out.append(Disk(args['json']))

    out.output(args['json'])

if __name__ == '__main__':
    main() 

    
