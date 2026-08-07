"""Generate an unchecked TurtleGoal velocity command."""

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from turtlesim.msg import Pose


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class TurtleGoalController(Node):
    """Drive toward a goal, leaving safety decisions to safety_guard."""

    def __init__(self) -> None:
        super().__init__('turtle_goal_controller')
        defaults = {
            'target_x': 9.5,
            'target_y': 5.5,
            'linear_gain': 1.0,
            'angular_gain': 4.0,
            'max_linear_speed': 2.0,
            'max_angular_speed': 2.5,
            'distance_tolerance': 0.05,
            'heading_tolerance': 0.20,
            'control_rate': 20.0,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

        self._pose: Pose | None = None
        self._reached = False
        self._cmd_pub = self.create_publisher(
            Twist, '/turtle_goal/cmd_vel_raw', 10
        )
        self.create_subscription(Pose, '/turtle1/pose', self._on_pose, 10)
        rate = float(self.get_parameter('control_rate').value)
        if not math.isfinite(rate) or rate <= 0.0:
            raise ValueError('control_rate must be finite and greater than 0')
        self.create_timer(1.0 / rate, self._control)
        self.get_logger().info(
            'Goal controller ready; output: /turtle_goal/cmd_vel_raw'
        )

    def _on_pose(self, message: Pose) -> None:
        self._pose = message

    def _number(self, name: str) -> float:
        return float(self.get_parameter(name).value)

    def _control(self) -> None:
        if self._pose is None:
            return

        target_x = self._number('target_x')
        target_y = self._number('target_y')
        dx = target_x - self._pose.x
        dy = target_y - self._pose.y
        distance = math.hypot(dx, dy)

        command = Twist()
        if distance <= self._number('distance_tolerance'):
            self._cmd_pub.publish(command)
            if not self._reached:
                self.get_logger().info('Goal reached.')
                self._reached = True
            return

        self._reached = False
        heading_error = normalize_angle(
            math.atan2(dy, dx) - self._pose.theta
        )
        command.angular.z = clamp(
            self._number('angular_gain') * heading_error,
            -self._number('max_angular_speed'),
            self._number('max_angular_speed'),
        )
        if abs(heading_error) <= self._number('heading_tolerance'):
            command.linear.x = clamp(
                self._number('linear_gain') * distance,
                0.0,
                self._number('max_linear_speed'),
            )
        self._cmd_pub.publish(command)

    def stop(self) -> None:
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
