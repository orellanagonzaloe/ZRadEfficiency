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

data_mc = {True : '', False : 'MC'}


syst_list = {
	
	'nominal': (0, 0, 0, 0, 0, 0),
	'llg_up' : (1, 1, 0, 0, 0, 0),
	'llg_dn' : (2, 2, 0, 0, 0, 0),
	'll_up'  : (0, 0, 1, 1, 0, 0),
	'll_dn'  : (0, 0, 2, 2, 0, 0),
	'l_ISO'  : (0, 0, 0, 0, 1, 0),
	'l_ID'   : (0, 0, 0, 0, 0, 1),
}

run_range = {
	'2015' : '276262_284484',
	'2016' : '297730_311481',
	'2017' : '325713_340453',
	'2018' : '348885_364292',
}

def main():

	if not os.path.exists('SFs/'):
		os.makedirs('SFs/')

	# for yr in ['2015']:
	for yr in ['2015', '2016', '2017', '2018']:
		for sam in ['data', 'MC']:

			createEff(yr, sam)

		createSF(yr)


def createEff(year, sam):

	### read output ###

	d_num_syst_tr = {}
	d_den_syst = {}
	d_num_syst_tr_1D = {}
	d_den_syst_tr_1D = {}

	filename = 'output/loop_output_%s_%s.root' % (sam, year)
	inputfile = ROOT.TFile(filename, 'READ')

	for syst in syst_list:

		d_den_syst[syst] = inputfile.Get('h_den_syst_' + syst)
		d_den_syst[syst].SetDirectory(0)

		d_num_syst_tr[syst] = {}
		d_num_syst_tr_1D[syst] = {}
		d_den_syst_tr_1D[syst] = {}

		for tr in cfg['trigger_list'][year]:

			d_num_syst_tr[syst][tr] = inputfile.Get('h_num_syst_tr_' + syst + '_' + tr)
			d_num_syst_tr[syst][tr].SetDirectory(0)
			d_num_syst_tr_1D[syst][tr] = inputfile.Get('h_num_syst_tr_' + syst + '_' + tr + '_1D')
			d_num_syst_tr_1D[syst][tr].SetDirectory(0)
			d_den_syst_tr_1D[syst][tr] = inputfile.Get('h_den_syst_tr_' + syst + '_' + tr + '_1D')
			d_den_syst_tr_1D[syst][tr].SetDirectory(0)

	
	### setup eff histograms

	h_num_bin = ROOT.TH1D('h_num_bin', 'title', 1, 0, 1)
	h_den_bin = ROOT.TH1D('h_den_bin', 'title', 1, 0, 1)
	h_num_bin.Sumw2()
	h_den_bin.Sumw2()

	h_eff_tr = {}
	h_eff_tr_1D = {}
	for syst in syst_list:

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


			h_eff_tr_1D[syst][tr] = ROOT.TGraphAsymmErrors()
			h_eff_tr_1D[syst][tr].Divide(d_num_syst_tr_1D[syst][tr], d_den_syst_tr_1D[syst][tr])



	inputfile.Close()


	### including systematics errors ###


	for syst in syst_list:

		if syst == 'nominal': continue

		for tr in cfg['trigger_list'][year]:

			for et in xrange(1, len(cfg['et_binning'])):
				for eta in xrange(1, len(cfg['eta_binning'])):

					old_error = h_eff_tr['nominal'][tr].GetBinError(et, eta)

					diff = h_eff_tr[syst][tr].GetBinContent(et, eta) - h_eff_tr['nominal'][tr].GetBinContent(et, eta)

					new_error = math.sqrt(old_error**2 + diff**2)

					h_eff_tr['nominal'][tr].SetBinError(et, eta, new_error)




	### eff output file ###

	for tr in cfg['trigger_list'][year]:

		if sam == 'data': sam = ''

		filename_eff = 'SFs/efficiency%s.%s.%s.%s.root' % (sam, tr, cfg['ph_ISO'], year)
		outputfile_eff = ROOT.TFile(filename_eff, 'RECREATE')
		outputdir_eff = outputfile_eff.mkdir(run_range[year])
		outputdir_eff.cd() 

		h_eff_tr['nominal'][tr].SetName('FullSim_sf')
		h_eff_tr['nominal'][tr].SetTitle('FullSim_sf')

		h_eff_tr['nominal'][tr].Write('FullSim_sf')

		outputfile_eff.Close()

		print '%s was created' % filename_eff

		filename_eff = 'SFs/efficiency1D%s.%s.%s.%s.root' % (sam, tr, cfg['ph_ISO'], year)
		outputfile_eff = ROOT.TFile(filename_eff, 'RECREATE')
		outputdir_eff = outputfile_eff.mkdir(run_range[year])
		outputdir_eff.cd() 

		h_eff_tr_1D['nominal'][tr].SetName('FullSim_sf')
		h_eff_tr_1D['nominal'][tr].SetTitle('FullSim_sf')

		h_eff_tr_1D['nominal'][tr].Write('FullSim_sf')

		outputfile_eff.Close()

		print '%s was created' % filename_eff




def createSF(year):


	for tr in cfg['trigger_list'][year]: 

		filename_MC = 'SFs/efficiencyMC.%s.%s.%s.root' % (tr, cfg['ph_ISO'], year)
		inputfile_MC = ROOT.TFile(filename_MC, 'READ')

		h_MC = inputfile_MC.Get('%s/FullSim_sf' % run_range[year])
		h_MC.SetDirectory(0)


		filename_data = 'SFs/efficiency.%s.%s.%s.root' % (tr, cfg['ph_ISO'], year)
		inputfile_data = ROOT.TFile(filename_data, 'READ')

		h_data = inputfile_data.Get('%s/FullSim_sf' % run_range[year])
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
		outputdir_SF = outputfile_SF.mkdir(run_range[year])
		outputdir_SF.cd() 

		h_SF.SetName('FullSim_sf')
		h_SF.SetTitle('FullSim_sf')

		h_SF.Write('FullSim_sf')

		outputfile_SF.Close()

		print '%s was created' % filename_SF





def get_trigger_threshold(trigger):

	threshold = int(re.findall(r'_g.+?_', trigger)[0].split('_')[1].replace('g',''))
	
	return threshold
















