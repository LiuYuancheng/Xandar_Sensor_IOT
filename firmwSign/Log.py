from __future__ import print_function
#-----------------------------------------------------------------------------
# Name:        Log.py
# Purpose:     Debug/error logging
#
# Author:      <Jim Von Ehr>
#
# Created:     2008/06/17
# Copyright:   (c) 2008-2011 Zyvex Labs, LLC, (c) 2011-2016 Zycraft Pte Ltd
# License:     <Python standard>
#-----------------------------------------------------------------------------
"""Log: debug/error logging. This uses only Python library imports, so is safe to
import into any Zycraft module. Note that the main that initializes things should
call Log.initLogging(...)
"""
"""Copyright (c) 2008-2011, Zyvex Labs, LLC, (c) 2011-2016 Zycraft Pte. Ltd."""
# import logging
import logging.handlers
import time
import os
import traceback
from collections import deque

DEFAULT_LOGGER_NAME = 'ZyLog'
ROLLOVER_LENGTH = 1.0e7 + 1     # Python 'handlers' compares >= length, so roll at 10MB exactly

zLogger = None                  # logging object
zHandler = None                 # logging handler
gDetailFlags = 0                # flags controlling Log.detail
gLogDir = None                  # log directory path name: .../Zycraft/Logs/<appName>
gCurrentDir = ''                # as date rolls over, this holds the folder name of the current folder
gNewDir = ''                    # new directory name built by makeLogFile
# set below True to put rotating log files into folder named yyyymmdd
# otherwise, they will be under the Logs directory
gPutLogsUnderDate = False
gRolloverCallback = None        # call this when data rollover: cb(oldFolderName, newFolderName)
gTerminating = False            # set True to terminate any threading
gTruncateTo = 0                 # if >0, only keep this many files in directory
gFileList = None                # deque of files being truncated

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class Loggit(object):
    """Returns a file-like object that caller can use to replace sys.stdout & stderr:
    sys.stdout = Log.Loggit(False)
    sys.stderr = Log.Loggit(True)
    """
    def __init__(self, fWarning=False):
        self.str = ''
        self.appending = False
        self.fWarning = fWarning

#-----------------------------------------------------------------------------
    def flush(self):
        pass

