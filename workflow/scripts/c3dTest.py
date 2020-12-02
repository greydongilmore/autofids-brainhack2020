#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import glob
import yaml


script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
config_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'config/config.yml')

with open(config_path) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

c4d_path=os.path.join(config['c3d_path'],'c4d')

def main():
    
    out_dir=os.path.join(config['output_dir'],'test_prob')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    for ifile in glob.glob(os.path.join(config['output_dir'],'test_data','*.nii.gz')):
        output_prob=os.path.join(out_dir, os.path.basename(ifile).split('.nii')[0] + '_prob.nii.gz')
        c4d_cmd = f"{c4d_path} -verbose {ifile} -rf-apply {config['output_dir']+'/myforest.rf'} -o {output_prob}"
    
        #--- Run c3d command
        print ('Starting model training...')
        process = subprocess.call(c4d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
        
        
if __name__ == "__main__":
    
    main()