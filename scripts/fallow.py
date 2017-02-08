#!/usr/bin/python
import random
import getopt
import sys
import re
import os
import subprocess
import string
import time
from math import ceil

##--- class
class Job :
  def __init__(self,g,r,j):
    self.globalJobId = g
    self.requestCpus = r
    self.jobStatus = j
      
##--- class
class Queue :

  def getTotalQueued(self):
    return self.totalQueued 
  def getTotalSingleQueued(self):
    return self.totalSingleQueued 
  def getTotalMultiQueued(self):
    return self.totalMultiQueued 
  def getTotalRunning(self):
    return self.totalRunning 
  def getTotalSingleJobsRunning(self):
    return self.totalSingleJobsRunning 
  def getTotalMultiJobsRunning(self):
    return self.totalMultiJobsRunning 
  def getTotalHeld(self):
    return self.totalHeld 
  def getTotalDontKnow(self):
    return self.totalDontKnow 
  def getTotalSingleUnicoresRunning(self):
    return self.totalSingleJobsRunning * 1
  def getTotalMultiUnicoresRunning(self):
    return self.totalMultiJobsRunning * 8



  def __init__(self):
    self.jobs = {}
    self.totalQueued = 0
    self.totalSingleQueued = 0
    self.totalMultiQueued = 0
    self.totalRunning = 0
    self.totalSingleJobsRunning = 0
    self.totalMultiJobsRunning = 0
    self.totalHeld = 0
    self.totalDontKnow = 0

    worked,code,report,err = runCommand ("condor_q -long ")
    if (worked != True):
      print 'ERROR in Queue class, condor_q command did not run'
      sys.exit(1)
    if (code != 0):
      print 'ERROR in Queue class, condor_q command gave return code ', code, ', stderr was ', err
      sys.exit(1)
      
    lines = string.split(report, '\n')

    globalJobId = -1
    requestCpus = -1
    jobStatus = -1

    for l in lines:
      matchObj = re.match('^$',l)  
      if matchObj is not None:
        job = Job(globalJobId,requestCpus,jobStatus)
        self.jobs[globalJobId] = job
        if (jobStatus == 1):
          self.totalQueued = self.totalQueued + 1
          if (requestCpus == 1):
            self.totalSingleQueued = self.totalSingleQueued + 1
          else:
            self.totalMultiQueued = self.totalMultiQueued + 1
        else:
          if (jobStatus == 2):
            self.totalRunning = self.totalRunning + 1
            if (requestCpus == 1):
              self.totalSingleJobsRunning = self.totalSingleJobsRunning + 1
            else:
              self.totalMultiJobsRunning = self.totalMultiJobsRunning + 1 

          else:
            if (jobStatus == 5):
              self.totalHeld = self.totalHeld + 1
            else:
              self.totalDontKnow = self.totalDontKnow + 1
        
      else:
        halves = l.split(' = ')
        if halves[0] == 'GlobalJobId':
          globalJobId = halves[1]
        if halves[0] == 'RequestCpus':
          requestCpus = int(halves[1])
        if halves[0] == 'JobStatus':
          jobStatus = int(halves[1])

