"""Stage 1 paths, provenance, admission and native-equation batched execution."""
from pathlib import Path
import os,json,hashlib,time,resource
P=Path(__file__).resolve().parents[2]
OUT=P/'04-Results/stage1';DATA=P/'03-Data/stage1';HIST=P/'06-Study-History/stage1'
def save_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)));tmp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def configure():
 for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMBA_NUM_THREADS']:os.environ[k]='2'
 os.environ.setdefault('MPLBACKEND','Agg');os.environ['FLYVIS_ROOT_DIR']=str(P/'03-Data/flyvis-root');os.environ['MPLCONFIGDIR']=str(P/'.cache/matplotlib');os.environ['XDG_CACHE_HOME']=str(P/'.cache');os.environ['TIMEZONE']='UTC'
def admit():
 import shutil
 m=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
 if m<3*1024**2 or shutil.disk_usage(P).free<10*1024**3:raise RuntimeError('Resource admission failed')
def health(device=None):
 m=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
 if m<2*1024**2:raise RuntimeError('Stop own worker: available host RAM below2GiB')
 if device is not None and str(device).startswith('cuda'):
  import torch
  if torch.cuda.mem_get_info()[0]<1024**3:raise RuntimeError('Stop own worker: GPU free below1GiB')
def sync(device):
 if str(device).startswith('cuda'):
  import torch;torch.cuda.synchronize()
configure()
