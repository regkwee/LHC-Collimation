#!/usr/bin/python
#
#
#
# R Kwee-Hinzmann, October 2013 
# ----------------------------------------------------------------------------------------------------------------------
import os, stat, sys, shutil, re
import optparse
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-r", dest="rundir", type="string",
                      help="put rundir in which file are to be merged")

parser.add_option("-s", dest="scoringType", type="string",
                      help="put scoringtype usrtrack, usrbin or usrbdx")

parser.add_option("-u", dest="unit", type="string",
                      help="put corresponding fluka unit. if several seperate by ,")

(options, args) = parser.parse_args()

rundir = options.rundir
if not rundir.endswith('/'): rundir += '/'
scoringType = options.scoringType
unit = options.unit
# ----------------------------------------------------------------------------------------------------------------------
# define run files and parameters
debug      = 1
doRun      = 1

flukatool  = ''
flukapath  = '/afs/cern.ch/work/r/rkwee/Fluka/fluka20112blinuxAA/'
if scoringType.count('usrbin'):   flukatool   = flukapath + 'flutil/usbsuw'
elif scoringType.count('usrtrk'): flukatool   = flukapath + 'flutil/ustsuw'
elif scoringType.count('usrbdx'): flukatool   = flukapath + 'flutil/usxsuw'
elif scoringType.count('text'):   flukatool   = ''

# flukanumbers
flukaNumber = [i for i in unit.split(',')]    
# ----------------------------------------------------------------------------------------------------------------------
def ListFortFiles(fn):
    
    # create a list with all fortfile to be merged, ie per flukanumber!
    allfortfiles = []
    
    # get all sub dirs like run_12345
    alldirs = os.listdir(rundir)

    # for each subrundir 
    for adir in alldirs:

        if not os.path.isdir(rundir+adir): continue

        # all file in each subrundir
        filesInAdir = os.listdir(rundir+adir)

        for afile in filesInAdir:

            if not afile.endswith("_fort." + fn): continue
            allfortfiles += [rundir + adir +'/' + afile]
    
    # remove the last 3 characters as they indicate the cycle number
    #   example of file: ir1_4TeV_settings_from_TWISS_b2001_fort.53
    onefile = allfortfiles[-1].split('/')[-1]
    onefile = onefile.split('_fort')[0]
    onefile = onefile.rstrip(onefile[-3:])

    # per fn return a list
    return allfortfiles, onefile
# ----------------------------------------------------------------------------------------------------------------------
def joinTextFiles(fn):
    # all subfiles are joined replacing the first colum (first 8 characters) by runnumber and cyclenumber

    allfortfiles,inpfile = ListFortFiles(fn)
    
    foutname = rundir + inpfile + '_' + fn 
    fout     = open(foutname, 'w')

    for afile in allfortfiles:

        if not afile.count("run"): continue
        runnumber   = afile.split('run_')[-1].split('/')[0]
        cyclenumber = afile.split('/')[-1].split('b2')[-1].split('_fort.' + fn)[0]
        # print("for file", afile, "found runnumber ", runnumber, ' and cyclenumber', cyclenumber)

        with open(afile) as af:

            for line in af:
                #line = line.rstrip()
                outline  = runnumber + cyclenumber + '  ' + line[9:]

                fout.write(outline)

    fout.close()

    print("Wrote " + foutname)

    return foutname
# ----------------------------------------------------------------------------------------------------------------------
def mergeFortfiles():

    if scoringType == 'text':

        for fn in flukaNumber: joinTextFiles(fn)

    return


    for fn in flukaNumber:

        allfortfiles,inpfile = ListFortFiles(fn)

        fdummy   = rundir + inpfile + '_' + fn + '.dummy'
        foutname = rundir + inpfile + '_' + fn 

        fout     = open(fdummy, 'w')

        for afile in allfortfiles: fout.write(afile +"\n")

        # add a newline
        fout.write("\n")

        # add filename of merged file. IMPORTANT: add newline
        fout.write(foutname + '\n')

        fout.close()

        # create the merged binary
        cmd = flukatool + ' < ' + fdummy
        print cmd
        
        if doRun:
            os.system(cmd)            

    
# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    mergeFortfiles()
