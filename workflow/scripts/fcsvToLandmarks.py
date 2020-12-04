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
import ants

from skfuzzy import cmeans
from sklearn.model_selection import train_test_split
from nipype.interfaces.ants.segmentation import N4BiasFieldCorrection


#config_path='/home/greydon/Documents/GitHub/autofids-brainhack2020/config/config.yml'

script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
config_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'config/config.yml')

with open(config_path) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

os.environ['PATH'] += ':'+config['ants_path']
os.environ['PATH'] += ':'+config['c3d_path']

def fcm_class_mask(img_fn, landmark_fn):
    
    img = nibabel.load(img_fn)
    img_data = img.get_fdata()
    mask_data = img_data > img_data.mean()
    
    
    [t1_cntr, t1_mem, _, _, _, _, _] = cmeans(img_data[mask_data].reshape(-1, len(mask_data[mask_data])),config['preproc']['fcm']['num_class'], 2, 0.005, 50)
    t1_mem_list = [t1_mem[i] for i, _ in sorted(enumerate(t1_cntr), key=lambda x: x[1])]  # CSF/GM/WM
    
    # add 1 dimension for the landmark labels
    mask = np.zeros(img_data.shape + (config['preproc']['fcm']['num_class'],))
    for i in range(config['preproc']['fcm']['num_class']):
        mask[..., i][mask_data] = t1_mem_list[i]
    
    
    img_landmark = nibabel.load(landmark_fn)
    img_landmark_data = img_landmark.get_fdata()
    
    landmark_mem = 0.0001*np.zeros(img_data.shape+ (1,))
    landmark_mem[...,0][img_landmark_data==4]= 0.9999

    mask=np.append(mask, landmark_mem, axis=3)
    
    
    
    mask_hard = np.zeros(img_data.shape)
    mask_hard[mask_data] = np.argmax(mask[mask_data], axis=1) + 1
    nii_mask = nibabel.Nifti1Image(np.flip(mask, 1), img.affine, img.header)
    nii_mask_hard = nibabel.Nifti1Image(mask_hard, img.affine, img.header)
    
    if 'ct' not in os.path.basename(img_fn):
        tissue_mask_data = np.flip(mask, 1)[..., 2] > 0.8
        tissue_mean = img_data[tissue_mask_data > 0].mean()
        normalized = nibabel.Nifti1Image((img_data / tissue_mean) * config['preproc']['fcm']['norm_value'],
                                     img.affine, img.header)
        nibabel.save(normalized, img_fn)
    
    output_mask=os.path.join(os.path.dirname(img_fn)+'_masks', os.path.basename(img_fn).split('.nii')[0] + '_mask.nii.gz')
    nibabel.save(nii_mask, output_mask)
    
    output_mask_hard=os.path.join(os.path.dirname(img_fn)+'_masks', os.path.basename(img_fn).split('.nii')[0] + '_hardmask.nii.gz')
    nibabel.save(nii_mask_hard, output_mask_hard)
    
    
    
    return output_mask,output_mask_hard

def preprocess(img_fn):
    
    #--- replace any nan values in nifti file as number
    img = nibabel.load(img_fn)
    img_data = img.get_fdata()
    new_data = np.nan_to_num(img_data)
    
    #--- normalize if nifti file is CT
    if 'ct' in os.path.basename(img_fn):
        min = -1024
        max = 3071
        new_data[new_data < min] = min
        new_data[new_data > max] = max
        new_data = (new_data - min) / (max - min)
    
    new_image = nibabel.Nifti1Image(new_data, img.affine, img.header)
    nibabel.save(new_image, img_fn)
    
    #--- bias correction
    if config['preproc']['bias_correct']['perform']:
        n4 = N4BiasFieldCorrection()
        n4.inputs.input_image = img_fn
        n4.inputs.output_image = img_fn
    
        n4.inputs.dimension = config['preproc']['bias_correct']['dim']
        n4.inputs.n_iterations = config['preproc']['bias_correct']['n_iterations']
        n4.inputs.shrink_factor = config['preproc']['bias_correct']['shrink_factor']
        n4.inputs.convergence_threshold = config['preproc']['bias_correct']['convergence_threshold']
        n4.inputs.bspline_fitting_distance = config['preproc']['bias_correct']['bspline_fitting_distance']
        n4.run()
    
    #--- resample the image
    img = ants.image_read(img_fn)
    
    if config['preproc']['resample']['res'] != img.spacing:
        img = ants.resample_image(img, config['preproc']['resample']['res'], False, config['preproc']['resample']['interp'])
    
    ants.image_write(img, img_fn)


def main():
    nifti_files=glob.glob(os.path.join(config['input_dir'])+'/*.nii.gz')
    x_train ,x_test = train_test_split(nifti_files,test_size=0.2)
    
    dir_setup={'test_data','test_data_labels','test_prob','train_data','train_data_labels', 'test_data_masks', 'train_data_masks'}
    for ipath in dir_setup:
        if not os.path.exists(os.path.join(config['output_dir'],ipath)):
            os.makedirs(os.path.join(config['output_dir'],ipath))
    
    dir_dic = {
        'train_data': x_train,
        'test_data': x_test}
    
    tot_cnt=len(nifti_files)
    file_cnt=1
    for idir,ifiles in dir_dic.items():
        for ifile in ifiles:
            
            sub = os.path.basename(ifile).split('_')[0]
            input_fcsv=glob.glob(os.path.join(config['input_dir'],f'{sub}*.fcsv'))
            
            if input_fcsv:
                
                img_fn = os.path.join(config['output_dir'], idir, os.path.basename(ifile))
                
                if not os.path.exists(img_fn):
                    shutil.copyfile(ifile, img_fn)
                    
                    print (f'Pre-processing file {file_cnt} of {tot_cnt}: {os.path.basename(ifile)}')
                    preprocess(img_fn)
                
                landmarks_txt=os.path.join(config['output_dir'], idir+'_labels', os.path.basename(ifile).split('.nii')[0] + '_landmarks.txt')
                
                if not os.path.exists(landmarks_txt):
                    fcsv_df = pd.read_csv(input_fcsv[0], sep=',', header=2)
                    
                    coords = fcsv_df[['x','y','z']].to_numpy()
                    with open (landmarks_txt, 'w') as fid:
                        for i in range(len(coords)):
                            fid.write(' '.join(str(i) for i in np.r_[np.round(coords[i,:],3),int(config['c3d']['landmarks']['sphere_label'])])+ "\n")
                
                output_landmark_mask=os.path.join(config['output_dir'], idir+'_labels', os.path.basename(ifile).split('.nii')[0] + '_landmarks.nii.gz')
                
                if not os.path.exists(output_landmark_mask):
                    #--- Build c3d Command
                    c3d_cmd = f"{os.path.join(config['c3d_path'],'c3d')} {img_fn} -scale 0 -landmarks-to-spheres {landmarks_txt} {config['c3d']['landmarks']['sphere_size']} -o {output_landmark_mask}"
                    
                    #--- Run c3d command
                    print (f'Creating landmark mask for file {file_cnt} of {tot_cnt}: {os.path.basename(ifile)}')
                    process = subprocess.call(c3d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
                
                
                    print (f'Creating tissue mask for file {file_cnt} of {tot_cnt}: {os.path.basename(ifile)}\n')
                    output_mask,output_mask_hard=fcm_class_mask(img_fn, output_landmark_mask)
            
            file_cnt +=1

if __name__ == "__main__":
    
    main()





