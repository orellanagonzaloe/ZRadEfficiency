#! /usr/bin/env python

import os
import argparse
import array
import yaml

def check_args(args):

	# under construction 

	return 0


parser = argparse.ArgumentParser()

parser.add_argument('--loop', dest='loop', action='store_true', default=False)
parser.add_argument('--inputFiles', dest='inputFiles', default=[], nargs='+')
parser.add_argument('--year', dest='year', default=None)
parser.add_argument('--nevents', dest='nevents', default=None)
parser.add_argument('--config', dest='config', default='ZRadEfficiency.yaml')
parser.add_argument('--outputDir', dest='outputDir', type = str, default='output')

parser.add_argument('--createSF', dest='createSF', action='store_true', default=False)

parser.add_argument('--plots', dest='plots', action='store_true', default=False)
parser.add_argument('--SFsDir', dest='SFsDir', type = str, default=None)
parser.add_argument('--outputPlotDir', dest='outputPlotDir', type = str, default=None)

args = parser.parse_args()

check_args(args)

with open(args.config, 'r') as f:
	cfg = yaml.safe_load(f)

cfg['inputFiles'] = args.inputFiles
cfg['year'] = args.year
cfg['config'] = args.config
cfg['outputDir'] = args.outputDir
cfg['nevents'] = args.nevents
cfg['SFsDir'] = args.SFsDir
cfg['outputPlotDir'] = args.outputPlotDir

if args.loop:
	import loop as lp
	lp.main(cfg)
elif args.createSF:
	import createSF as sf
	sf.main()
elif args.plots:
	import plots as pl
	pl.main(cfg)