#-----------------------------------------------------------------------------
    def write(self, s):
        s = s.replace('\r', '\n')
        s = s.replace('\n\n', '\n')

        # tricky stuff - pack lines together until we get a \n
        if self.appending:
            self.str += s
        else:
            self.str = s
        self.appending = '\n' not in s      # append next line to this if not \n

        if not self.appending:
            if self.fWarning:
                # FIXME: this is a hack while tracking down garbage collection issues
                if self.str.startswith('gc:'):
                    debug(self.str[:-1])        # demote GC strings to debug, not warning
                else:
                    warning(self.str[:-1])      # don't emit last newline
            else:
                debug(self.str[:-1])
            self.str = ''

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# class ZCTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
#     """Standard TimedRotatingFileHandler makes a mess of file names that end in .txt - this
#     version inserts an index in between the name and the suffix"""
#     def __init__(self, filename, *args, **kwargs):
#         # zcFilenameBase is just the base name - cobble up better name by adding date/time
#         self.zcFilenameBase = filename
#         yyyymmdd, hhmmss = getLogTime()
#         self.zcHHMMSS = hhmmss      # save creation time
#         self.zcSuffix = 0           # save suffix
#         fName = self.buildFilename()
#         logging.handlers.TimedRotatingFileHandler.__init__(self, fName, *args, **kwargs)
#         self.nextIndex = 0
#
# #-----------------------------------------------------------------------------
#     def buildFilename(self):
#         self.zcSuffix += 1  # advance to next suffix
#         fileName = self.zcFilenameBase + '_' + self.zcHHMMSS + '_' + str(self.zcSuffix) + '.txt'
#         if gPutLogsUnderDate:
#             yyyymmdd, hhmmss = getLogTime()  # put in folder by today's date
#             pathName = makeLogFile(yyyymmdd, fileName)
#         else:
#             pathName = makeLogFile(fileName)
#         return pathName
#
# #-----------------------------------------------------------------------------
#     def doRollover(self):
#         """Handle rollover for TimedRotatingFileHandler"""
#         if self.stream:
#             self.stream.close()
#             self.stream = None
#
#         dfn = self.buildFilename()
#         self.baseFilename = dfn     # this name is used by logging internals
#         self.mode = 'w'
#         self.stream = self._open()
#         currentTime = int(time.time())
#         newRolloverAt = self.computeRollover(currentTime)
#         while newRolloverAt <= currentTime:
#             newRolloverAt = newRolloverAt + self.interval
#         #If DST changes and midnight or weekly rollover, adjust for this.
#         if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
#             dstNow = time.localtime(currentTime)[-1]
#             dstAtRollover = time.localtime(newRolloverAt)[-1]
#             if dstNow != dstAtRollover:
#                 if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
#                     newRolloverAt = newRolloverAt - 3600
#                 else:           # DST bows out before next rollover, so we need to add an hour
#                     newRolloverAt = newRolloverAt + 3600
#         self.rolloverAt = newRolloverAt

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ZCRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Standard RotatingFileHandler makes a mess of file names that end in .txt - this
    version inserts an index in between the name and the suffix"""
    def __init__(self, filename, *args, **kwargs):
        # zcFilenameBase is just the base name - cobble up better name by adding date/time
        self.zcFilenameBase = filename
        fName = self.buildFilename(True)
        logging.handlers.RotatingFileHandler.__init__(self, fName, *args, **kwargs)
        self.nextIndex = 0

#-----------------------------------------------------------------------------
    def buildFilename(self, fResetTime=False):
        global gCurrentDir, fNewDir
        yyyymmdd, hhmmss = getLogTime()  # put in folder by today's date
        if fResetTime:
            # reset time part of name
            self.zcTime = yyyymmdd + '_' + hhmmss      # save creation date & time
            self.zcSuffix = 0           # save suffix
        self.zcSuffix += 1  # advance to next suffix
        fileName = self.zcFilenameBase + '_' + self.zcTime + '_' + str(self.zcSuffix) + '.txt'
        if gPutLogsUnderDate:
            pathName = makeLogFile(yyyymmdd, fileName)
        else:
            pathName = makeLogFile(fileName)
        if gNewDir != gCurrentDir:
            # if we changed the directory we're logging to, call catchDateRollover if needed
            if gRolloverCallback:
                gRolloverCallback(gCurrentDir, gNewDir)
            gCurrentDir = gNewDir
#         print('Log.ZCRotatingFileHandler.buildFilename returning ' + pathName)
        return pathName

#-----------------------------------------------------------------------------
    def doRollover(self, fResetTime=False):
        """Handle rollover for TimedRotatingFileHandler"""
        if self.stream:
            self.stream.close()
            self.baseFilename = 'TempBogusLog.txt'      # in case someone still tries to write & opens file
        dfn = self.buildFilename(fResetTime)
        if gTruncateTo and (gFileList is not None):
            if len(gFileList) >= gTruncateTo:
                truncFileName = gFileList.popleft()
                #print('doRollover truncating: len:%s, truncName:%s, dfn:%s' % (len(gFileList), truncFileName, dfn))
                os.rename(truncFileName, dfn)
            gFileList.append(self.baseFilename)
        self.baseFilename = dfn     # this name is used by logging internals
        self.mode = 'w'
        self.stream = self._open()
#         print('Log.ZCRotatingFileHandler.doRollover opened ', self.baseFilename)

#-----------------------------------------------------------------------------
#  STANDARD PYTHON LOGGING METHODS
#-----------------------------------------------------------------------------
# print compact callstack, with introductory string
def callstack(*args):
    stk = traceback.extract_stack()
    debug(*args)
    for tup in stk[:-2]:
        fName, line, fcn, txt = tup
        debug('...%s:%i %s', os.path.split(fName)[1], line, txt)

#-----------------------------------------------------------------------------
def myPrint(*args):
    """Handler when we can't write to log"""
    if len(args) > 1:
        s = args[0] % args[1:]
        print(s)
    else:
        print(args[0])

