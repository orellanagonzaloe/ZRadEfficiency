ZRadEfficiency
=========================

Script to produce Photon Trigger Efficiencies and SFs files, using the output of the [RadiativeZ](https://gitlab.cern.ch/ATLAS-EGamma/Software/PhotonID/RadiativeZ/) tool.

The procedure is done in three stages. The first one is to process the samples into the ntuples, using the `RadiativeZ` tool. Then a loop in those ntuples to produce a small output. Finally, the productions f the Eff/SFs files.

## RadiativeZ output

Run the `RadiativeZ` tool including this configuration in the AnalysisConfig.cxx:

	doPhotonTriggerMatching = true;
	elQuality = "LHMedium";
	elIsolation = "FCLoose";
	muQuality = "Medium";
	muIsolation = "FCLoose";

## Loop

Creates a rootfile with all information in `output` directory. In `ZRadEfficiency.yaml` is the default configuration. You need to indicate the path to the ntuples from `RadiativeZ`. Wildcards and multiple path are possible (if you want to include both electron and muon decays together). Also year must be indicated to choose the correct trigger list. Example:

	python ZRadEfficiency.py --loop --inputFiles /path/to/data15_EGAM3/*/* /path/to/data15_EGAM4/*/* --year 2015

## EFf/SFs files

Only after the previous step was done for all year, and also for both Data and MC, you can produce the Eff/SFs files (`SFs` directory):

	python ZRadEfficiency.py --createSF