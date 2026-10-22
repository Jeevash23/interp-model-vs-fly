"""Batched explicit Euler equation from pinned FlyVis; validated against native.

Gains scale rectified outgoing voltage; cell state and feedback remain free.
All parameters detached/frozen except the supplied attenuation coordinates.
"""
from common import *
import numpy as np,torch
from torch.utils.checkpoint import checkpoint
TARGETS=['T4a','T4b','T4c','T4d','T5a','T5b','T5c','T5d']
PAIRS=[('Mi1','Tm3'),('Mi1','Mi4'),('Tm3','Mi4'),('Mi4','Mi9'),('Tm1','Tm2'),('Tm1','Tm9'),('Tm2','Tm4'),('Tm4','Tm9')]
class Core:
 def __init__(self,model='000',device='cpu'):
  # Native package initialized/recovered on CPU; caller holds GPU lock before import.
  import flyvis
  torch.set_default_device('cpu');flyvis.device=torch.device('cpu')
  # This pinned module copies flyvis.device at import; keep initialization and
  # its generator on CPU before recovering the fixed checkpoint values.
  import importlib
  initialization=importlib.import_module('flyvis.network.initialization')
  initialization.device=torch.device('cpu')
  self.native=flyvis.NetworkView(flyvis.results_dir/f'flow/0000/{model}').init_network()
  self.native.clamp();p=self.native._param_api();self.device=torch.device(device);self.model=model
  self.source=self.native._source_indices.to(self.device);self.target=self.native._target_indices.to(self.device)
  self.weight=p.edges.weight.detach().to(self.device);self.bias=p.nodes.bias.detach().to(self.device);self.tau=p.nodes.time_const.detach().to(self.device)
  self.n=self.native.n_nodes;self.e=self.native.n_edges
  nt=self.native.connectome.nodes.type[:].astype(str);self.names=list(dict.fromkeys(nt.tolist()));self.c=len(self.names);lookup={x:i for i,x in enumerate(self.names)}
  self.types=torch.tensor([lookup[x] for x in nt],dtype=torch.long,device=self.device)
  central=self.native.connectome.central_cells_index[:];self.readout=torch.tensor([int(central[np.flatnonzero(nt[central]==x)[0]]) for x in TARGETS],device=self.device)
  self.input=torch.tensor(np.asarray(self.native.stimulus.input_index),device=self.device,dtype=torch.long)
  src=self.source.cpu().numpy();tar=self.target.cpu().numpy();read=self.readout.cpu().numpy();pick=np.flatnonzero(np.isin(tar,read));self.cur_edge=torch.tensor(pick,device=self.device);self.cur_src=self.source[self.cur_edge];self.cur_group=torch.tensor([TARGETS.index(nt[tar[i]])*self.c+lookup[nt[src[i]]] for i in pick],device=self.device)
  self.cur_weight=self.weight[self.cur_edge];self.syn_counts=p.edges.syn_count.detach().cpu().numpy()
  self.node_names=nt;self.pairs=sorted(set(zip(nt[src],nt[tar])))
  # Graph reachability includes the target itself (zero-length path), conservative for outputs.
  ancestors=set(TARGETS)
  while True:
   new=ancestors|{a for a,b in self.pairs if b in ancestors}
   if new==ancestors:break
   ancestors=new
  self.zeros=[x for x in self.names if x not in ancestors]
  self.edge_zeros=[(a,b) for a,b in self.pairs if b not in ancestors]
  self.counts=np.zeros((8,self.c),dtype=np.float64)
  for i in pick:self.counts[TARGETS.index(nt[tar[i]]),lookup[nt[src[i]]]]+=float(self.syn_counts[i])
 def step(self,v,x,atten,dt):
  # (weight * relu(source)) attenuated by source class, no clamping of v.
  release=torch.relu(v)*(1-atten[:,self.types])
  edge=release[:,self.source]*self.weight
  current=torch.zeros_like(v).scatter_add(1,self.target[None].expand(v.shape[0],-1),edge)
  external=torch.zeros_like(v);external[:,self.input]=x[:,None,:].to(v.dtype)
  velocity=1/torch.maximum(self.tau,torch.tensor(dt,device=self.device,dtype=torch.float32))*(-v+self.bias+current+external)
  return v+velocity*dt
 @torch.no_grad()
 def gray(self,dt=.005):
  v=self.bias[None].clone();x=torch.full((1,self.input.shape[1]),.5,device=self.device);a=torch.zeros((1,self.c),device=self.device)
  for _ in range(int(1/dt)):v=self.step(v,x,a,dt)
  return v
 def run(self,frames,atten=None,state=None,start=200,dt=.005,grad=False,block=8,currents=False):
  frames=torch.as_tensor(frames,device=self.device,dtype=torch.float32)
  if frames.ndim==4:frames=frames[:,:,0]
  if frames.ndim!=3:raise ValueError('frames must be batch,time,hex')
  B,T,_=frames.shape
  if atten is None:atten=torch.zeros((B,self.c),device=self.device)
  if atten.ndim==1:atten=atten[None].expand(B,-1)
  if state is None:state=self.gray(dt).expand(B,-1).clone()
  v=state;zeros=torch.zeros_like(atten);outputs=[];cs=[]
  def segment(v,a,x,offset):
   trace=[]
   for k in range(x.shape[1]):
    mask=a if offset+k>=start else zeros
    v=self.step(v,x[:,k],mask,dt);trace.append(v[:,self.readout])
   return v,torch.stack(trace,1)
  with torch.set_grad_enabled(grad):
   if grad:
    for k in range(0,T,block):
     # Capture k as value so backward recomputation uses identical mask timing.
     fn=lambda vv,aa,xx,offset=k:segment(vv,aa,xx,offset)
     v,tr=checkpoint(fn,v,atten,frames[:,k:k+block],use_reentrant=False,preserve_rng_state=False);outputs.append(tr)
   else:
    for k in range(T):
     if currents:
      cur=(torch.relu(v[:,self.cur_src])*self.cur_weight).abs();agg=torch.zeros((B,8*self.c),device=self.device).scatter_add_(1,self.cur_group[None].expand(B,-1),cur);cs.append(agg.reshape(B,8,self.c))
     v=self.step(v,frames[:,k],atten if k>=start else zeros,dt);outputs.append(v[:,self.readout][:,None])
  result=torch.cat(outputs,1)
  if not bool(torch.isfinite(result).all()):raise FloatingPointError('Nonfinite batched output')
  return result,v,torch.stack(cs,1) if currents else None
 def metadata(self):return {'model':self.model,'nodes':self.n,'edges':self.e,'model_types':self.names,'realized_pairs':self.pairs,'structural_zero_types':self.zeros,'stage2_structural_zero_pairs':self.edge_zeros,'device':str(self.device)}

