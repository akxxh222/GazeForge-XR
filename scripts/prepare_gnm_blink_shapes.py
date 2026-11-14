"""Decode pinned GNM semantic wink weights as data and export native deltas.

Runs in CPython with NumPy/h5py. Reads only allowlisted Dense/ReLU layers;
does not deserialize Keras functions or execute downloaded model code.
"""
import hashlib
import json
from pathlib import Path
import h5py
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    model=ROOT/'assets/gnm/semantic/expression_decoder_model.h5'
    sha=hashlib.sha256(model.read_bytes()).hexdigest()
    if sha!='5eba165f8a414f73b24be96963d0a17e708c0856739ed85a19031f318dfb51e6':
        raise ValueError('Expression decoder source checksum changed')
    outputs={}
    with h5py.File(model,'r') as f:
        config=json.loads(f.attrs['model_config'])['config']
        for label,index in [('L',13),('R',14)]:
            values={}
            for layer in config['layers']:
                c=layer['config']
                kind=layer['class_name']
                name=c['name']
                if kind=='InputLayer':
                    values[name]=np.zeros((1,c['batch_input_shape'][-1]),np.float32)
                    if name=='decoder_label_input':values[name][0,index]=1
                    continue
                inputs=[values[n[0]] for n in layer['inbound_nodes'][0]]
                if kind=='Concatenate':
                    values[name]=np.concatenate(inputs,axis=c['axis'])
                elif kind=='Dense':
                    group=f['model_weights'][name][name]
                    output=inputs[0]@np.asarray(group['kernel:0'])+np.asarray(group['bias:0'])
                    if c['activation']=='relu':output=np.maximum(output,0)
                    elif c['activation']!='linear':raise ValueError('Unrecognized activation')
                    values[name]=output
                else:raise ValueError('Unrecognized serialized model layer: '+kind)
            outputs[label]=values[config['output_layers'][0][0]].reshape(-1)
    source=ROOT/'assets/gnm/gnm_head.npz'
    if hashlib.sha256(source.read_bytes()).hexdigest()!='61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb':
        raise ValueError('Native GNM source checksum changed')
    with np.load(source,allow_pickle=False) as data:
        basis=data['expression_basis']
        names=data['expression_names'].tolist()
        result={}
        transform=np.array([[1,0,0],[0,0,1],[0,-1,0]],np.float32)
        for side,prefix in [('L','left_eye_region_'),('R','right_eye_region_')]:
            indices=[i for i,name in enumerate(names) if name.startswith(prefix)]
            if len(indices)!=100:raise ValueError('Native eye expression region changed')
            weights=np.zeros(383,np.float32)
            weights[indices]=outputs[side][indices]
            result['delta_'+side]=np.tensordot(weights,basis,axes=1)@transform
            result['coefficients_'+side]=weights
    out=ROOT/'work/gnm/blink_shapes.npz'
    np.savez_compressed(out,**result)
    receipt={'decoder_sha256':sha,'source':'Official Google GNM expression decoder; zero latent, wink classes 13/14, corresponding 100 eye-region components only.',
             'license':'Apache-2.0, copyright 2026 Google LLC',
             'modifications':'Deterministic Dense/ReLU forward pass; isolate each native eye region; convert native deltas to project world axes. No geometry/UV replacement.',
             'artifact_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
             'max_delta_m':{s:float(np.linalg.norm(result['delta_'+s],axis=1).max()) for s in ('L','R')},
             'status':'Milestone 3 prototype input; closure, corneal clearance and attachments need pose/render validation.'}
    (out.with_suffix('.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print('GNM_BLINK_SHAPES',json.dumps(receipt),flush=True)


if __name__=='__main__':main()
