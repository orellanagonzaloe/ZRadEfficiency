import os
import re
import sys
import yaml
import math
import ctypes
import glob
from array import array 


import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import *


with open('ZRadEfficiency.yaml', 'r') as f:
	cfg = yaml.safe_load(f)

run_range = {
	'2015' : '276262_284484',
	'2016' : '297730_311481',
	'2017' : '325713_340453',
	'2018' : '348885_364292',
	'2021' : 'XXXXXX_XXXXXX',
}


def main(SFsDir, outputPlotDir):

	inputfiles = glob.glob(SFsDir + 'efficiency*.root')

	for file in inputfiles:	

		if '1D' in  file:

			rootfile = ROOT.TFile(file, 'READ')

			tgae_tmp = rootfile.Get('%s/FullSim_sf' % run_range[file.split('.')[3]])

			plot_eff(tgae_tmp, file, outputPlotDir)

			continue


		rootfile = ROOT.TFile(file, 'READ')

		h_tmp = rootfile.Get('%s/FullSim_sf' % run_range[file.split('.')[3]])

		h_tmp_err = h_tmp.Clone()
		h_tmp_err.Reset()

		for i in range(1, h_tmp.GetNbinsX()+1):
			for j in range(1, h_tmp.GetNbinsY()+1):

				err = h_tmp.GetBinError(i, j)
				h_tmp_err.SetBinContent(i, j, err)

		plot_SF(h_tmp, h_tmp_err, file, outputPlotDir)

		rootfile.Close()





def plot_SF(h_SF, h_SF_err, file, outputPlotDir):

	ZCanvas = ROOT.TCanvas('ZCanvas', 'ZCanvas', 0, 0, 1000, 700)

	ROOT.gPad.SetRightMargin(0.16)
	ROOT.gPad.SetLeftMargin(0.06)
	ROOT.gPad.SetTopMargin(0.03)

	
	h_SF.SetStats(ROOT.kFALSE)
	ROOT.gStyle.SetOptStat( 10 )
	ROOT.gStyle.SetOptTitle(0)

	ROOT.gStyle.SetStatY(0.9)                
	ROOT.gStyle.SetStatX(0.3)                
	ROOT.gStyle.SetStatW(0.2)                
	ROOT.gStyle.SetStatH(0.22)
	ROOT.gStyle.SetPaintTextFormat('1.3f')

	z_min = h_SF.GetMinimum(0.)
	z_max = h_SF.GetMaximum(1.)


	h_SF.GetXaxis().SetRangeUser( 10000. , 50000. )
	h_SF.GetYaxis().SetRangeUser( 0. , 2.39 )
	h_SF.GetZaxis().SetRangeUser( 0. , 1.5 )

	h_SF.GetXaxis().SetLabelOffset(999)
	h_SF.GetXaxis().SetLabelSize(0)
	h_SF.GetXaxis().SetTickLength(0)
	h_SF.GetXaxis().SetTitle('E_{T} [GeV]')

	h_SF.GetYaxis().SetLabelOffset(999)
	h_SF.GetYaxis().SetLabelSize(0)
	h_SF.GetYaxis().SetTickLength(0)
	h_SF.GetYaxis().SetTitle('|#eta|')

	h_SF.GetYaxis().SetTitleOffset( 0.5 )
	h_SF.GetXaxis().SetTitleOffset( 1.1 )

	gStyle.SetNumberContours(999)

	gStyle.SetPalette(ROOT.kFruitPunch)



	h_SF.SetBarOffset(0.2)
	h_SF.Draw('colz TEXT')
	h_SF.SetMaximum(z_max)
	h_SF.SetMinimum(z_min)

	h_SF_err.SetMarkerColor(ROOT.kRed+3)
	h_SF_err.SetBarOffset(-0.2)
	h_SF_err.Draw('TEXT SAME')
	h_SF_err.SetMinimum(-1.)



	# Vertical lines
	sf_Yline = []
	for i in range(len(cfg['et_binning'])-1):

		sf_Yline.append(ROOT.TLine(cfg['et_binning'][i], cfg['eta_binning'][0], cfg['et_binning'][i], cfg['eta_binning'][len(cfg['eta_binning'])-1]))
		sf_Yline[i].SetLineWidth(1)
		sf_Yline[i].SetLineStyle(2)
		sf_Yline[i].Draw()
	
	# Horizontal lines
	sf_Xline = []
	for i in range(len(cfg['eta_binning'])):

		sf_Xline.append(ROOT.TLine(cfg['et_binning'][0], cfg['eta_binning'][i], cfg['et_binning'][len(cfg['et_binning'])-1], cfg['eta_binning'][i]))
		sf_Xline[i].SetLineWidth(1)
		sf_Xline[i].SetLineStyle(2)
		sf_Xline[i].Draw()
	
	

	# Horizontal axis
	sf_Yaxis = []
	for i in range(len(cfg['et_binning'])-1):

		sf_Yaxis.append(ROOT.TGaxis(cfg['et_binning'][i], cfg['eta_binning'][0], cfg['et_binning'][i+1], cfg['eta_binning'][0], cfg['et_binning'][i]/1000, cfg['et_binning'][i+1]/1000, 0o1, ''))
		sf_Yaxis[i].SetTextFont(42)
		sf_Yaxis[i].SetLabelSize(0.03)
		sf_Yaxis[i].Draw()
	
	# Vertical axis
	sf_Xaxis = []
	for i in range(len(cfg['eta_binning'])-1):

		sf_Xaxis.append(ROOT.TGaxis(cfg['et_binning'][0], cfg['eta_binning'][i], cfg['et_binning'][0], cfg['eta_binning'][i+1], cfg['eta_binning'][i], cfg['eta_binning'][i+1], 0o1, ''))
		sf_Xaxis[i].SetTextFont(42)
		sf_Xaxis[i].SetLabelSize(0.03)
		sf_Xaxis[i].Draw()



	atlas_int = ROOT.TLatex(0.10, 0.92, '#font[72]{ATLAS} Internal')
	atlas_int.SetNDC()
	atlas_int.SetTextFont(42)
	atlas_int.SetLineWidth(2)
	atlas_int.Draw()
	data_label = ROOT.TLatex(0.10, 0.87, 'Data %s, #sqrt{s} = 13 TeV' % (file.split('.')[3]))
	data_label.SetNDC()
	data_label.SetTextFont(42)
	data_label.SetTextSize(0.035)
	data_label.SetLineWidth(2)
	data_label.Draw()
	channel_label = ROOT.TLatex(0.10, 0.82, 'Z#rightarrow ll#gamma')
	channel_label.SetNDC()
	channel_label.SetTextFont(42)
	channel_label.SetTextSize(0.035)
	channel_label.SetLineWidth(2)
	channel_label.Draw()

	trigger_tmp = ROOT.TLatex(0.42, 0.87, file.split('.')[1])
	trigger_tmp.SetNDC()
	trigger_tmp.SetTextFont(42)
	trigger_tmp.SetTextSize(0.035)
	trigger_tmp.SetLineWidth(2)
	trigger_tmp.Draw()

	Z_axis_label = ROOT.TLatex(0.9,0.95,'#splitline{SF}{#color[635]{Stat. Unc.}}')
	Z_axis_label.SetNDC()
	Z_axis_label.SetTextFont(42)
	Z_axis_label.SetTextSize(0.035)
	Z_axis_label.SetLineWidth(2)
	Z_axis_label.Draw()
	

	filename = outputPlotDir + file.split('/')[-1].replace('.root','.pdf')

	ZCanvas.Print( filename )


