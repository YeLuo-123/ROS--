"""Optional Chapter 9 launch file for the TurtleGoal demo."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory('turtle_goal')
    parameter_file = os.path.join(
        package_share,
        'config',
        'turtle_goal.yaml',
    )

    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            output='screen',
        ),
        Node(
            package='turtle_goal',
            executable='turtle_goal_node',
            name='turtle_goal_controller',
            parameters=[parameter_file],
            output='screen',
        ),
    ])
