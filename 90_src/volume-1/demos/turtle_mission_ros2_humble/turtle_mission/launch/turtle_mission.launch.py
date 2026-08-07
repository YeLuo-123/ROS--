"""Launch the integrated TurtleMission system in one namespace."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml


def load_parameters() -> dict[str, dict]:
    config_path = (
        Path(get_package_share_directory('turtle_mission'))
        / 'config' / 'mission.yaml'
    )
    data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    return {
        name: section['ros__parameters']
        for name, section in data.items()
    }


def generate_launch_description() -> LaunchDescription:
    parameters = load_parameters()
    namespace = LaunchConfiguration('namespace')
    auto_start = LaunchConfiguration('auto_start')
    record_bag = LaunchConfiguration('record_bag')
    bag_name = LaunchConfiguration('bag_name')

    safety_remappings = [
        ('/turtle1/pose', 'turtle1/pose'),
        ('/turtle_goal/cmd_vel_raw', 'turtle_goal/cmd_vel_raw'),
        ('/turtle1/cmd_vel', 'turtle1/cmd_vel'),
        ('/turtle_guard/status', 'turtle_guard/status'),
        ('/turtle_guard/enable', 'turtle_guard/enable'),
    ]
    painter_remappings = [
        ('/turtle1/pose', 'turtle1/pose'),
        ('/turtle_goal/cmd_vel_raw', 'turtle_goal/cmd_vel_raw'),
        ('/turtle1/set_pen', 'turtle1/set_pen'),
        ('/turtle_painter/draw_shape', 'turtle_painter/draw_shape'),
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='mission',
            description='Namespace shared by all TurtleMission nodes.',
        ),
        DeclareLaunchArgument(
            'auto_start',
            default_value='true',
            description='Automatically submit the YAML mission.',
        ),
        DeclareLaunchArgument(
            'record_bag',
            default_value='false',
            description='Record all discovered topics with rosbag2.',
        ),
        DeclareLaunchArgument(
            'bag_name',
            default_value='turtle_mission_bag',
            description='Output directory used by ros2 bag record.',
        ),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            namespace=namespace,
            name='simulator',
            output='screen',
        ),
        Node(
            package='turtle_guard',
            executable='safety_guard',
            namespace=namespace,
            name='safety_guard',
            parameters=[parameters['safety_guard']],
            remappings=safety_remappings,
            output='screen',
        ),
        Node(
            package='turtle_painter',
            executable='painter_server.py',
            namespace=namespace,
            name='turtle_painter_server',
            parameters=[parameters['turtle_painter_server']],
            remappings=painter_remappings,
            output='screen',
        ),
        Node(
            package='turtle_mission',
            executable='performance_logger',
            namespace=namespace,
            name='performance_logger',
            parameters=[parameters['performance_logger']],
            output='screen',
        ),
        TimerAction(
            period=2.0,
            actions=[Node(
                package='turtle_mission',
                executable='mission_runner',
                namespace=namespace,
                name='mission_runner',
                parameters=[parameters['mission_runner']],
                condition=IfCondition(auto_start),
                output='screen',
            )],
        ),
        ExecuteProcess(
            cmd=['ros2', 'bag', 'record', '-a', '-o', bag_name],
            condition=IfCondition(record_bag),
            output='screen',
        ),
    ])
