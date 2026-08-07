from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'turtle_guard'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROS Textbook Project',
    maintainer_email='maintainer@example.com',
    description='ROS 2 Humble TurtleGuard virtual-fence teaching demo.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'goal_controller = turtle_guard.goal_controller:main',
            'safety_guard = turtle_guard.safety_guard:main',
        ],
    },
)
