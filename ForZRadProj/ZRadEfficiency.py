#! /usr/bin/env python

### contact: orellana.g@cern.ch, for any suggestion! ###

import os
import argparse
import re
import sys
import yaml
import math
import ctypes
from array import array 

import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import *

with open('ZRadEfficiency.yaml', 'r') as f:
	cfg = yaml.safe_load(f)

def loop(inputFiles, year):

	### init ###

	if not os.path.exists('output/'):
		os.makedirs('output/')

	isData = False
	if any('data' in x for x in inputFiles):
		isData = True

	d_num_syst_tr = {}
	d_den_syst = {}
	for syst in cfg['syst_list']:

		d_num_syst_tr[syst] = {}

		d_den_syst[syst] = ROOT.TH2D('h_den_syst_' + syst, 'h_den_syst_' + syst, len(cfg['et_binning'])-1, array('f', cfg['et_binning']), len(cfg['eta_binning'])-1, array('f', cfg['eta_binning']))
		d_den_syst[syst].Sumw2()

		for tr in cfg['trigger_list'][year]:

			d_num_syst_tr[syst][tr] = ROOT.TH2D('h_num_syst_tr_' + syst + '_' + tr, 'h_num_syst_tr_' + syst + '_' + tr, len(cfg['et_binning'])-1, array('f', cfg['et_binning']), len(cfg['eta_binning'])-1, array('f', cfg['eta_binning']))
			d_num_syst_tr[syst][tr].Sumw2()
			


	### loop in events ###

	chain = TChain('output')

	for file in inputFiles:
		chain.Add(file)

	nevents = chain.GetEntries()

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
		# l1_ID.append(getattr(chain, 'l1.loose_id')) # not used 

		l2_ID = []
		l2_ID.append(getattr(chain, 'l2.medium_id'))
		l2_ID.append(getattr(chain, 'l2.tight_id'))
		# l2_ID.append(getattr(chain, 'l2.loose_id')) # not used

		l1_ISO = []
		l1_ISO.append(getattr(chain, 'l1.isoloose'))
		l1_ISO.append(getattr(chain, 'l1.isotight'))

		l2_ISO = []
		l2_ISO.append(getattr(chain, 'l2.isoloose'))
		l2_ISO.append(getattr(chain, 'l2.isotight'))


		for s in cfg['syst_list']:

			if	llg_m>cfg['llg_m_Min'][cfg['syst_list'][s][0]] and llg_m<cfg['llg_m_Max'][cfg['syst_list'][s][1]] and \
				ll_m>cfg['ll_m_Min'][cfg['syst_list'][s][2]] and ll_m<cfg['ll_m_Max'][cfg['syst_list'][s][3]]     and \
				l1_ID[cfg['syst_list'][s][5]] and l1_ISO[cfg['syst_list'][s][4]] and l2_ID[cfg['syst_list'][s][5]] and l2_ISO[cfg['syst_list'][s][4]] and\
				ph_ISO and ph_idtight and \
				ph_pdgid:

				d_den_syst[s].Fill(ph_pt, abs(ph_eta))

				for tr in cfg['trigger_list'][year]:

					if d_match_tr[tr]:

						d_num_syst_tr[s][tr].Fill(ph_pt, abs(ph_eta))



	### output file ###

	data_mc = {True: 'data', False: 'MC'}
	filename = 'output/loop_output_%s_%s.root' % (data_mc[isData], year)
	outputfile = ROOT.TFile(filename, 'RECREATE')

	for s in cfg['syst_list']:

		d_den_syst[s].Write()

		for tr in cfg['trigger_list'][year]:

			d_num_syst_tr[s][tr].Write()

	outputfile.Close()

	print '%s was created' % filename


def SFs():

	if not os.path.exists('SFs/'):
		os.makedirs('SFs/')

	for yr in ['2015', '2016', '2017', '2018']:
		for sam in ['data', 'MC']:

			createEff(yr, sam)

		createSF(yr)