##--- class
class Node :

  """ Holds a Node """

  # Constructor, with initial attribute values
  def __init__(self,name):
    self.name = name
    self.detectedCpus = 0    # Don't know
    self.totalSlotCpus = 0   # How much is available on this node
    self.totalUsed     = 0   # How much is used 
    self.slack         = 0   # How much is not used
    self.slots = []
    self.current_slot = {}
    self.hasSlotWith8 = False
    self.hasSlackOf8 = False

  def __cmp__(self, other):
    if self.totalSlotCpus < other.totalSlotCpus:
      return 1
    elif self.totalSlotCpus > other.totalSlotCpus:
      return -1
    else:
      return 0

  def allowSinglecore(self):
    self.slots[0]['OnlyMulticore'] = 'False'
    worked,code,sout,serr = runCommand("condor_config_val -startd -set \"OnlyMulticore = False\" -name " + self.name)
    if ((worked != True) or (code != 0 )):
      print 'WARNING Odd result in allowSinglecore() for node ' + self.name
      return False
    
    return makeCmdTakeHold (self.name)

  def disallowSinglecore(self):
    self.slots[0]['OnlyMulticore'] = 'True'
    worked,code,sout,serr = runCommand("condor_config_val -startd -set \"OnlyMulticore = True\" -name " + self.name)
    if ((worked != True) or (code != 0 )):
      print 'WARNING Odd result in disallowSinglecore() for node ' + self.name
      return False
    return makeCmdTakeHold (self.name)

  def getHasSlotWith8 (self):
    return self.hasSlotWith8

  def getSlackOf8 (self):
    return self.hasSlackOf8

  def getName (self):
    return self.name

  def getSlot(self,s):
    max = len(self.slots) - 1
    if (s < 0 or s > max):
      return None
    slot = self.slots[s]
    return slot

  def getOnlyMulticore(self):
    slot = self.slots[0]
    if 'OnlyMulticore' not in slot:
      return False
    om = slot['OnlyMulticore']
    true = 'True'
    if om.lower() == true.lower():
      return True
    else:
      return False

#  def setOnlyMulticore(self,state):
#    slot = self.slots[0]
#    if state: 
#      slot['OnlyMulticore'] = 'True'
#    else:
#      slot['OnlyMulticore'] = 'False'

  def getState(self):
    slot = self.slots[0]
    return slot['State']

  def readNodeState (self):
    worked,code,report,err = runCommand ("condor_status -long " + self.name)
    if (worked != True):
      print 'WARNING in Node class, condor status command did not run for ',self.name
      return False
    if (code != 0):
      print 'WARNING in Node class, for node', self.name, ', condor status command gave return code ', code, ', stderr was ', err
      return False
    lines = string.split(report, '\n')

    slot_count = 0

    for l in lines:
      matchObj = re.match('^$',l)  
      if matchObj is not None:
        self.slots.append(self.current_slot)
        self.current_slot = {}
        slot_count = slot_count + 1
      else:
        halves = l.split(' = ')
        self.current_slot[halves[0]] = halves[1]
        if self.detectedCpus == 0 and halves[0] == 'DetectedCpus':
          self.detectedCpus = int(halves[1])
        if self.totalSlotCpus == 0 and halves[0] == 'TotalSlotCpus':
          self.totalSlotCpus = int(halves[1])
        if halves[0] == 'Cpus':   # When in first slot, how much is slack. When in later slots, how much is used.
          if int(halves[1]) >= 8:
            self.hasSlotWith8 = True

          if slot_count == 0:
            self.slack = self.slack + int(halves[1])
            if self.slack >= 8:
              self.hasSlackOf8 = True
          else:
            self.totalUsed = self.totalUsed + int(halves[1])  
    return True

#--- sub
def makeCmdTakeHold (node):
  worked,code,sout,serr = runCommand("condor_reconfig " + node)
  if ((worked != True) or (code != 0 ) ):
    print 'WARNING odd result in makeCmdTakeHold() for node ' + node 
    return False
  return True

#--- sub
def runCommand(cmd):
  worked = False
  statusCode = -99
  stdout_value = ''
  stderr_value = ''
  command=cmd.split(' ',1)
  try:
    p = subprocess.Popen([cmd ], stdout=subprocess.PIPE, shell=True)
    stdout_value, stderr_value = p.communicate()
    worked=True
    statusCode=p.returncode
  except Exception :
    worked=False
  return worked,statusCode,stdout_value, stderr_value

#--- sub
def listNodes():
  worked,code,report,err = runCommand ("condor_status -format '%s\n' Machine")
  if (worked != True):
    print 'ERROR in listNodes, condor status command did not run'
    sys.exit(1)
  if (code != 0):
    print 'ERROR in listNodes, condor status command gave return code ', code, ', stderr was ', err
    sys.exit(1)

  lines = string.split(report[0:-1], '\n')

  nodeNames = []
  for l in lines:
    nodeNames.append(l)

  nodeset = set(nodeNames)
  nodeNames = list(nodeset)
  nodeNames.sort()
  return nodeNames