def metrics(trace,angles,intensities,speed,time_start=-1.,dt=.005):
 """Differentiable native DSI and per-trajectory raw means over native window."""
 B,T,R=trace.shape
 # Match the pinned native helper's arithmetic and original full-trial time
 # coordinates, including a boundary exactly on a sampled biological speed.
 end=((10*2.25/5.8+2.25/5.8)-(-10*2.25/5.8))/speed
 t=(np.arange(T,dtype=np.float64)+round((time_start+1)/dt))*dt-1
 sel=torch.as_tensor((t>=0)&(t<=end),device=trace.device)
 vals=trace[:,sel];peaks=vals.clamp_min(0).amax(1);raw=vals.mean(1);integral=vals.sum(1)*dt
 angle=torch.as_tensor(angles,device=trace.device,dtype=trace.dtype)*torch.pi/180;pol=torch.as_tensor(intensities,device=trace.device);sums=[];vectors=[]
 for intensity in [0,1]:
  ix=pol==intensity;p=peaks[ix];a=angle[ix];sums.append(p.sum(0));vectors.append(torch.stack([(p*torch.cos(a[:,None])).sum(0),(p*torch.sin(a[:,None])).sum(0)],0).norm(dim=0))
 den=torch.stack(sums).amax(0);dsi=torch.stack(vectors)/(den+1e-15);chosen=torch.stack([dsi[1 if i<4 else 0,i] for i in range(8)])
 return {'dsi':chosen,'all_dsi':dsi,'denominator':den,'peaks':peaks,'raw_mean':raw,'raw_integral':integral,'window':sel}
