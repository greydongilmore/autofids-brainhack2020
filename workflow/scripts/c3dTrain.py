#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import yaml

script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
config_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'config/config.yml')

with open(config_path) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

c4d_path=os.path.join(config['c3d_path'],'c4d')


def main():
    
    input_files = os.path.join(config['output_dir'],'train_data','*.nii.gz')
    input_labels = os.path.join(config['output_dir'],'train_data_masks','*hardmask.nii.gz')
    
    model_fn=f"ntrees-{config['c3d']['model_params']['ntrees']}_tdepth-" \
        f"{config['c3d']['model_params']['treedepth']}_patch-{config['c3d']['model_params']['patch']}_model.rf"
    model_file = os.path.join(config['output_dir'], model_fn)
    
    extra=''
    if config['c3d']['model_params']['other']:
        extra=' '.join(['-'+x for x in config['c3d']['model_params']['other']])
        
    #--- Build c4d Command
    c4d_cmd = f"{c4d_path} -verbose {input_files} -foreach -popas ALLMRI -endfor {input_labels} " \
        f"-foreach -popas ALLSEG -endfor -rf-param-patch {config['c3d']['model_params']['patch']} " \
        f"-push ALLMRI -push ALLSEG -rf-param-treedepth {config['c3d']['model_params']['treedepth']} " \
        f"-rf-param-ntrees {config['c3d']['model_params']['ntrees']} {extra} -rf-train {model_file}"
    
    #--- Run c3d command
    print ('Starting model training...')
    process = subprocess.call(c4d_cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.PIPE)
    
    
if __name__ == "__main__":
    
    main()