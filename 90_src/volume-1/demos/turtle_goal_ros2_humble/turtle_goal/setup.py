from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'turtle_goal'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROS Textbook Project',
    maintainer_email='maintainer@example.com',
    description='ROS 2 Humble TurtleGoal closed-loop turtlesim teaching demo.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'turtle_goal_node = turtle_goal.controller:main',
        ],
    },
)
