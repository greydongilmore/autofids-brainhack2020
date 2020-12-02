#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import numpy as np
import pandas as pd
import argparse
import glob
import shutil
import nibabel

c3d_path='/opt/c3d/bin/c3d'

debug = False

if debug:
    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    input_dir = '/media/veracrypt6/projects/autofids/data/model_data'
    output_dir = '/home/greydon/Documents/GitHub/autofids-brainhack2020/resources/data/'
    
    args = Namespace(input_dir=input_dir, output_dir=output_dir)
    
def run_command(cmdLineArguments):
    process = subprocess.Popen(cmdLineArguments, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
    stdout = process.communicate()[0]
    p_status = process.wait()
    
def main(args):
    
    for ifile in glob.glob(os.path.join(args.input_dir,'*.nii.gz')):
        
        sub = os.path.basename(ifile).split('_')[0]
        input_fcsv=glob.glob(os.path.join(args.input_dir,f'{sub}*.fcsv'))
        
        if input_fcsv:
            if not os.path.exists(os.path.join(args.output_dir,'labels')):
                os.makedirs(os.path.join(args.output_dir,'labels'))
            
            if not os.path.exists(os.path.join(args.output_dir,'input_data')):
                os.makedirs(os.path.join(args.output_dir,'input_data'))
            
            landmarks_txt=os.path.join(args.output_dir, 'labels', os.path.basename(ifile).split('.nii')[0] + '_landmarks.txt')
            output_mask=os.path.join(args.output_dir, 'labels', os.path.basename(ifile).split('.nii')[0] + '_afids.nii.gz')
            
            fcsv_df = pd.read_csv(input_fcsv[0], sep=',', header=2)
            
            coords = fcsv_df[['x','y','z']].to_numpy()
            with open (landmarks_txt, 'w') as fid:
                for i in range(len(coords)):
                    fid.write(' '.join(str(i) for i in np.r_[np.round(coords[i,:],3),int(1)])+ "\n")
            
            #--- Build c3d Command
            c3d_cmd = f"{c3d_path} {ifile} -scale 0 -landmarks-to-spheres {landmarks_txt} 1 -o {output_mask}"
            
            #--- Run c3d command
            print (f'Starting landmark mask for {os.path.basename(ifile)}')
            process = subprocess.call(c3d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
            
            seg = nibabel.load(output_mask)
            data = seg.get_fdata()
            data[data==0]=2
            
            ni_img = nibabel.Nifti1Image(data, seg.affine)
            nibabel.save(ni_img, output_mask)

            shutil.copyfile(ifile, os.path.join(args.output_dir,'input_data',os.path.basename(ifile)))
    
###############################################################################
if __name__ == "__main__":
    
    ###############################################################################
    # command-line arguments with flags
    ###############################################################################
    parser = argparse.ArgumentParser(description="Run c3d to convert 3D Slicer fcsv files into binary landmark masks.")
    
    parser.add_argument("-i", dest="input_dir", help="Input data directory with nifti files and fcsv files.")
    parser.add_argument("-o", dest="output_dir", help="Output directory to store label volumes)")
    
    args = parser.parse_args()
    
    main(args)