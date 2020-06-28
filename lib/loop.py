#! /usr/bin/env python

### contact: orellana.g@cern.ch, for any suggestion! ###

import os
import re
import sys
import yaml
import math
import ctypes
from array import array 


import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import *


with open('config.yaml', 'r') as f:
	cfg = yaml.safe_load(f)

syst_list = {
	
	'nominal': (0, 0, 0, 0, 0, 0),
	'llg_up' : (1, 1, 0, 0, 0, 0),
	'llg_dn' : (2, 2, 0, 0, 0, 0),
	'll_up'  : (0, 0, 1, 1, 0, 0),
	'll_dn'  : (0, 0, 2, 2, 0, 0),
	'l_ISO'  : (0, 0, 0, 0, 1, 0),
	'l_ID'   : (0, 0, 0, 0, 0, 1),
}


def main(inputFiles, year):

	### init ###

	if not os.path.exists('output/'):
		os.makedirs('output/')

	isData = False
	if any('data' in x for x in inputFiles):
		isData = True

	d_num_syst_tr = {}
	d_den_syst = {}
	d_num_syst_tr_1D = {}
	d_den_syst_tr_1D = {}
	for syst in syst_list:

		d_num_syst_tr[syst] = {}
		d_num_syst_tr_1D[syst] = {}
		d_den_syst_tr_1D[syst] = {}

		d_den_syst[syst] = ROOT.TH2D('h_den_syst_' + syst, 'h_den_syst_' + syst, len(cfg['et_binning'])-1, array('f', cfg['et_binning']), len(cfg['eta_binning'])-1, array('f', cfg['eta_binning']))
		d_den_syst[syst].Sumw2()

		for tr in cfg['trigger_list'][year]:

			d_num_syst_tr[syst][tr] = ROOT.TH2D('h_num_syst_tr_' + syst + '_' + tr, 'h_num_syst_tr_' + syst + '_' + tr, len(cfg['et_binning'])-1, array('f', cfg['et_binning']), len(cfg['eta_binning'])-1, array('f', cfg['eta_binning']))
			d_num_syst_tr[syst][tr].Sumw2()
			
			et_binning_1D = create_et_binning(tr)

			d_num_syst_tr_1D[syst][tr] = ROOT.TH1D('h_num_syst_tr_' + syst + '_' + tr + '_1D', 'h_num_syst_tr_' + syst + '_' + tr + '_1D', len(et_binning_1D)-1, array('f', et_binning_1D))
			d_num_syst_tr_1D[syst][tr].Sumw2()

			d_den_syst_tr_1D[syst][tr] = ROOT.TH1D('h_den_syst_tr_' + syst + '_' + tr + '_1D', 'h_den_syst_tr_' + syst + '_' + tr + '_1D', len(et_binning_1D)-1, array('f', et_binning_1D))
			d_den_syst_tr_1D[syst][tr].Sumw2()



	### loop in events ###

	chain = TChain('output')

	for file in inputFiles:
		chain.Add(file)

	nevents = chain.GetEntries()
	# nevents = 200000
	for entry in xrange(nevents):

		if entry % int(nevents/100) == 0:
			print_progressbar('', nevents, entry)

		chain.GetEntry(entry)

		llg_m = getattr(chain, 'llg.m')
		ll_m = getattr(chain, 'll.m')

		ph_pt = getattr(chain, 'ph.pt')
		ph_eta = getattr(chain, 'ph.eta2')

		ph_idtight = getattr(chain, 'ph.tight_AOD')

		if cfg['ph_ISO'] == 'FixedCutLoose':
			ph_ISO = getattr(chain, 'ph.isoloose')
		elif cfg['ph_ISO'] == 'FixedCutTight':
			ph_ISO = getattr(chain, 'ph.isotight')
		elif cfg['ph_ISO'] == 'FixedCutTightCaloOnly':
			ph_ISO = getattr(chain, 'ph.isotightcaloonly')

		d_match_tr = {}
		for tr in cfg['trigger_list'][year]:
			d_match_tr[tr] = getattr(chain, 'Trigger.'+tr+'_match_gamma_TEGMT')

		ph_pdgid = True
		if not isData:
			ph_pdgid = getattr(chain, 'ph.truth_pdgId')

		l1_ID = []
		l1_ID.append(getattr(chain, 'l1.medium_id'))
		l1_ID.append(getattr(chain, 'l1.tight_id'))
		# l1_ID.append(getattr(chain, 'l1.loose_id'))

		l2_ID = []
		l2_ID.append(getattr(chain, 'l2.medium_id'))
		l2_ID.append(getattr(chain, 'l2.tight_id'))
		# l2_ID.append(getattr(chain, 'l2.loose_id'))

		l1_ISO = []
		l1_ISO.append(getattr(chain, 'l1.isoloose'))
		l1_ISO.append(getattr(chain, 'l1.isotight'))

		l2_ISO = []
		l2_ISO.append(getattr(chain, 'l2.isoloose'))
		l2_ISO.append(getattr(chain, 'l2.isotight'))


		for s in syst_list:

			if	llg_m>cfg['llg_m_Min'][syst_list[s][0]] and llg_m<cfg['llg_m_Max'][syst_list[s][1]] and \
				ll_m>cfg['ll_m_Min'][syst_list[s][2]] and ll_m<cfg['ll_m_Max'][syst_list[s][3]]     and \
				l1_ID[syst_list[s][5]] and l1_ISO[syst_list[s][4]] and l2_ID[syst_list[s][5]] and l2_ISO[syst_list[s][4]] and\
				ph_ISO and ph_idtight and \
				ph_pdgid:

				d_den_syst[s].Fill(ph_pt, abs(ph_eta))

				for tr in cfg['trigger_list'][year]:

					d_den_syst_tr_1D[s][tr].Fill(ph_pt/1000.)

					if d_match_tr[tr]:

						d_num_syst_tr_1D[s][tr].Fill(ph_pt/1000.)
						d_num_syst_tr[s][tr].Fill(ph_pt, abs(ph_eta))



	### output file ###

	data_mc = {True: 'data', False: 'MC'}
	filename = 'output/loop_output_%s_%s.root' % (data_mc[isData], year)
	outputfile = ROOT.TFile(filename, 'RECREATE')

	for s in syst_list:

		d_den_syst[s].Write()

		for tr in cfg['trigger_list'][year]:

			d_den_syst_tr_1D[s][tr].Write()
			d_num_syst_tr_1D[s][tr].Write()
			d_num_syst_tr[s][tr].Write()

	outputfile.Close()

	print '%s was created' % filename


def print_progressbar(name, total, progress):

	bar_length, status = 50, ''
	progress = float(progress) / float(total)
	if progress >= 1.:
		progress, status = 1, '\r\n'
	block = int(round(bar_length * progress))
	text = '\rProcessing {:2}  [{}] {:.0f}% {}'.format(name, '#' * block + '-' * (bar_length - block), round(progress * 100, 0), status)
	sys.stdout.write(text)
	sys.stdout.flush()


def create_et_binning(triger):

	tr_to = get_trigger_threshold(triger)

	et_binning = []

	et_binning.append(tr_to-8.)
	et_binning.append(tr_to-5.)

	for i in xrange(10):
		et_binning.append( et_binning[-1] + 1.)
	for i in xrange(2):
		et_binning.append( et_binning[-1] + 3.)
	for i in xrange(3):
		et_binning.append( et_binning[-1] + 5.)
	for i in xrange(3):
		et_binning.append( et_binning[-1] + 10.)
	for i in xrange(3):
		et_binning.append( et_binning[-1] + 20.)
	et_binning.append(500.5)


	return et_binning



def get_trigger_threshold(trigger):

	threshold = int(re.findall(r'_g.+?_', trigger)[0].split('_')[1].replace('g',''))
	
	return threshold