def createEff(year, sam):

	### read output ###

	filename = 'output/loop_output_%s_%s.root' % (sam, year)
	inputfile = ROOT.TFile(filename, 'READ')

	d_den_syst = {}
	d_num_syst_tr = {}
	for syst in cfg['syst_list']:

		d_den_syst[syst] = inputfile.Get('h_den_syst_' + syst)
		d_den_syst[syst].SetDirectory(0)

		d_num_syst_tr[syst] = {}

		for tr in cfg['trigger_list'][year]:

			d_num_syst_tr[syst][tr] = inputfile.Get('h_num_syst_tr_' + syst + '_' + tr)
			d_num_syst_tr[syst][tr].SetDirectory(0)

	
	### setup eff histograms

	h_num_bin = ROOT.TH1D('h_num_bin', 'title', 1, 0, 1)
	h_den_bin = ROOT.TH1D('h_den_bin', 'title', 1, 0, 1)
	h_num_bin.Sumw2()
	h_den_bin.Sumw2()

	h_eff_tr = {}
	h_eff_tr_1D = {}
	for syst in cfg['syst_list']:

		h_eff_tr[syst] = {}
		h_eff_tr_1D[syst] = {}

		for tr in cfg['trigger_list'][year]:


			h_eff_tr[syst][tr] = ROOT.TH2D( 'h_eff_syst_tr_' + syst + '_' + tr, 'h_eff_syst_tr_' + syst + '_' + tr, len(cfg['et_binning'])-1, array('f', cfg['et_binning']), len(cfg['eta_binning'])-1, array('f', cfg['eta_binning']))
			h_eff_tr[syst][tr].SetDirectory(0)
			h_eff_tr[syst][tr].Sumw2()


			for et in xrange(1, len(cfg['et_binning'])):
				for eta in xrange(1, len(cfg['eta_binning'])):

					num = d_num_syst_tr[syst][tr].GetBinContent(et, eta)
					den = d_den_syst[syst].GetBinContent(et, eta)

					if num == 0.:
						h_eff_tr[syst][tr].SetBinContent(et, eta, 0.)
						h_eff_tr[syst][tr].SetBinError(et, eta, 0.)
						continue

					h_num_bin.SetBinContent(1, num)
					h_den_bin.SetBinContent(1, den)
					h_num_bin.SetBinError(1, d_num_syst_tr[syst][tr].GetBinError(et, eta))
					h_den_bin.SetBinError(1, d_den_syst[syst].GetBinError(et, eta))

					x = ctypes.c_double(0.)
					y = ctypes.c_double(0.)
					eff_tmp = ROOT.TGraphAsymmErrors()
					eff_tmp.Divide(h_num_bin, h_den_bin, 'cl=0.683 b(0.5,0.5) mode')
					eff_tmp.GetPoint(0, x, y)

					h_eff_tr[syst][tr].SetBinContent(et, eta, y.value)
					h_eff_tr[syst][tr].SetBinError(et, eta, eff_tmp.GetErrorYlow(0)) # TH2 cannot store asymmetric errors, so we only use the lower error considering is always the greater

	inputfile.Close()


	### including systematics errors ###


	for syst in cfg['syst_list']:

		if syst == 'nominal': continue

		for tr in cfg['trigger_list'][year]:

			for et in xrange(1, len(cfg['et_binning'])):
				for eta in xrange(1, len(cfg['eta_binning'])):

					old_error = h_eff_tr['nominal'][tr].GetBinError(et, eta)

					diff = h_eff_tr[syst][tr].GetBinContent(et, eta) - h_eff_tr['nominal'][tr].GetBinContent(et, eta)

					new_error = math.sqrt(old_error**2 + diff**2) # syst is square difference with nominal

					h_eff_tr['nominal'][tr].SetBinError(et, eta, new_error)


	### eff output file ###

	for tr in cfg['trigger_list'][year]:

		if sam == 'data': sam = ''

		filename_eff = 'SFs/efficiency%s.%s.%s.%s.root' % (sam, tr, cfg['ph_ISO'], year)
		outputfile_eff = ROOT.TFile(filename_eff, 'RECREATE')
		outputdir_eff = outputfile_eff.mkdir(cfg['run_range'][year])
		outputdir_eff.cd() 

		h_eff_tr['nominal'][tr].SetName('FullSim_sf')
		h_eff_tr['nominal'][tr].SetTitle('FullSim_sf')

		h_eff_tr['nominal'][tr].Write('FullSim_sf')

		outputfile_eff.Close()

		print '%s was created' % filename_eff