def plot_eff(tgae_tmp, file, outputPlotDir):


	canvas = ROOT.TCanvas('ZCanvas', 'ZCanvas', 0, 0, 800, 600)

	gPad.SetRightMargin(0.05)
	gPad.SetTopMargin(0.05)


	legend = ROOT.TLegend(0.42, 0.68, 0.59, 0.91)




	tgae_tmp.SetMarkerStyle(20)
	tgae_tmp.SetMarkerSize(1.2)
	tgae_tmp.SetLineWidth(2)

	tgae_tmp.SetMarkerColor(861)
	tgae_tmp.SetLineColor(861)

	legend.AddEntry(tgae_tmp, file.split('.')[1], 'p')


	tgae_tmp.Draw('aepz')


	# tgae_tmp.GetXaxis().SetRangeUser( 20. , 70. )
	tgae_tmp.GetXaxis().SetLabelFont(42)
	# tgae_tmp.GetXaxis().SetLabelSize(0.05)
	# tgae_tmp.GetXaxis().SetTitleSize(0.05)
	tgae_tmp.GetXaxis().SetTitleOffset(1.1)
	tgae_tmp.GetXaxis().SetTitleFont(42)


	tgae_tmp.GetYaxis().SetRangeUser( 0. , 1.55 )
	tgae_tmp.GetYaxis().SetLabelFont(42)
	# tgae_tmp.GetYaxis().SetLabelSize(0.05)
	# tgae_tmp.GetYaxis().SetTitleSize(0.05)
	tgae_tmp.GetYaxis().SetTitleOffset(1.1)
	tgae_tmp.GetYaxis().SetTitleFont(42)
	tgae_tmp.GetYaxis().SetTitle('Efficiency')




	tgae_tmp.GetXaxis().SetTitle('#font[52]{E}_{T} [GeV]')
	tgae_tmp.GetXaxis().SetRangeUser(8., 60.)

	line = ROOT.TLine()
	line.SetY1(1)
	line.SetY2(1)
	line.SetLineColor(ROOT.kGray)
	line.SetLineStyle(7)
	line.SetX1(10.)
	line.SetX2(60.)
	line.Draw('same')


	atlas_int = ROOT.TLatex(0.15, 0.85, '#font[72]{ATLAS} Internal')
	atlas_int.SetNDC()
	atlas_int.SetTextFont(42)
	atlas_int.SetLineWidth(2)
	atlas_int.Draw('same')
	data_label = ROOT.TLatex(0.15, 0.8, 'Data %s, #sqrt{s} = 13 TeV' % (file.split('.')[3]))
	data_label.SetNDC()
	data_label.SetTextFont(42)
	data_label.SetTextSize(0.035)
	data_label.SetLineWidth(2)
	data_label.Draw('same')

	channel_label = ROOT.TLatex(0.15, 0.75, 'Z#rightarrow ll#gamma')
	channel_label.SetNDC()
	channel_label.SetTextFont(42)
	channel_label.SetTextSize(0.035)
	channel_label.SetLineWidth(2)
	channel_label.Draw('same')

	legend.SetTextSize(0.04)
	legend.SetBorderSize(0)
	legend.Draw('same')



	filename = outputPlotDir + file.split('/')[-1].replace('.root', '.pdf')

	canvas.Print(filename)