#--- sub
def usage():
  print 'This program controls the drain rate on a condor server '
  print 'using a process controller.'
  print ''
  print 'The options to this program are:'
  print ' -s  --setpoint      250     setpoint value'
  print ' -n  --negdelay       61     negotiator delay'
  print ''

#--- sub
def initOptions(o):

  """ Sets the defaults and read the options """

  # Set defaults (not used)
  o['setpoint']      = 250
  o['negdelay']      = 61 

  # Read the options
  try:
    options, remainder = getopt.getopt(sys.argv[1:], 's:n:', 
      [ 'setpoint=','negdelay='])

  except getopt.GetoptError:
    usage(); sys.exit(1)

  if len(options) < 1:
    usage(); sys.exit(1)

  # Store the options
  for opt, arg in options:
    try:
      if opt in ('-s', '--setpoint'):
        o['setpoint'] =  int(arg)
      if opt in ('-n', '--negdelay'):
        o['negdelay'] =  int(arg)
    except ValueError:
      usage(); sys.exit(1)

#--- main

options = {}
initOptions(options)
setPoint = options['setpoint'] 
negDelay = options['negdelay'] 

q = Queue()

nodeList = []
for n in listNodes():
  node = Node(n)
  if (node.readNodeState()):
    nodeList.append(node)
if (len(nodeList) == 0):
  print 'ERROR in main, could find no nodes at all'
  sys.exit(1)

# Find any node which disallows single cores, while having
# 8 cores slack. For these, allow single cores, but only
# after waiting for one negotiator cycle
readyList = []
for n in nodeList:
  if(n.getOnlyMulticore()):
    if(n.getHasSlackOf8()):
      readyList.append(n)
if (len(readyList) > 0):
  time.sleep(negDelay)
for n in readyList:
  n.allowSinglecore()

mcq = q.getTotalMultiQueued()
scq = q.getTotalSingleQueued()
mcr = q.getTotalMultiJobsRunning()
scr = q.getTotalSingleJobsRunning()
print 'INFO mcq', mcq, ', scq', scq, ', mcr', mcr, ', scr', scr

if (mcq == 0 and scq == 0):
  print 'INFO Nothing in the queue, so do nothing.'
  sys.exit(0)
if (mcq > 0 and scq == 0):
  print 'INFO Only mcore in the queue, so do nothing.'
  sys.exit(0)
if (mcq == 0 and scq > 0):
  print 'INFO Only score in the queue, so make all nodes allow score.'
  for n in nodeList:
    n.allowSinglecore()
  sys.exit(0)
if (mcq >  0 and scq > 0):
  print 'INFO A mix of score and mcore in the queue, so this will need some judgement.'
  mcoreDesired = int(round(setPoint / 8.0))
  if (mcr >= mcoreDesired ):
    print 'INFO Already enough mcores running, so do nothing.'
    sys.exit(0)

  delta = mcoreDesired - mcr
  print 'INFO Would want to see ',delta,' nodes being prepared for mcore.'

  # We want to discount nodes that are OnlyMulticore but 
  # not yet with 8 cores of slack (or more)
  alreadyBeingPrepared = 0
  for n in nodeList:
    if(n.getOnlyMulticore()):
      if(n.getHasSlackOf8() == False):
        alreadyBeingPrepared = alreadyBeingPrepared + 1
  print 'INFO The are already ',alreadyBeingPrepared,' nodes being prepared for mcore.'
  delta = delta - alreadyBeingPrepared
  
  # Go over all the nodes and find a set (sized: delta)
  # where each node is:
  # a) without 8 cores of slack (at least) 
  # b) not OnlyMulticore
  # Make each OnlyMulticore

  newlyPreparing = 0
  for n in nodeList:
    if(n.getHasSlackOf8 () == False):
      if(n.getOnlyMulticore() == False):
        if (delta > 0):
          newlyPreparing = newlyPreparing + 1
          delta = delta - 1
          n.disallowSinglecore()
          print 'INFO Will prepare ',n.getName(),' for mcore.'

  print 'INFO Started to prepare ',newlyPreparing,' nodes for mcore.'
sys.exit(0)

