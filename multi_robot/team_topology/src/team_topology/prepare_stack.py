"""Generate an isolated candidate stack, offline. Never launches any process."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def set_param(node, name, value):
    for old in list(node.findall("param")):
        if old.get("name") == name:
            node.remove(old)
    ET.SubElement(node, "param", name=name, value=str(value).lower() if isinstance(value,bool) else str(value))


def set_remap(node, name, value):
    for old in list(node.findall("remap")):
        if old.get("from") == name:
            node.remove(old)
    ET.SubElement(node,"remap",{"from":name,"to":value})


def transform(root, runtime_home, native_workspace):
    owned={"topo_planner_node","path_execution_node","explorer_node"}
    for node in list(root.findall("node")):
        root.remove(node)  # Historical externally owned command gates are not reused.
    for group in root.findall("group"):
        robot=group.get("ns")
        if robot not in ("robot_1","robot_2"):
            raise ValueError("unexpected robot group")
        prefix="/"+robot
        for node in group.findall("node"):
            name=node.get("name")
            for env in list(node.findall("env")):
                if env.get("name") in ("ROS_HOME","ROS_PACKAGE_PATH","LD_LIBRARY_PATH"):
                    node.remove(env)
            ET.SubElement(node,"env",name="ROS_HOME",value=runtime_home+"/"+robot+"/"+name+"/ros_home")
            if name in owned:
                set_param(node,"team/topology_enabled",True)
                set_param(node,"team/robot_id",int(robot[-1]))
                new_paths=":".join(native_workspace+"/src/"+x for x in
                    ("planner","control_planner_interface","path_execution","explorer","team_topology"))
                ET.SubElement(node,"env",name="ROS_PACKAGE_PATH",value=new_paths+":$(optenv ROS_PACKAGE_PATH)")
                ET.SubElement(node,"env",name="LD_LIBRARY_PATH",value=native_workspace+"/devel/lib:$(optenv LD_LIBRARY_PATH)")
            if name=="topo_planner_node":
                set_param(node,"team/shared_sensor_mapping",False)
                set_param(node,"team/robot_count",2)
                set_param(node,"execution_repair/cmu_terrain_input",True)
                set_remap(node,"point_cloud",prefix+"/velodyne/velodyne_points")
                set_remap(node,"sensor_odometry",prefix+"/sensor_to_world/odometry")
                for remap in list(node.findall("remap")):
                    if remap.get("from") in ("remote_point_cloud","remote_sensor_odometry"):
                        node.remove(remap)
            if name=="pathFollower":
                set_remap(node,"/cmd_vel",prefix+"/topology/raw_cmd_vel")
            if name in ("pathFollower","localPlanner"):
                set_param(node,"maxSpeed",2.);set_param(node,"autonomySpeed",2.)
        if group.find("node[@name='explorer_node']") is None:
            node=ET.SubElement(group,"node",pkg="exploration_manager",type="explorer_node",name="explorer_node",output="log")
            for a,b in [("odometry",prefix+"/base_link/odometry"),
                ("vehicle_execute",prefix+"/path_execution_node/vehicle_execute"),
                ("vehicle_stop",prefix+"/path_execution_node/vehicle_stop"),
                ("topo_planner",prefix+"/topo_planner_node/topo_planner"),
                ("topo_planner_msgs",prefix+"/topo_planner_node/topo_planner_msgs")]:
                set_remap(node,a,b)
            for a,b in [("team/topology_enabled",True),("team/robot_id",int(robot[-1])),
                         ("frame_id","world"),("run_mode","kSim"),("init_motion_enable",False)]:
                set_param(node,a,b)
            ET.SubElement(node,"env",name="ROS_HOME",value=runtime_home+"/"+robot+"/explorer_node/ros_home")
            ET.SubElement(node,"env",name="LD_LIBRARY_PATH",value=native_workspace+"/devel/lib:$(optenv LD_LIBRARY_PATH)")
    ET.SubElement(root,"include",file="$(find team_topology)/launch/collaboration.launch")
    validate(root)
    return root


def validate(root):
    groups=root.findall("group")
    if {g.get("ns") for g in groups}!={"robot_1","robot_2"}:
        raise ValueError("exactly two isolated robot groups required")
    for g in groups:
        prefix="/"+g.get("ns")
        follower=g.find("node[@name='pathFollower']")
        remaps={r.get("from"):r.get("to") for r in g.findall("remap")+follower.findall("remap")}
        if remaps.get("/cmd_vel")!=prefix+"/topology/raw_cmd_vel":
            raise ValueError("follower bypasses final velocity fence")
        for name in ("topo_planner_node","path_execution_node","explorer_node"):
            node=g.find("node[@name='%s']"%name)
            if node is None or node.find("param[@name='team/topology_enabled']").get("value")!="true":
                raise ValueError("mixed native ABI or disabled execution fencing")
        planner=g.find("node[@name='topo_planner_node']")
        if planner.find("param[@name='team/shared_sensor_mapping']").get("value")!="false":
            raise ValueError("remote point-cloud fusion still enabled")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-stack",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--runtime-home",required=True)
    parser.add_argument("--native-workspace",default="/opt/stgplanner/team_topology_native_task_20261116_ws")
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("output already exists; preserve previous artifacts")
    if "benchmarks/results" in args.output.resolve().as_posix():
        raise ValueError("never write a candidate stack into historical results")
    root=transform(ET.parse(args.source_stack).getroot(),args.runtime_home,args.native_workspace)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if hasattr(ET,"indent"):ET.indent(root)  # ROS Noetic's Python 3.8 has no ET.indent.
    ET.ElementTree(root).write(args.output,encoding="utf-8",xml_declaration=True)


if __name__=="__main__":main()