#-----------------------------------------------------------------------------
def debug(*args):
    if zLogger:
        zLogger.debug(*args)
    else:
        myPrint(*args)

# do logged debug, plus print
def debugP(*args):
    if zLogger:
        zLogger.debug(*args)
    myPrint(*args)

#-----------------------------------------------------------------------------
def detail(flags, *args):
    """Log details, if our global gDetailFlags & flags == flags. Caller should
    set up which details should be logged by calling Log.detailSetFlags(flags)
    and then pass in the detailed flag bit vector controlling detail logging.
    E.G., if we want to control logging of PLC details, and we have somewhere
    defined the flag FLG_PLC_DETAILS, we set up to log this by calling:
    Log.detailSetFlags(Log.detailGetFlags() | FLG_PLC_DETAILS)
    and we control logging by calling:
    Log.detail(FLG_PLC_DETAILS, formatString, args)
    flags: bit vector to compare against gDetailFlags to see whether to log this
    """
    if (gDetailFlags & flags) == flags:     # flags set to log this detail?
        if zLogger:
            zLogger.debug(*args)
        else:
            myPrint(*args)

#-----------------------------------------------------------------------------
def detailGetFlags():
    """Return current detail flag"""
    return gDetailFlags

#-----------------------------------------------------------------------------
def detailSetFlags(flags):
    """Set detail flag globally"""
    global gDetailFlags
    gDetailFlags = flags
    #debug('>>>>>>>>>>>>>>> detailSetFlags:0x%08x', flags)
    #callstack('called by')

#-----------------------------------------------------------------------------
#info = zLogger.info
def info(*args):
    if zLogger:
        zLogger.info(*args)
    else:
        myPrint(*args)

# do logged info, plus print
def infoP(*args):
    if zLogger:
        zLogger.info(*args)
    myPrint(*args)

#-----------------------------------------------------------------------------
#warning = zLogger.warning
def warning(*args):
    if zLogger:
        zLogger.warning(*args)
    else:
        myPrint(*args)

# do logged warning, plus print
def warningP(*args):
    if zLogger:
        zLogger.warning(*args)
    myPrint(*args)

#-----------------------------------------------------------------------------
def error(*args):
    """Called to print error message"""
    if zLogger:
        zLogger.error(*args)
    else:
        myPrint(*args)

# do logged error, plus print
def errorP(*args):
    if zLogger:
        zLogger.error(*args)
    myPrint(*args)

#-----------------------------------------------------------------------------
def exception(*args):
    """Called to print exception, call stack, args"""
    if zLogger:
        error('***EXCEPTION***')
        error(traceback.format_exc())
        error(*args)
    else:
        print('***EXCEPTION***')
        print(traceback.format_exc())
        myPrint(*args)

# do logged exception, plus print
def exceptionP(*args):
    if zLogger:
        error('***EXCEPTION***')
        error(traceback.format_exc())
        error(*args)
    print('***EXCEPTION***')
    print(traceback.format_exc())
    myPrint(*args)

#-----------------------------------------------------------------------------
gConsole = None
def setLogger(strm):
    """
    Define a handler which writes INFO messages or higher to the specified stream.
    I had to change this for multiprocessing, to allow None for strm, to remove handler
    for subprocesses (cannot write to main process' screen in subprocess)
    strm: stream, such as ScreenLog.ScreenLog, where we can write high priority messages
    """
    global gConsole
    if strm is None:
        # called from sub-process or terminate - want to remove previous logger
        if gConsole is not None:
            zLogger.removeHandler(gConsole)
            gConsole = None
    else:
        gConsole = logging.StreamHandler(strm)
        gConsole.setLevel(logging.INFO)
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        # tell the handler to use this format
        gConsole.setFormatter(formatter)
        # add the handler to the root logger
        zLogger.addHandler(gConsole)

#-----------------------------------------------------------------------------
# USEFUL LOG-RELATED UTILITIES FOR EVERYONE
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
def catchDateRollover(cbRollover):
    """
    Set up callback in case of date rollover.
    we call: cbRollover(oldDirName, newDirName)
    """
    global gRolloverCallback
    gRolloverCallback = cbRollover

