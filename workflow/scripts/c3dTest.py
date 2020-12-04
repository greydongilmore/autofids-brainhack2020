#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import glob
import yaml
import nibabel
import numpy as np
import glob

script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
config_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'config/config.yml')

with open(config_path) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

c4d_path=os.path.join(config['c3d_path'],'c4d')

def main():
    
    out_dir=os.path.join(config['output_dir'],'test_prob')
    
    model_fn=glob.glob(os.path.join(config['output_dir'],'*.rf'))
    
    if model_fn:
        for ifile in glob.glob(os.path.join(config['output_dir'],'test_data','*.nii.gz')):
            output_prob=os.path.join(out_dir, os.path.basename(ifile).split('.nii')[0] + '_prob%02d.nii.gz')
            
            c4d_cmd = f"{c4d_path} -verbose {ifile} -rf-apply {model_fn[0]} -oo {output_prob}"
        
            #--- Run c3d command
            print (f'Starting model testing: {os.path.basename(ifile)}')
            process = subprocess.call(c4d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
            
            # sub = os.path.basename(ifile).split('_')[0]
            # ground_truth_file=glob.glob(os.path.join(config['output_dir'],'test_data_labels',f'{sub}*.nii.gz'))
                
            # out_prob = nibabel.load(output_prob)
            # ground_truth = nibabel.load(ground_truth_file[0])
            
            # prob_data = out_prob.get_fdata()
            # ground_truth_data = ground_truth.get_fdata()
            
            # output_prob_labels=os.path.join(out_dir, os.path.basename(ifile).split('.nii')[0] + '_label04.nii.gz')
            # nii_mask = nibabel.Nifti1Image(prob_data[...,3], ground_truth.affine, ground_truth.header)
            # nibabel.save(nii_mask, output_prob_labels)
            
            # len(prob_data[..., 3]==4)
            # len(ground_truth_data[ground_truth_data==1])
            
            # len(prob_data[prob_data==1])
            # len(ground_truth_data[ground_truth_data==2])
            
            # np.unique(ground_truth_data)
            # np.unique(prob_data)
        
if __name__ == "__main__":
    
    main()