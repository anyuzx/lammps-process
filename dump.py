#
# Read, write and manipulate LAMMPS dump file
# Read one or several snapshots at a time
#

# NEED NUMPY 
import numpy as np
import sys
import os

#
# class dump
#   class readSnap : (element module) for read single snapshot from dump file
#   class readSnaps : given a timesteps array, read snapshots of those timesteps and store snapshots in snaps
#   class picktime : (element module) given a timesteps array, get the postition of each snapshot in the dump file
#   class tselect : given a timesteps array, get the position of each timesteps in the dump file(using class picktime)
#   class nextSnap : read next snapshot according to the given timesteps array
#   class gettime : get all the timesteps from the dump file
#   class snapdelete: delete snapshot of certain timestep and save to another file
#   class tdelete: delete certain timesteps of tpocdic and timeselect
#
#
# self.snaps   list of snapshots
#   time = time step
#   boundary = boundary string list 
#   box = box dimension array
#   natoms = # of atoms
#   atoms = atoms array
#   descriptor = atoms attributes list
# self.file = dump file
# self.tpocdic = list of position of timesteps in the dump file
# self.tpocdiciter = iterator object of self.tpocdic
# self.timearray = list of all timesteps in the dump file
# self.timeselect = list of selected timesteps
#
# Usage:
# d = dump("dump.txt")
# d.gettime()
# d.timearray  # get all timesteps in the dump file
# t = [0,500,20000]    # say we want to get the snapshots of timestep 0 500 and 20000
# d.readSnaps(t)    # store all the wanted snapshots in list self.snaps
# d.tselect(t)    # get the position of all wanted timesteps in the dump file and store th positions in self.tpocdic
# d.nextSnap()    # read the timestep 0, store the snapshot in the self.snaps
# d.nextSnap()    # read the timestep 500
# d.nextSnap()    # read the timestep 20000
# self.snaps will always contain one snapshot when using nextSnap() method


class dump:

    # -------------------------------------

    def __init__(self,*args):
        self.snaps = []
        self.tpocdic = {}
        self.timearray = []
        self.nottimeselect = []
        self.timeselect = []

        if len(args) == 0: raise StandardError("specify dump file")
        self.file = args[0]
        if not os.path.exists(self.file): raise StandardError("No such file")

    # ------------------------------------

    # t can be an integer, python list or numpy array
    # Ex.
    # To get the timesteps 0 500 20000
    # readSnaps([0,500,20000])
    def readSnaps(self):
        with open(self.file) as f:
            for item in self.tpocdiciter:
                f.seek(item)
                self.snaps.append(self.readSnap(f))

    # -----------------------------------
    def nextSnap(self):
        self.snaps = [] 
        with open(self.file) as f:
            try:
                f.seek(self.tpocdiciter.next())
                self.snaps.append(self.readSnap(f))
                return 1
            except:
                print "reach the last snapshot"
                return 0
                raise

    # -----------------------------------
    # t can a integer, python list or numpy array
    def tselect(self,t):
        # renew the tpocdic
        self.tpocdic = {}
        if isinstance(t,int) or isinstance(t,np.ndarray) or isinstance(t,list):
            self.timeselect = np.array([t])
            self.timeselect = self.timeselect.flatten()
            unorder_timeselect = self.timeselect
            self.timeselect.sort()
            if 'int' not in str(self.timeselect.dtype):
                raise ValueError("all the elements in t should be integer")
        else:
            raise ValueError("selected t should be an integer, python list or numpy array")
        t_array = self.timeselect
        check = False
        t_poc, t_poc_temp = 0, 0
        with open(self.file) as f:
            fiter = iter(f.readline,'')
            for i, line in enumerate(fiter,start=0):
                if check:
                    time = int(line.split()[0])
                    if time == t_array[0]:
                        self.tpocdic[time] = t_poc
                        t_array = np.delete(t_array,0)
                        if len(t_array) == 0:
                            self.tpocdiciter = iter([self.tpocdic[value] for value in unorder_timeselect])
                            break
                    check = False
                else:
                    if line == 'ITEM: TIMESTEP\n':
                        check = True
                t_poc = t_poc_temp
                t_poc_temp = f.tell()
        if len(self.tpocdic) == 0:
            print "no timestep is selected because there are no corresponding timesteps in dump file"
        else:
            if len(t_array) > 0:
                self.nottimeselect = t_array
                print "The following timesteps are not selected because there are no corresponding timesteps in dump file"
                print t_array
                print "check instance self.nottimeselect"

    # -----------------------------------
    # tdelete class
    # delete certain selected timesteps from self.tpocdic
    def tdelete(self,t):
    	if len(self.tpocdic) == 0:
    		print "No timestep has been selected"
    	else:
    		if isinstance(t,int) or isinstance(t,np.ndarray) or isinstance(t,list):
    			tdellst = np.array([t])
    			tdellst = tdellst.flatten()
    			tdellst.sort()
    			if 'int' not in str(self.timeselect.dtype):
    				raise ValueError("timesteps should be integer")
    		else:
    			raise ValueError("delected t should be an integer, python list or numpy array")
    		
    		# update the tpocdiciter
    		temp_tpocdiciter = list(self.tpocdiciter)
    		for value in tdellst:
    			try:
    				temp_tpocdiciter.remove(self.tpocdic[value])
    			except ValueError:
    				pass
    		self.tpocdiciter = iter(temp_tpocdiciter)

    		# delete timesteps from tpocdic
    		for i in tdellst:
    			try:
    				del self.tpocdic[i]
    			except KeyError:
    				print 'Skip timestep {} because there is no one'.format(int(i))

    # -----------------------------------
    def gettime(self):
        check = False
        with open(self.file) as f:
            for i, line in enumerate(f):
                if check:
                    self.timearray.append(int(line.split()[0]))
                    check = False
                else:
                    if line == 'ITEM: TIMESTEP\n':
                        check = True
        self.timearray = np.array(self.timearray)

    # -------------------------------------
    # read a single snapshot
    # return snap
    # snap has its own instances as following
    # time = timestep
    # box = box dimension array
    # boundary = boundary string list
    # natoms = # of atoms
    # atoms = atoms array
    # descriptor = atoms attributes list
    def readSnap(self,f):
        snap = Snap()
        snap.time = 0
        snap.box = []
        snap.atoms = []
        snap.natoms = 0
        for i, line in enumerate(f):
            if i > 8 and i < 8 + snap.natoms:
                snap.atoms.append(line.split())
            elif i == 3:
                snap.natoms = int(line.split()[0])
            elif i == 5 or i == 6 or i == 7:
                snap.box.append(np.float_(line.split()))
            elif i == 4:
                if len(line.split()) == 3:
                    snap.boundary = []
                else:
                    snap.boundary = line.split()[3:-1]
            elif i == 8:
                snap.descriptor = line.split()[2:-1]
            elif i == 1:
                snap.time = int(line.split()[0])
            elif i == 8 + snap.natoms:
                snap.atoms.append(line.split())
                break
        snap.box = np.array(snap.box)
        return snap

class Snap:
    pass