#-----------------------------------------------------------------------------
def cleanOldFiles(dirName, fileNameBase, cnt):
    """Examine files in 'dirName', and if we find any that start with
    'fileNameBase', remove the oldest of those to keep no more
    than 'cnt' files in that dir
    This may be used for apps own logs, as well as the Log.xxx logs"""
    #s = 'Log.cleanOldFiles dirName:' + dirName +' fnBase:' + fileNameBase +' cnt:' + str(cnt)
    #print(s)
    log_list = []
    for f in os.listdir(dirName):
        # added every log file found into the log file list
        if f[0:len(fileNameBase)] == fileNameBase: log_list.append(f)
    if len(log_list) > cnt:     # if the number of log files found more than the maximum number
        # set current working directory
        prevDir = os.getcwd()
        os.chdir(dirName)
        # sort the file list according to modification time
        log_list.sort(key=lambda x: (os.stat(x).st_mtime, x))
        # keep most recent log files and remove the old ones
        for i in range(len(log_list) - cnt):
            try:
                #print('Log.cleanOldFiles deleted: ', log_list[i])
                os.remove(log_list[i])
            except:
                warning('Log: cleanOldFiles could not delete <%s>', log_list[i])
        os.chdir(prevDir)

#-----------------------------------------------------------------------------
def getLogTime(now=None):
    """Get current local time, return tuple for logging (yyyymmdd, hhmmss)
    Can pass floating point time, or leave empty for 'now' """
    if now is None:
        timeTup = time.localtime()
    else:
        timeTup = time.localtime(now)
    t = time.strftime('%Y%m%d %H%M%S', timeTup)
    return t.split()

#-----------------------------------------------------------------------------
def initLogging(wd, logDirName, appName, filePrefix, historyCnt=100,
        fPutLogsUnderDate=False, loggerName=DEFAULT_LOGGER_NAME, truncateTo=0):
    """Initialize logging
    wd: pathname of working directory under which we put logs
    logDirName: put all logs into this dir, i.e. 'Logs'
    appName: make subdir under LogDirName for this app, i.e. CommHub - if '', skip this level
        because we are putting "Logs" directly under "appName" directory instead of under "Zycraft"
    filePrefix: prefix for log files, i.e. 'Hub'
    historyCnt: # of log files to save (delete oldest if >this many files)
    truncateTo: dynamically truncate to just this many log files (good for embedded systems on BBB)
        but do not truncate if this == 0
    fPutLogsUnderDate: if True, we arrange to put log files into a daily
        folder, otherwise, they go directly into the Logs folder.
    loggerName: name of this logger, i.e. 'ZyLog'
    This assumes current WD set to Zycraft, and that we put our top log dir under it"""
    global zLogger, zHandler, gPutLogsUnderDate, gLogDir, gTruncateTo, gFileList
    assert wd is not None       # caller must set this up
    try:
#         if wd is None:
#             # if called from testing code, we haven't set up all the WD stuff,
#             # so if caller passes None for wd, we will do default setup here
#             TOPDIR = 'Zycraft'          # folder name where we put Logs, Maps, etc
#             gWD = os.getcwd()
#             idx = gWD.find(TOPDIR)
#             if idx != -1:
#                 gTopDir = gWD[:idx + len(TOPDIR)]     # found it - truncate right after TOPDIR
#             else:
#                 gTopDir = gWD   # did not find TOPDIR - use WD
#             wd = gTopDir

        if zLogger is not None:
            # reinitializing
            try:
                print('Log  deleting zLogger for re-init')
                zLogger.removeHandler(zHandler)
                del zLogger
            except:
                exception('Log  could not delete zLogger')
            zLogger = None
            zHandler = None
        gPutLogsUnderDate = fPutLogsUnderDate
        gTruncateTo = truncateTo
        if truncateTo:
            gFileList = deque(maxlen=truncateTo)
        else:
            gFileList = None
        # put 'Logs' at ..../Zycraft level
        gLogDir = wd        # start path from here
        if appName:
            gLogDir = makeLogFile(logDirName, appName)      # extend to here, creating as needed
        else:
            gLogDir = makeLogFile(logDirName)               # extend to here, creating as needed
        zLogger = logging.getLogger(loggerName)
        zHandler = ZCRotatingFileHandler(filePrefix, maxBytes=ROLLOVER_LENGTH)
        zHandler.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s'))
        zLogger.addHandler(zHandler)
        zLogger.setLevel(logging.DEBUG)
    except Exception, e:
        print('Logging setup exception:', e)

    # parse the directory to look for all the log files
    cleanOldFiles(os.path.dirname(zHandler.baseFilename), filePrefix, historyCnt)

