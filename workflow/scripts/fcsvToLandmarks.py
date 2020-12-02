#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import numpy as np
import pandas as pd
import glob
import shutil
import nibabel
import yaml
from sklearn.model_selection import train_test_split


script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
config_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'config/config.yml')

with open(config_path) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

c3d_path=os.path.join(config['c3d_path'],'c3d')

def main():
    nifti_files=glob.glob(os.path.join(config['input_dir'])+'/*.nii.gz')
    x_train ,x_test = train_test_split(nifti_files,test_size=0.2)
    
    dir_setup={'test_data','test_data_labels','test_prob','train_data','train_data_labels'}
    for ipath in dir_setup:
        if not os.path.exists(os.path.join(config['output_dir'],ipath)):
            os.makedirs(os.path.join(config['output_dir'],ipath))
    
    dir_dic = {
        'train_data': x_train,
        'test_data': x_test}
    
    for idir,ifiles in dir_dic.items():
        for ifile in ifiles:
            
            sub = os.path.basename(ifile).split('_')[0]
            input_fcsv=glob.glob(os.path.join(config['input_dir'],f'{sub}*.fcsv'))
            
            if input_fcsv:
                
                landmarks_txt=os.path.join(config['output_dir'], idir+'_labels', os.path.basename(ifile).split('.nii')[0] + '_landmarks.txt')
                output_mask=os.path.join(config['output_dir'], idir+'_labels', os.path.basename(ifile).split('.nii')[0] + '_afids.nii.gz')
                
                if not os.path.exists(landmarks_txt):
                    fcsv_df = pd.read_csv(input_fcsv[0], sep=',', header=2)
                    
                    coords = fcsv_df[['x','y','z']].to_numpy()
                    with open (landmarks_txt, 'w') as fid:
                        for i in range(len(coords)):
                            fid.write(' '.join(str(i) for i in np.r_[np.round(coords[i,:],3),int(1)])+ "\n")
                
                if not os.path.exists(output_mask):
                    #--- Build c3d Command
                    c3d_cmd = f"{c3d_path} {ifile} -scale 0 -landmarks-to-spheres {landmarks_txt} 1 -o {output_mask}"
                    
                    #--- Run c3d command
                    print (f'Starting landmark mask for {os.path.basename(ifile)}')
                    process = subprocess.call(c3d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
                    
                    #--- c3d does not allow zero labels, need to change 0 labels to 2
                    seg = nibabel.load(output_mask)
                    data = seg.get_fdata()
                    data[data==0]=2
                    
                    ni_img = nibabel.Nifti1Image(data, seg.affine)
                    nibabel.save(ni_img, output_mask)
                
                if not os.path.exists(os.path.join(config['output_dir'], idir, os.path.basename(ifile))):
                    shutil.copyfile(ifile, os.path.join(config['output_dir'], idir, os.path.basename(ifile)))

if __name__ == "__main__":
    
    main()





