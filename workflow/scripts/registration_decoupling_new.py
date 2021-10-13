#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 03:15:24 2020

@author: greydon
"""
import os
import re
import glob
import csv
import subprocess
import pandas as pd


def sorted_nicely(data, reverse = False):
	convert = lambda text: int(text) if text.isdigit() else text
	alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
	
	return sorted(data, key = alphanum_key, reverse=reverse)

def determineFCSVCoordSystem(input_fcsv):
	# need to determine if file is in RAS or LPS
	# loop through header to find coordinate system
	coordFlag = re.compile('# CoordinateSystem')
	coord_sys=None
	with open(input_fcsv, 'r+') as fid:
		rdr = csv.DictReader(filter(lambda row: row[0]=='#', fid))
		row_cnt=0
		for row in rdr:
			cleaned_dict={k:v for k,v in row.items() if k is not None}
			if any(coordFlag.match(x) for x in list(cleaned_dict.values())):
				coordString = list(filter(coordFlag.match,  list(cleaned_dict.values())))
				assert len(coordString)==1
				coord_sys = coordString[0].split('=')[-1].strip()
			row_cnt +=1
	return coord_sys

def convertSlicerRASFCSVtoAntsLPSCSV( input_fcsv, output_csv, coord_system):
	# convert Slicer RAS oriented FCSV (default) to Ants LPS oriented format (expected orientation)
	# use with CAUTION: orientation flips here
	
	df = pd.read_csv(input_fcsv, skiprows=2, usecols=['x','y','z']) # first 2 rows of fcsv not necessary for header
	if any(x in coord_system for x in {'RAS','0'}):
		df['x'] = -1 * df['x'] # flip orientation in x
		df['y'] = -1 * df['y'] # flip orientation in y
	
	# need to add extra column 't' for ANTS
	df['t'] = [0] * df['x'].shape[0]
	df.to_csv( output_csv, index=False )

def convertAntsLPSCSVtoSlicerRASFCSV( input_csv, output_fcsv, ref_fcsv, coord_system):
	# convert Ants LPS oriented format (ants expected orientation) to Slicer RAS oriented FCSV (for viewing in Slicer)
	# use with CAUTION: orientation flips here

	# extract Slicer header
	f = open( ref_fcsv, 'r' )
	lines = f.readlines()
	f.close()

	# orienting the image image back to RAS from LPS
	input_df = pd.read_csv( input_csv, usecols=['x','y','z'] ) # use reference fcsv as template
	df = pd.read_csv( ref_fcsv, skiprows=2 ) # use reference fcsv as template
	
	if any(x in coord_system for x in {'RAS','0'}):
		df['x'] = -1 * input_df['x'] # flip orientation in x
		df['y'] = -1 * input_df['y'] # flip orientation in y
	else:
		df['x'] = input_df['x']
		df['y'] = input_df['y']
		
	df['z'] = input_df['z'] # normal orientation in z
	df.to_csv( output_fcsv, index=False )

	# add in extracted Slicer header
	with open( output_fcsv, 'r+' ) as f:
		old = f.read() # read all the old csv file info
		f.seek(0) # rewind, start at the top
		f.write( lines[0] + lines[1] + old ) # add expected Slicer header

def run_command(cmdLineArguments):
	process = subprocess.Popen(cmdLineArguments, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
	stdout = process.communicate()[0]
	p_status = process.wait()


#%%
debug=False

if debug:
	class Namespace:
		def __init__(self, **kwargs):
			self.__dict__.update(kwargs)
	
	input_bids_dir=r'/home/greydon/scratch/autofid_final/HCP/fmriprep'
	input_fcsv_dir=r'/home/greydon/scratch/autofid_final/HCP/Original'
	output_dir_lin=r'/home/greydon/scratch/fmriprep_HCP_linear_GG'
	output_dir_combined=r'/home/greydon/scratch/fmriprep_HCP_combined_GG'

	args = Namespace(input_bids_dir=input_bids_dir, input_fcsv_dir=input_fcsv_dir, output_dir_lin=output_dir_lin,output_dir_combined=output_dir_combined)

if not os.path.exists(args.output_dir_lin):
	os.makedirs(args.output_dir_lin)

if not os.path.exists(args.output_dir_combined):
	os.makedirs(args.output_dir_combined)

files = [x for x in glob.glob(args.input_fcsv_dir+f'/*/*/*T1w.fcsv')]

for ifile in sorted_nicely(files):
	subj=os.path.basename(os.path.dirname(os.path.dirname(ifile)))
	
	input_transform_to_MNI152=os.path.join(args.input_bids_dir, subj, 'anat', f'{subj}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5')
	input_transform_from_MNI152=os.path.join(args.input_bids_dir, subj, 'anat', f'{subj}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5')
	
	affine_to_MNI152=os.path.join(args.input_bids_dir, subj, "anat",f'00_{subj}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm_AffineTransform.mat')
	displacement_to_MNI152=os.path.join(args.input_bids_dir, subj, "anat",f'01_{subj}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm_DisplacementFieldTransform.nii.gz')
	affine_from_MNI152=os.path.join(args.input_bids_dir, subj, "anat",f'01_{subj}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm_AffineTransform.mat')
	displacement_from_MNI152=os.path.join(args.input_bids_dir, subj, "anat",f'00_{subj}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm_DisplacementFieldTransform.nii.gz')
	
	output_fcsv_lin=os.sep.join([args.output_dir_lin, os.path.splitext(os.path.basename(ifile))[0] + '_lin.fcsv'])
	output_fcsv_nlin=os.sep.join([args.output_dir_combined, os.path.splitext(os.path.basename(ifile))[0] + '_nlin.fcsv'])
	
	tmp_slicer_to_LPS_csv = os.path.dirname(output_fcsv_lin) + f"/tmp_{subj}_slicer_to_LPS.csv"
	tmp_slicer_to_LPS_transformed_lin_csv = os.path.dirname(output_fcsv_lin) + f"/tmp_{subj}_slicer_to_LPS_transformed-lin.csv"
	tmp_slicer_to_LPS_transformed_nlin_csv = os.path.dirname(output_fcsv_lin) + f"/tmp_{subj}_slicer_to_LPS_transformed-nlin.csv"
	
	# if the decomposed transform doesn't exists, run 'CompositeTransformUtil' from ANTS to return the linear and non-linear components
	if not os.path.exists(affine_to_MNI152):
		cmd= f'cd {os.path.join(args.input_bids_dir, subj, "anat")} && /opt/ANTs/bin/CompositeTransformUtil --disassemble {os.path.basename(input_transform_to_MNI152)} {os.path.splitext(os.path.basename(input_transform_to_MNI152))[0]}'
		run_command(cmd)
	
	# if the decomposed transform doesn't exists, run 'CompositeTransformUtil' from ANTS to return the linear and non-linear components
	if not os.path.exists(affine_from_MNI152):
		cmd= f'cd {os.path.join(args.input_bids_dir, subj, "anat")} && /opt/ANTs/bin/CompositeTransformUtil --disassemble {os.path.basename(input_transform_from_MNI152)} {os.path.splitext(os.path.basename(input_transform_from_MNI152))[0]}'
		run_command(cmd)
	
	# determine the coordinate system of the FCSV
	coordSys=determineFCSVCoordSystem(ifile)
	
	if not os.path.exists(output_fcsv_lin):
		
		# need to convert the RAS fiducials to LPS for ANTS, if already LPS then output will be same as input
		convertSlicerRASFCSVtoAntsLPSCSV( ifile, tmp_slicer_to_LPS_csv, coordSys)
		
		cmd = ' '.join(['/opt/ANTs/bin/antsApplyTransformsToPoints',
				  '-d', str(3),
				  '-i', '"'+tmp_slicer_to_LPS_csv+'"',
				  '-o', '"'+tmp_slicer_to_LPS_transformed_lin_csv+'"',
				  '-t', ''.join(['"[', '"', affine_from_MNI152, '"', ",", str(0), ']"'])])
		
		run_command(cmd)
		
		convertAntsLPSCSVtoSlicerRASFCSV(tmp_slicer_to_LPS_transformed_lin_csv, output_fcsv_lin, ifile, coordSys)
		
		os.remove(tmp_slicer_to_LPS_transformed_lin_csv)
	
	if not os.path.exists(output_fcsv_nlin):
		if not os.path.exists(tmp_slicer_to_LPS_csv):
			# need to convert the RAS fiducials to LPS for ANTS, if already LPS then output will be same as input
			convertSlicerRASFCSVtoAntsLPSCSV( ifile, tmp_slicer_to_LPS_csv, coordSys)
	
		# now apply the non-linear component to the output FCSV from above
		cmd_nlin = ' '.join(['/opt/ANTs/bin/antsApplyTransformsToPoints',
				  '-d', str(3),
				  '-i', '"'+tmp_slicer_to_LPS_csv+'"',
				  '-o', '"'+tmp_slicer_to_LPS_transformed_nlin_csv+'"',
				  '-t', ''.join(['"[', '"', input_transform_from_MNI152, '"', ",", str(0), ']"'])])
		
		run_command(cmd_nlin)
		
		convertAntsLPSCSVtoSlicerRASFCSV(tmp_slicer_to_LPS_transformed_nlin_csv, output_fcsv_nlin, ifile, coordSys)
		
		os.remove(tmp_slicer_to_LPS_transformed_nlin_csv)
	
	if os.path.exists(tmp_slicer_to_LPS_csv):
		os.remove(tmp_slicer_to_LPS_csv)


