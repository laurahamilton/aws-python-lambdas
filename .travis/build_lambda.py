import sys
import os
import glob
import yaml
from distutils.dir_util import copy_tree
import shutil
import argparse
import boto3
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# build the lambda in travis
# for i in src/*/; do python .travis/build_lambda.py "$i"; done
lambda_path = sys.argv[1]

# lambda_path = 'src/hello_world/'
logger.info('Building lambda in {}'.format(lambda_path))

# path
config_path = os.path.join(lambda_path, 'config.yml')
conda_env_name = 'aws-python-lambdas'
conda_path = os.path.join(os.environ['HOME'], 'miniconda3')
conda_pkgs_path = os.path.join(os.environ['HOME'], 'miniconda3', 'pkgs')
conda_env_path = os.path.join(conda_path, 'envs', conda_env_name)
site_packages_path = os.path.join(conda_env_path, 'lib', 'python3.6', 'site-packages')

# read config of lambda
with open(config_path, 'r') as stream:
    lambda_cfg = yaml.load(stream)

logger.debug(lambda_cfg)

# create a tmp path for the lambda function
tmp_dir = os.path.join('tmp', lambda_path.replace('src/', ''))
os.makedirs(tmp_dir)

# copy lambda function content to tmp dir
r = copy_tree(lambda_path, tmp_dir)

if 'libs' not in lambda_cfg.keys():
    lambda_cfg['libs'] = []

# create paths to be copied for the libs
libs_paths = []
libs = lambda_cfg['libs']
for l in libs:
    lib_path = os.path.join(site_packages_path, l)
    logger.info(glob.glob(lib_path))
    lib_files = glob.glob(os.path.join(site_packages_path, l))
    if len(lib_files) == 0:
        logger.debug('trying to add single file')
        lib_path = os.path.join(site_packages_path, l) + '.py'
        lib_files = glob.glob(lib_path)
        logger.info('Found {}'.format(lib_files))
    libs_paths.extend(lib_files)

# copy all libs to build folder
for p in libs_paths:
    if '.py' in p:
        logger.info('Copying file {} to {}'.format(p, tmp_dir))
        shutil.copy2(p, tmp_dir)
    else:
        dst = os.path.join(tmp_dir, p.split('/')[-1])
        logger.info('Copying tree path {} to {}'.format(p, dst))
        t = copy_tree(p, dst)

if 'numpy' in libs:
    logger.info('Copy needed libs for numpy')

    shutil.copy2(os.path.join(conda_env_path, 'lib', 'libmkl_intel_lp64.so'), tmp_dir)
    shutil.copy2(os.path.join(conda_env_path, 'lib', 'libmkl_intel_thread.so'), tmp_dir)
    shutil.copy2(os.path.join(conda_env_path, 'lib', 'libmkl_core.so'), tmp_dir)
    shutil.copy2(os.path.join(conda_env_path, 'lib', 'libiomp5.so'), tmp_dir)

# create zip
zip_file_dst = os.path.join('dist', lambda_path.split('/')[-2])
logger.info('creating {}'.format(zip_file_dst + '.zip'))
shutil.make_archive(zip_file_dst, 'zip', tmp_dir)

# clean tmp path for the lambda
shutil.rmtree(tmp_dir)