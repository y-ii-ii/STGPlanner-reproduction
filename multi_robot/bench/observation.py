"""Known-pose sparse-map fusion. Full snapshots replace one source, never add odds twice."""
import copy, hashlib, json, math
import numpy as np

def transform(points, position, quaternion):
    x,y,z,w=quaternion
    norm=x*x+y*y+z*z+w*w
    if not math.isfinite(norm) or abs(norm-1)>1e-3:raise ValueError('invalid quaternion')
    rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                       [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                       [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    return np.asarray(points).dot(rotation.T)+np.asarray(position)

def grid(points,resolution=.4):return np.floor(np.asarray(points)/resolution).astype(np.int64)

def peer_keep(world_points,peer,stamp,max_age=.35):
    """Drop only measured peer-body hits; no clearing ray or synthetic endpoint."""
    points=np.asarray(world_points);keep=np.ones(len(points),dtype=bool)
    if peer is None or abs(stamp-peer['stamp'])>max_age:return keep,False
    p=points-np.asarray(peer['position']);yaw=peer['yaw'];c=math.cos(yaw);s=math.sin(yaw)
    x=c*p[:,0]+s*p[:,1];y=-s*p[:,0]+c*p[:,1]
    hits=(abs(x)<=.65)&(abs(y)<=.55)&(p[:,2]>=-.18)&(p[:,2]<=.80)
    return ~hits,True
