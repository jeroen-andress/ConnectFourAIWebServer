#!/usr/bin/env python

# http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

import sys, os, time, atexit, signal
from signal import SIGTERM

class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, daemonName, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = "/var/run/%s.pid" % daemonName

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
        
        # decouple from parent environment
        os.chdir("/") 
        os.setsid() 
        os.umask(0) 
        
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        signal.signal(signal.SIGTERM, self.sigtermHandler)
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)

    def sigtermHandler(self, signum, frame):
        self.cleanup()
        sys.exit(0)

    def delpid(self):
        os.remove(self.pidfile)

    def readpid(self):
        # Get the pid from the pidfile
        pid = None

        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pass

        return pid

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        pid = self.readpid()        

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        pid = self.readpid()        

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def status(self):
        """
        Get status of the daemon
        """
        pid = self.readpid()
 
        try:
            procfile = file("/proc/%d/status" % pid, 'r')
            procfile.close()
        except IOError:
            sys.stdout.write("there is not a process with the PID specified in %s\n" % self.pidfile)
            sys.exit(0)
        except TypeError:
            sys.stdout.write("pidfile %s does not exist\n" % self.pidfile)
            sys.exit(0)

        sys.stdout.write("the process with the PID %d is running\n" % pid)        

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
		
    def cleanup(self):
        """
        You should override this method when you subclass Daemon. Its will be called when the deamon stopped.
        """

def daemonmain(argv, daemon):
    if len(argv) == 2:
         if 'start' == argv[1]:
              daemon.start()
         elif 'stop' == argv[1]:
              daemon.stop()
         elif 'restart' == argv[1]:
              daemon.restart()
         elif 'status' == argv[1]:
              daemon.status()
         else:
              print "Unknown command"
              return 2
         return 0
    else:
         print "usage: %s start|stop|status|restart" % argv[0]
         return 2

