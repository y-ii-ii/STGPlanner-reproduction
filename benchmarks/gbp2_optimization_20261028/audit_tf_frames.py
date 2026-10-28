"""Check cloud and synthetic sensor origins in the actual native map frame."""
import json
import sys
from pathlib import Path
import rospy
import tf
rospy.init_node('gbp2_tf_frame_audit',anonymous=True,disable_signals=True)
listener=tf.TransformListener()
value={'read_only':True,'transforms':{}}
for child in ['sensor','base_link','jackal/velodyne/VLP_16','map']:
    try:
        listener.waitForTransform('world',child,rospy.Time(0),rospy.Duration(6))
        translation,rotation=listener.lookupTransform('world',child,rospy.Time(0))
        value['transforms'][child]={'translation':translation,'rotation':rotation}
    except Exception as error:value['transforms'][child]={'error':str(error)}
target=Path(sys.argv[1])/'tf_frame_snapshot.json';assert not target.exists()
target.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
