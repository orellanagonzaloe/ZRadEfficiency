#! /usr/bin/env python

### contact: orellana.g@cern.ch, for any suggestion! ###

import os

import utils as utl

import ROOT
ROOT.gROOT.SetBatch(True)





def main(cfg):

	### init ###

	if not os.path.exists(cfg['outputDir']):
		os.makedirs(cfg['outputDir'])

	isData = utl.isData(cfg['inputFiles'])

	d_all_hist = utl.createHistDictionary(cfg)


	### setup chain ###

	if not ROOT.xAOD.Init().isSuccess():
		utl.printMsg('Failed xAOD.Init()', 2)

	chain = ROOT.TChain('output')

	for file in cfg['inputFiles']:
		chain.Add(file)

	# Set aliases to branches to omit annoying dots in name...

	usedBranches = ['llg.m', 'll.m', 'ph.pt', 'ph.eta2', 'ph.tight_AOD', 'ph.isoloose', 'ph.isotight', 'ph.isotightcaloonly']

	for var in usedBranches:
		chain.SetAlias(var.replace('.', '_'), var)

	if cfg['phIso'] == 'FixedCutLoose':
		chain.SetAlias('phIso', 'ph.isoloose')
	elif cfg['phIso'] == 'FixedCutTight':
		chain.SetAlias('phIso', 'ph.isotight')
	elif cfg['phIso'] == 'FixedCutTightCaloOnly':
		chain.SetAlias('phIso', 'ph.isotightcaloonly')

	chain.SetAlias('phID', 'ph.tight_AOD')

	chain.SetAlias('phIso', 'ph.isotightcaloonly')

	chain.SetAlias('l1IDMedium', 'l1.medium_id')
	chain.SetAlias('l1IDTight', 'l1.tight_id')
	# chain.SetAlias('l1IDLoose', 'l1.loose_id')

	chain.SetAlias('l2IDMedium', 'l2.medium_id')
	chain.SetAlias('l2IDTight', 'l2.tight_id')
	# chain.SetAlias('l2IDLoose', 'l2.loose_id')

	chain.SetAlias('l1IsoFCLoose', 'l1.isoloose')
	chain.SetAlias('l1IsoFCTight', 'l1.isotight')

	chain.SetAlias('l2IsoFCLoose', 'l2.isoloose')
	chain.SetAlias('l2IsoFCTight', 'l2.isotight')

	nevents = chain.GetEntries()
	if cfg['nevents'] is not None:
		nevents = cfg['nevents']
	utl.printMsg('Running with %i' % (nevents), 0)


	### start event loop ###

	for entry in range(nevents):

		if entry % int(nevents/100) == 0:
			utl.printProgressbar('', nevents, entry)

		chain.GetEntry(entry)

		d_match_tr = {}
		for tr in cfg['triggerList'][cfg['year']]:
			d_match_tr[tr] = getattr(chain, 'Trigger.'+tr+'_match_gamma')

		phPDGID = 22
		if not isData:
			phPDGID = getattr(chain, 'ph.truth_pdgId')

		for syst, systIndex in cfg['systMap'].items():

			minMllg = utl.getSystValue(syst, 'minMllg', cfg)
			maxMllg = utl.getSystValue(syst, 'maxMllg', cfg)
			b_massMllgWin = (chain.llg_m > minMllg) and (chain.llg_m < maxMllg)

			minMll = utl.getSystValue(syst, 'minMll', cfg)
			maxMll = utl.getSystValue(syst, 'maxMll', cfg)
			b_massMllWin = (chain.ll_m > minMll) and (chain.ll_m < maxMll)

			b_phReq = chain.phID and chain.phIso and (phPDGID == 22)

			lID = utl.getSystValue(syst, 'lID', cfg)
			lIso = utl.getSystValue(syst, 'lIso', cfg)
			l1ID = getattr(chain, 'l1ID%s' % (lID))
			l2ID = getattr(chain, 'l2ID%s' % (lID))
			l1Iso = getattr(chain, 'l1Iso%s' % (lIso))
			l2Iso = getattr(chain, 'l2Iso%s' % (lIso))
			b_lepReq = all([l1ID, l2ID, l1Iso, l2Iso])

			if all([b_massMllgWin, b_massMllWin, b_phReq, b_lepReq]):

				for tr in cfg['triggerList'][cfg['year']]:

					d_all_hist[syst][tr]['et']['den'].Fill(chain.ph_pt * 0.001)
					d_all_hist[syst][tr]['eta']['den'].Fill(chain.ph_eta2)
					d_all_hist[syst][tr]['et:eta']['den'].Fill(chain.ph_pt, abs(chain.ph_eta2))

					if getattr(chain, 'Trigger.%s_match_gamma' % (tr)):

						d_all_hist[syst][tr]['et']['num'].Fill(chain.ph_pt * 0.001)
						d_all_hist[syst][tr]['eta']['num'].Fill(chain.ph_eta2)
						d_all_hist[syst][tr]['et:eta']['num'].Fill(chain.ph_pt, abs(chain.ph_eta2))

	print('')

	### output file ###

	_tag = 'data' if isData else 'MC'
	filename = 'output/loop_output_%s_%s.root' % (_tag, cfg['year'])

	utl.writeOutput(cfg, filename, d_all_hist)



