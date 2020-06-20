#! /usr/bin/env python

import os
import argparse
import array

def check_args(args):

	# under construction 

	return 0


parser = argparse.ArgumentParser()

parser.add_argument('--loop', dest='loop', action='store_true', default=False)
parser.add_argument('--inputFiles', dest='inputFiles', default=[], nargs='+')
parser.add_argument('--year', dest='year', default=None)

parser.add_argument('--createSF', dest='createSF', action='store_true', default=False)

parser.add_argument('--plots', dest='plots', action='store_true', default=False)
parser.add_argument('--SFsDir', dest='SFsDir', type = str, default=None)
parser.add_argument('--outputPlotDir', dest='outputPlotDir', type = str, default=None)

args = parser.parse_args()

check_args(args)

inputFiles = args.inputFiles
year = args.year

loop = args.loop
createSF = args.createSF
plots = args.plots

SFsDir = args.SFsDir
outputPlotDir = args.outputPlotDir

for i in inputFiles:
	if i[-1] != '/':
		i += '/'

if SFsDir is not None and SFsDir[-1] != '/':
	SFsDir += '/'
if outputPlotDir is not None and outputPlotDir[-1] != '/':
	outputPlotDir += '/'


if loop:
	import lib.loop as lp
	lp.main(inputFiles, year)
elif createSF:
	import lib.createSF as sf
	sf.main()
elif plots:
	import lib.plots as pl
	pl.main(SFsDir, outputPlotDir)




