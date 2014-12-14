# ---------------------------------------------
# Read, write and manipulate LAMMPS dump file
# Read one or several snapshots at a time
# ---------------------------------------------

# NEED NUMPY 
import numpy as np
import sys
import os

#
# class dump
#   class readSnap : (element module) for read single snapshot from dump file
#   class getSnap: return certain snapshots 
#   class tselect : given a timesteps array, get the position of each timesteps in the dump file(using class picktime)
#   class nextSnap : read next snapshot according to the given timesteps array
#   class gettime : get all the timesteps from the dump file
#   (not implemented)class snapdelete: delete snapshot of certain timestep and save to another file
#   class tdelete: delete certain timesteps of tpocdic and timeselect
#   class tadd: add certain timesteps into tpocdic and timeselect
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
# self.timesteps = list of all timesteps in the dump file
# self.timeselect = list of selected timesteps
#
# Usage:
# d = dump("dump.txt")
# d.gettime()
# d.timesteps  # get all timesteps in the dump file
# t = [0,500,20000]    # say we want to get the snapshots of timestep 0 500 and 20000
# d.tselect(t)    # get the position of all wanted timesteps in the dump file and store th positions in self.tpocdic
# d.nextSnap()    # read the timestep 0, store the snapshot in the self.snaps
# d.nextSnap()    # read the timestep 500
# d.nextSnap()    # read the timestep 20000


class dump:

    # -------------------------------------
    def __init__(self,*args):
        self.tpocdic = {}
        self.timesteps = []
        self.nottimeselect = []
        self.timeselect = []

        if len(args) == 0: raise StandardError("***** Error: specify dump file *****")
        self.file = args[0]
        if not os.path.exists(self.file): raise StandardError("***** Error: No such file *****")

    # -----------------------------------
    def nextSnap(self):
        with open(self.file) as f:
            try:
                f.seek(self.tpocdiciter.next())
                return self.readSnap(f)
            except:
                print "Reach the last snapshot"
                return 0
                raise

    # -----------------------------------
    def getSnap(self,*args):
        snaps = []
        if len(args) == 0:
            raise StandardError('***** Error: Please provide timesteps argument*****')
        elif len(args) == 1:
            t = args[0]
        else:
            raise StandardError('***** Error: Number of argument is larger than 1. Please check *****')

        if t == 'all':
            with open(self.file) as f:
                for value in self.timeselect:
                    f.seek(self.tpocdic[value])
                    snaps.append(self.readSnap(f))
        else:
            if isinstance(t,int) or isinstance(t,np.ndarray) or isinstance(t,list):
                tgetlst = np.array([t])
                tgetlst = tgetlst.flatten()
                if 'int' not in str(tgetlst.dtype):
                    raise ValueError("***** Error: all the elements in t should be integer *****")
            else:
                raise ValueError("***** Error: selected t should be an integer, python list or numpy array *****")

            with open(self.file) as f:
                for value in tgetlst:
                    try:
                        f.seek(self.tpocdic[value])
                        snaps.append(self.readSnap(f))
                    except KeyError:
                        print '***** Timestep {} not found, first use tselect method to initialize *****'.format(value)
                        pass


        if len(snaps) == 0:
            raise StandardError('***** Timestep not found, first use tselect method to initialize *****')
        elif len(snaps) == 1:
            return snaps[0]
        else:
            return snaps

    # -----------------------------------
    # t can a integer, python list or numpy array
    def tselect(self,t):
        # renew the tpocdic
        self.tpocdic = {}
        if isinstance(t,int) or isinstance(t,np.ndarray) or isinstance(t,list):
            self.timeselect = np.array([t])
            self.timeselect = self.timeselect.flatten()
            unorder_timeselect = np.copy(self.timeselect)
            self.timeselect.sort()
            if 'int' not in str(self.timeselect.dtype):
                raise ValueError("***** Error: all the elements in t should be integer *****")
        else:
            raise ValueError("***** Error: selected t should be an integer, python list or numpy array *****")
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
            print "***** Error: no timestep is selected because there are no corresponding timesteps in dump file *****"
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
                if 'int' not in str(tdellst.dtype):
                    raise ValueError("***** Error: timesteps should be integer *****")
            else:
                raise ValueError("***** Error: delected t should be an integer, python list or numpy array *****")
            
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
    # tadd class
    # add certain timesteps to tpocdic and tpocdiciter
    def tadd(self,t):
        if isinstance(t,int)  or isinstance(t,np.ndarray) or isinstance(t,list):
            taddlst = np.array([t])
            taddlst = taddlst.flatten()
            if 'int' not in str(taddlst.dtype):
                raise ValueError("***** Error: timesteps should be integer *****")
        else:
            raise ValueError("***** Error: added t should an integer,python list or numpy array *****")

        # first check duplicate
        duplicate = np.intersect1d(self.timeselect,t)
        t = np.delete(t,np.searchsorted(t,duplicate))
        t_temp = t

        # add t into tpocdic
        index = np.searchsorted(self.timeselect,t) - 1
        with open(self.file) as f:
            for i in index:
                if i == -1:
                    pass
                else:
                    f.seek(self.tpocdic[self.timeselect[i]])
                check = False
                t_poc, t_poc_temp = 0, 0
                fiter = iter(f.readline,'')
                for i, line in enumerate(fiter,start=0):
                    if check:
                        time = int(line.split()[0])
                        if time == t[0]:
                            self.tpocdic[time] = t_poc
                            t = np.delete(t,0)
                            break
                        check = False
                    else:
                        if line == 'ITEM: TIMESTEP\n':
                            check = True
                    t_poc = t_poc_temp
                    t_poc_temp = f.tell()

        # update tpocdiciter
        temp_tpocdiciter = list(self.tpocdiciter)
        for value in t_temp:
            temp_tpocdiciter.append(self.tpocdic[value])
        self.tpocdiciter = iter(temp_tpocdiciter)

        # update timeselect
        self.timeselect = np.insert(self.timeselect,index + 1,t_temp)


    # -----------------------------------
    def gettime(self):
        check = False
        with open(self.file) as f:
            for i, line in enumerate(f):
                if check:
                    self.timesteps.append(int(line.split()[0]))
                    check = False
                else:
                    if line == 'ITEM: TIMESTEP\n':
                        check = True
        self.timesteps = np.array(self.timesteps)

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
        snap.atoms = np.float_(snap.atoms)
        snap.box = np.array(snap.box)
        return snap

class Snap:
    pass