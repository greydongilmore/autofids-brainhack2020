#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 03:15:24 2020

@author: greydon
"""
import os
import glob
import subprocess
import numpy as np
import pandas as pd
import argparse

def convertSlicerRASFCSVtoAntsLPSCSV( input_fcsv, output_csv ):
	# convert Slicer RAS oriented FCSV (default) to Ants LPS oriented format (expected orientation)
	# use with CAUTION: orientation flips here

	df = pd.read_csv( input_fcsv, skiprows=2, usecols=['x','y','z'] ) # first 2 rows of fcsv not necessary for header
	df['x'] = -1 * df['x'] # flip orientation in x
	df['y'] = -1 * df['y'] # flip orientation in y
	df.to_csv( output_csv, index=False )

def convertAntsLPSCSVtoSlicerRASFCSV( input_csv, output_fcsv, ref_fcsv ):
	# convert Ants LPS oriented format (ants expected orientation) to Slicer RAS oriented FCSV (for viewing in Slicer)
	# use with CAUTION: orientation flips here

	# extract Slicer header
	f = open( ref_fcsv, 'r' )
	lines = f.readlines()
	f.close()

	# orienting the image image back to RAS from LPS
	input_df = pd.read_csv( input_csv, usecols=['x','y','z'] ) # use reference fcsv as template
	df = pd.read_csv( ref_fcsv, skiprows=2 ) # use reference fcsv as template
	df['x'] = -1 * input_df['x'] # flip orientation in x
	df['y'] = -1 * input_df['y'] # flip orientation in y
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

#if debug:
#	class Namespace:
#		def __init__(self, **kwargs):
#			self.__dict__.update(kwargs)
#	
#	input_deriv_dir=r'/home/greydon/Documents/scratch/lhsc_dbs/deriv/fmriprep'
#	input_fcsv_dir=r'/home/greydon/Documents/scratch/lhsc_dbs/deriv/afids'
#	
#	args = Namespace(input_deriv_dir=input_deriv_dir, input_fcsv_dir=input_fcsv_dir)
#

def main(args):
	
	subjects=[x for x in os.listdir(args.input_deriv_dir) if os.path.isdir(os.path.join(args.input_deriv_dir,x))]

	for isub in subjects:
		
		for ifile in glob.glob(args.input_fcsv_dir+f'/{isub}/*/*.fcsv'):
			
			input_warp_to_MNI152=os.path.join(args.input_deriv_dir, isub, 'anat', f'{isub}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5')
			input_warp_to_MNI152_dis=os.path.join(args.input_deriv_dir, isub, 'anat', f'{isub}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm')
			
			affineT=os.path.join(args.input_deriv_dir, isub, "anat", f'00_{isub}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm_AffineTransform.mat')
			displacement=os.path.join(args.input_deriv_dir, isub, "anat",f'01_{isub}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm_DisplacementFieldTransform.nii.gz')
			
			output_fcsv=os.sep.join([args.input_fcsv_dir, isub, "anat", os.path.splitext(os.path.basename(ifile).split(os.sep)[-1])[0] + '_lin.fcsv'])
			tmp_slicer_to_ants_csv = os.path.dirname(output_fcsv) + "/tmp_slicer_to_ants.csv"
			tmp_slicer_to_ants_transformed_csv = os.path.dirname(output_fcsv) + "/tmp_slicer_to_ants_transformed.csv"
			
			if not os.path.exists(affineT):
				cmd= f'cd {os.path.join(args.input_deriv_dir, isub, "anat")} && CompositeTransformUtil --disassemble {os.path.basename(input_warp_to_MNI152)} {os.path.basename(input_warp_to_MNI152_dis)}'
				
				run_command(cmd)
			
			
			convertSlicerRASFCSVtoAntsLPSCSV( ifile, tmp_slicer_to_ants_csv )
			
			cmd = ' '.join(['antsApplyTransformsToPoints',
					  '-d', str(3),
					  '-i', '"'+tmp_slicer_to_ants_csv+'"',
					  '-o', '"'+tmp_slicer_to_ants_transformed_csv+'"',
					  '-t', ''.join(['"[', '"', affineT, '"', ",", str(1), ']"']),
					  '-t', displacement])
			
			run_command(cmd)
			
			
			convertAntsLPSCSVtoSlicerRASFCSV( tmp_slicer_to_ants_transformed_csv, output_fcsv, ifile )
			
			
			os.remove(tmp_slicer_to_ants_csv)
			os.remove(tmp_slicer_to_ants_transformed_csv)

if __name__ == "__main__":
	
	# Input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-input_deriv_dir', help='Directory for the fmriprep data.')
	parser.add_argument("-input_fcsv_dir", help="Directory for the fcsv files")
	args = parser.parse_args()
	 
	main(args)
