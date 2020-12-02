#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import numpy as np
import pandas as pd
import argparse
import glob
import nibabel

c4d_path='/opt/c3d/bin/c4d'

debug = False

if debug:
    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    input_dir = '/home/greydon/Documents/GitHub/autofids-brainhack2020/resources/data'
    
    args = Namespace(input_dir=input_dir)
    
def main(args):
    
    test_img="/home/greydon/Documents/GitHub/autofids-brainhack2020/resources/data/input_data/sub-103111_space-MNI152NLin2009cAsym_T1w.nii.gz"

    c4d_cmd = f"{c4d_path} -verbose {test_img} -rf-apply {args.input_dir+'/myforest.rf'} -o {args.input_dir+'/class_prob.nii.gz'}"
    
    #--- Run c3d command
    print ('Starting model training...')
    process = subprocess.call(c4d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
    
    seg = nibabel.load(os.path.join(args.input_dir,'class_prob.nii.gz'))
    true=nibabel.load("/home/greydon/Documents/GitHub/autofids-brainhack2020/resources/data/labels/sub-103111_space-MNI152NLin2009cAsym_T1w_afids.nii.gz")
    data = seg.get_fdata()
    data_true = true.get_fdata()
    
    len(data[data==0])
    len(data_true[data_true==1])
    len(data[data==1])
    len(data_true[data_true==2])
    len(data[data==2])
            
            ni_img = nibabel.Nifti1Image(data, seg.affine)
            nibabel.save(ni_img, os.path.join(args.input_dir,'class_prob.nii.gz'))
            
###############################################################################
if __name__ == "__main__":
    
    ###############################################################################
    # command-line arguments with flags
    ###############################################################################
    parser = argparse.ArgumentParser(description="Run c3d to convert 3D Slicer fcsv files into binary landmark masks.")
    
    parser.add_argument("-i", dest="input_dir", help="Input data directory with sub-directory 'data'")
    parser.add_argument("-o", dest="output_dir", help="Output directory to store label volumes)")
    
    args = parser.parse_args()
    
    main(args)