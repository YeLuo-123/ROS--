"""Closed-loop TurtleGoal controller for ROS 2 Humble and turtlesim."""

from __future__ import annotations

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from turtlesim.msg import Pose


def clamp(value: float, lower: float, upper: float) -> float:
    """Limit value to the inclusive interval [lower, upper]."""
    return max(lower, min(value, upper))


def normalize_angle(angle: float) -> float:
    """Normalize an angle to [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


class TurtleGoalController(Node):
    """Drive turtle1 to a parameterized 2-D target using pose feedback."""

    def __init__(self) -> None:
        super().__init__('turtle_goal_controller')

        self.declare_parameter('target_x', 8.0)
        self.declare_parameter('target_y', 8.0)
        self.declare_parameter('linear_gain', 1.0)
        self.declare_parameter('angular_gain', 4.0)
        self.declare_parameter('max_linear_speed', 2.0)
        self.declare_parameter('max_angular_speed', 2.5)
        self.declare_parameter('distance_tolerance', 0.05)
        self.declare_parameter('heading_tolerance', 0.20)
        self.declare_parameter('control_rate', 20.0)

        self._pose: Pose | None = None
        self._goal_reached = False
        self._waiting_logged = False
        self._last_goal: tuple[float, float] | None = None
        self._last_config_error: str | None = None
        self._goal_started_at = time.monotonic()

        self._cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self._pose_sub = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self._pose_callback,
            10,
        )

        control_rate = float(self.get_parameter('control_rate').value)
        if not math.isfinite(control_rate) or control_rate <= 0.0:
            raise ValueError('control_rate must be a finite value greater than 0')
        self._control_timer = self.create_timer(
            1.0 / control_rate,
            self._control_callback,
        )

        self.get_logger().info(
            'TurtleGoal ready: waiting for /turtle1/pose.'
        )

    def _pose_callback(self, message: Pose) -> None:
        self._pose = message

    def _read_configuration(self) -> dict[str, float] | None:
        names = (
            'target_x',
            'target_y',
            'linear_gain',
            'angular_gain',
            'max_linear_speed',
            'max_angular_speed',
            'distance_tolerance',
            'heading_tolerance',
        )
        config = {
            name: float(self.get_parameter(name).value)
            for name in names
        }

        if not all(math.isfinite(value) for value in config.values()):
            self._report_config_error('all numeric parameters must be finite')
            return None
        if not (0.5 <= config['target_x'] <= 10.5):
            self._report_config_error('target_x must be in [0.5, 10.5]')
            return None
        if not (0.5 <= config['target_y'] <= 10.5):
            self._report_config_error('target_y must be in [0.5, 10.5]')
            return None
        positive_names = (
            'linear_gain',
            'angular_gain',
            'max_linear_speed',
            'max_angular_speed',
            'distance_tolerance',
            'heading_tolerance',
        )
        if any(config[name] <= 0.0 for name in positive_names):
            self._report_config_error(
                'gains, speed limits, and tolerances must be greater than 0'
            )
            return None

        self._last_config_error = None
        return config

    def _report_config_error(self, message: str) -> None:
        if message != self._last_config_error:
            self.get_logger().error(f'Invalid configuration: {message}')
            self._last_config_error = message
        self.stop()

    def _control_callback(self) -> None:
        if self._pose is None:
            if not self._waiting_logged:
                self.get_logger().warning(
                    'No pose received. Is turtlesim_node running?'
                )
                self._waiting_logged = True
            return

        config = self._read_configuration()
        if config is None:
            return

        goal = (config['target_x'], config['target_y'])
        if goal != self._last_goal:
            self._last_goal = goal
            self._goal_reached = False
            self._goal_started_at = time.monotonic()
            self.get_logger().info(
                f'New goal accepted: x={goal[0]:.3f}, y={goal[1]:.3f}'
            )

        dx = goal[0] - self._pose.x
        dy = goal[1] - self._pose.y
        distance = math.hypot(dx, dy)

        if distance <= config['distance_tolerance']:
            self.stop()
            if not self._goal_reached:
                elapsed = time.monotonic() - self._goal_started_at
                self.get_logger().info(
                    'Goal reached: '
                    f'x={self._pose.x:.3f}, y={self._pose.y:.3f}, '
                    f'error={distance:.4f} m, time={elapsed:.2f} s'
                )
                self._goal_reached = True
            return

        desired_heading = math.atan2(dy, dx)
        heading_error = normalize_angle(desired_heading - self._pose.theta)

        command = Twist()
        command.angular.z = clamp(
            config['angular_gain'] * heading_error,
            -config['max_angular_speed'],
            config['max_angular_speed'],
        )
        if abs(heading_error) <= config['heading_tolerance']:
            command.linear.x = clamp(
                config['linear_gain'] * distance,
                0.0,
                config['max_linear_speed'],
            )

        self._cmd_pub.publish(command)

    def stop(self) -> None:
        """Publish a zero command while the publisher is still valid."""
        self._cmd_pub.publish(Twist())


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TurtleGoalController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