def createSF(year):


	for tr in cfg['trigger_list'][year]: 

		filename_MC = 'SFs/efficiencyMC.%s.%s.%s.root' % (tr, cfg['ph_ISO'], year)
		inputfile_MC = ROOT.TFile(filename_MC, 'READ')

		h_MC = inputfile_MC.Get('%s/FullSim_sf' % cfg['run_range'][year])
		h_MC.SetDirectory(0)


		filename_data = 'SFs/efficiency.%s.%s.%s.root' % (tr, cfg['ph_ISO'], year)
		inputfile_data = ROOT.TFile(filename_data, 'READ')

		h_data = inputfile_data.Get('%s/FullSim_sf' % cfg['run_range'][year])
		h_data.SetDirectory(0)



		h_SF = ROOT.TH2D('h_SF', 'h_SF', len(cfg['et_binning'])-1, array('f', cfg['et_binning']), len(cfg['eta_binning'])-1, array('f', cfg['eta_binning']))
		h_SF.Sumw2()


		for et in xrange(1, len(cfg['et_binning'])):
			for eta in xrange(1, len(cfg['eta_binning'])):

				if 	(cfg['eta_binning'][eta-1] >= 1.37 and cfg['eta_binning'][eta-1]< 1.52) or \
					(h_SF.GetXaxis().GetBinLowEdge(et+1) <= 1000.*get_trigger_threshold(tr)):

					h_SF.SetBinContent(et, eta, 1.)
					h_SF.SetBinError(et, eta, 1.)
					continue

				x  = h_data.GetBinContent(et, eta)
				dx = h_data.GetBinError(et, eta)
				y  = h_MC.GetBinContent(et, eta)
				dy = h_MC.GetBinError(et, eta)

				h_SF.SetBinContent(et, eta, x/y)

				error = (x/y)*math.sqrt( (dy/y)**2 + (dx/x)**2 )

				h_SF.SetBinError(et, eta, error)


		filename_SF = 'SFs/efficiencySF.%s.%s.%s.root' % (tr, cfg['ph_ISO'], year)
		outputfile_SF = ROOT.TFile(filename_SF, 'RECREATE')
		outputdir_SF = outputfile_SF.mkdir(cfg['run_range'][year])
		outputdir_SF.cd() 

		h_SF.SetName('FullSim_sf')
		h_SF.SetTitle('FullSim_sf')

		h_SF.Write('FullSim_sf')

		outputfile_SF.Close()

		print '%s was created' % filename_SF


def print_progressbar(name, total, progress):

	bar_length, status = 50, ''
	progress = float(progress) / float(total)
	if progress >= 1.:
		progress, status = 1, '\r\n'
	block = int(round(bar_length * progress))
	text = '\rProcessing {:2}  [{}] {:.0f}% {}'.format(name, '#' * block + '-' * (bar_length - block), round(progress * 100, 0), status)
	sys.stdout.write(text)
	sys.stdout.flush()


def get_trigger_threshold(trigger):

	threshold = int(re.findall(r'_g.+?_', trigger)[0].split('_')[1].replace('g',''))
	
	return threshold


###########################################################

parser = argparse.ArgumentParser()

parser.add_argument('--loop', dest='loop', action='store_true', default=False)
parser.add_argument('--inputFiles', dest='inputFiles', default=[], nargs='+')
parser.add_argument('--year', dest='year', default=None)

parser.add_argument('--createSF', dest='createSF', action='store_true', default=False)

args = parser.parse_args()

for i in args.inputFiles:
	if i[-1] != '/':
		i += '/'

if args.loop: loop(args.inputFiles, args.year)
elif args.createSF: SFs()