#-----------------------------------------------------------------------------
def makeLogFile(*args):
    """Make arbitrary number of directories under our 'Logs' dir, creating
    as necessary, and finally return a fully qualified file name as string.
    'args' is a list of directories in the path to the filename in args[-1]"""
    global gNewDir
    myArgs = [gLogDir]
    myArgs.extend(args[:-1])
    dirPath = os.path.join(*myArgs)
    gNewDir = dirPath      # save this in case someone is watching
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    fileName = os.path.join(dirPath, args[-1])
#     print('Log.makeLogFile made:' + fileName)
    return fileName

#-----------------------------------------------------------------------------
def makeLogFileAtTop(fNameBase, suffix):
    """Make a long-lived log file (possibly spanning days) at the top level
    of .../Zycraft/Logs/.../. This cobbles up a suitable name, based on 'fNameBase',
    and returns a FQN string. When caller is done with that, they can call
    moveToCurrentFolder(fName) to have us move that (closed) file under today's
    folder inside the Logs folder. See NMEA0183 for an example of usage.
    fNameBase: base name for new file, e.g. 'NMEA0183_'
    suffix: file suffix, e.g. '.txt'
    returns: fully-qualified file name string
    """
    yyyymmdd, hhmmss = getLogTime()
    fName = os.path.join(gLogDir, fNameBase + yyyymmdd + '_' + hhmmss + suffix)
    return fName

#-----------------------------------------------------------------------------
def moveToCurrentFolder(fName):
    """Long-duration files that can span a day should be created using makeLogFileAtTop.
    When caller is done, and file closed, it can be moved to the current folder in the
    Logs dir by calling this routine."""
    yyyymmdd = getLogTime()[0]              # find folder info for today's logs
    fNameSrc = os.path.split(fName)[1]      # extract just file name & suffix
    # make name down in date folder (handles date overflow in makeLogFile)
    newFileName = makeLogFile(gLogDir, yyyymmdd, fNameSrc)
    debug('Log  moving file:%s to %s', fName, newFileName)
    os.rename(fName, newFileName)

#-----------------------------------------------------------------------------
# Testing code
#-----------------------------------------------------------------------------
def writeJunk(mb=10):
    """Write 'mb' megabytes of junk to log"""
    print('writeJunk %iMB' % mb)
    lineLen = 100
    hdrLen = 33 + 7 + 1        # header per line, plus len of line #, plus lf
    pad = '$' * (lineLen - hdrLen)
    for i in range((mb * 1000000) // lineLen):
        debug('%06i %s', i, pad)

def main():
    TOPDIR = 'Zycraft'                      # folder name where we put Logs, Maps, etc
    gWD = os.getcwd()
    #print('gWD:%s' % gWD)
    idx = gWD.find(TOPDIR)
    #print('idx:%i' % idx)
    if idx != -1:
        gTopDir = gWD[:idx + len(TOPDIR)]     # found it - truncate right after TOPDIR
    else:
        gTopDir = gWD   # did not find TOPDIR - use WD
    #print('gTopDir:%s' % gTopDir)

    initLogging(gTopDir, 'Logs', 'LogTest1', 'Test', 100, True)
    writeJunk(65)
    initLogging(gTopDir, 'Logs', 'LogTest2', 'Test', 100, False, truncateTo=2)
    writeJunk(65)
    pass

if __name__ == '__main__':
    main()
    print('End of __main__')
