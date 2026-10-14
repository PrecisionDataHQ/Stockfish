"""Build checksum-pinned Stockfish for a separate local chess process."""
from pathlib import Path
import argparse
import hashlib
import os
import shutil
import subprocess
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
PIN='edb0d9db6731067ec50ce619ff372b463bc4dd5d'
NET='nn-1a298aa575a0.nnue'
NET_SHA='1a298aa575a085434d29027978dc36867fe9c5bcea9376654b7a8eba1e52dfc2'
parser=argparse.ArgumentParser()
parser.add_argument('--target',choices=('android','macos'),default='android')
target=parser.parse_args().target
source=ROOT/'.sources/stockfish'
if not source.exists():
    subprocess.run(['git','clone','--depth','1','--branch','sf_19','https://github.com/official-stockfish/Stockfish.git',str(source)],check=True)
if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN or subprocess.run(['git','-C',str(source),'diff','--quiet']).returncode:
    raise SystemExit('Preserve changed Stockfish source; use the pinned clean release.')
work=ROOT/('build/stockfish-'+target+'-source')
shutil.copytree(source,work,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'))
network=work/'src'/NET
if network.exists() and hashlib.file_digest(network.open('rb'),'sha256').hexdigest()!=NET_SHA:
    raise SystemExit('Preserve the unexpected network file and review it before building.')
if not network.exists():
    temporary=network.with_name(NET+'.new')
    urllib.request.urlretrieve('https://media.githubusercontent.com/media/official-stockfish/networks/master/'+NET,temporary)
    if hashlib.file_digest(temporary.open('rb'),'sha256').hexdigest()!=NET_SHA:
        raise SystemExit('Network checksum mismatch; do not build or bundle it.')
    temporary.rename(network)
arguments=['make','-j4','build']
if target=='android':
    ndk=Path(os.environ.get('JOYORBIT_NATIVE_NDK',str(Path(os.environ['ANDROID_SDK_ROOT'])/'ndk/29.0.14206865')))
    compiler=ndk/'toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android24-clang++'
    arguments += ['ARCH=armv8','COMP=ndk','COMPCXX='+str(compiler)]
else:
    arguments += ['ARCH=apple-silicon','COMP=clang']
subprocess.run(arguments,cwd=work/'src',check=True)
output=ROOT/'build/stockfish'/target
output.mkdir(parents=True,exist_ok=True)
binary=output/('libjoyorbit_stockfish.so' if target=='android' else 'stockfish')
shutil.copy2(work/'src/stockfish',binary)
if target=='android':
    subprocess.run([str(compiler.parent/'llvm-strip'),'--strip-debug',str(binary)],check=True)
notices=ROOT/'theme/licenses'
shutil.copy2(source/'Copying.txt',notices/'Stockfish-GPL3.txt')
shutil.copy2(source/'AUTHORS',notices/'Stockfish-authors.txt')
(notices/'Stockfish-networks.txt').write_text('Stockfish19 neural network: '+NET+'\nSHA256 '+NET_SHA+'\n'+
    'Source: https://github.com/official-stockfish/networks\n'+
    'The Stockfish README acknowledges networks trained on Leela Chess Zero data available under ODbL.\n'+
    'Original acknowledgement: https://github.com/official-stockfish/Stockfish/blob/'+PIN+'/README.md\n')
print('Stockfish separate-process binary built:',binary)
