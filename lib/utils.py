import sys
import array

import ROOT
ROOT.gROOT.SetBatch(True)


def printProgressbar(name, total, progress):

	bar_length, status = 50, ''
	progress = float(progress) / float(total)
	if progress >= 1.:
		progress, status = 1, '\r\n'
	block = int(round(bar_length * progress))
	text = '\rProcessing {:2}  [{}] {:.0f}% {}'.format(name, '#' * block + '-' * (bar_length - block), round(progress * 100, 0), status)
	sys.stdout.write(text)
	sys.stdout.flush()


def createHist(hname, binning):

	var2D = False
	if all(isinstance(i, list) for i in binning):
		var2D = True

	if var2D:
		xarray = array.array('f', binning[0])
		yarray = array.array('f', binning[1])
	else:
		xarray = array.array('f', binning)

	if var2D:
		h_tmp = ROOT.TH2D(hname, hname, len(xarray)-1, xarray, len(yarray)-1, yarray)
	else:
		h_tmp = ROOT.TH1D(hname, hname, len(xarray)-1, xarray)

	h_tmp.SetDirectory(0)
	h_tmp.Sumw2()

	return h_tmp

def createHistDictionary(cfg):

	d_all_hist = {}

	for syst in cfg['systMap']:

		d_all_hist[syst] = {}

		for tr in cfg['triggerList'][cfg['year']]:

			d_all_hist[syst][tr] = {}

			for variable in cfg['variables']:

				d_all_hist[syst][tr][variable] = {}
		
				for _type in ['num', 'den']:

					_variable = variable.replace(':', '_')

					hname = 'h_%s_%s_%s_%s' % (syst, tr, _variable, _type)

					binning = cfg['binning'][variable]

					if binning == 'smart':
						binning = smartEtBinning(tr)

					d_all_hist[syst][tr][variable][_type] = createHist(hname, binning)

	return d_all_hist

def writeOutput(cfg, filename, d_all_hist):

	outputfile = ROOT.TFile(filename, 'RECREATE')

	for syst in cfg['systMap']:

		for tr in cfg['triggerList'][cfg['year']]:

			for variable in cfg['variables']:
		
				for _type in ['num', 'den']:

					d_all_hist[syst][tr][variable][_type].Write()

	outputfile.Close()

	printMsg('Created file: %s' % (filename), 0)

def smartEtBinning(triger):

	tr_to = getTriggerThreshold(triger)

	et_binning = []

	et_binning.append(tr_to-8.)
	et_binning.append(tr_to-5.)

	for i in range(10):
		et_binning.append( et_binning[-1] + 1.)
	for i in range(2):
		et_binning.append( et_binning[-1] + 3.)
	for i in range(3):
		et_binning.append( et_binning[-1] + 5.)
	for i in range(3):
		et_binning.append( et_binning[-1] + 10.)
	for i in range(3):
		et_binning.append( et_binning[-1] + 20.)
	et_binning.append(500.5)


	return et_binning


def getTriggerThreshold(trigger):

	# threshold = int(re.findall(r'_g.+?_', trigger)[0].split('_')[1].replace('g',''))

	threshold = int(trigger.split('_')[1].replace('g',''))
	
	return threshold


def getSystValue(syst, var, cfg):

	try:
		return cfg['systMap'][syst][var]
	except:
		return cfg['systMap']['nominal'][var]


def printMsg(msj, level):

	color = ['[1;92mINFO', '[1;93mWARNING', '[1;91mERROR']

	print('\033%s: %s\033[0m' % (color[level], msj))


def isData(inputFiles):

	isData = False # Fix TODO
	if any('data' in x for x in inputFiles):
		isData = True