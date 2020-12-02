#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import numpy as np
import pandas as pd
import argparse
import glob

c4d_path='/opt/c3d/bin/c4d'

debug = False

if debug:
    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    input_dir = '/home/greydon/Documents/GitHub/autofids-brainhack2020/resources/data'
    
    args = Namespace(input_dir=input_dir)
    
def main(args):
    
    #--- Build c4d Command
    c4d_cmd = f"{c4d_path} -verbose {args.input_dir+'/input_data/*.nii.gz'} -foreach -popas ALLMRI -endfor {args.input_dir+'/labels/*.nii.gz'}  \
        -foreach -popas ALLSEG -endfor -rf-param-patch 5x5x5x0 -push ALLMRI -push ALLSEG -rf-param-treedepth 50 \
            -rf-param-ntrees 100 -rf-train {args.input_dir+'/myforest.rf'}"
    
    #--- Run c3d command
    print ('Starting model training...')
    process = subprocess.call(c4d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
    
    
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