"""Virtual fence and command safety layer for turtlesim."""

from __future__ import annotations

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from std_srvs.srv import SetBool
from turtlesim.msg import Pose


NUMERIC_PARAMETERS = (
    'world_min', 'world_max', 'safe_margin', 'warning_margin',
    'max_linear_speed', 'max_angular_speed', 'recovery_speed',
    'recovery_angular_gain', 'recovery_heading_tolerance',
    'command_timeout', 'control_rate',
)


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class SafetyGuard(Node):
    """Filter raw commands according to a parameterized virtual fence."""

    def __init__(self) -> None:
        super().__init__('safety_guard')
        defaults = {
            'enabled': True,
            'world_min': 0.0,
            'world_max': 11.0,
            'safe_margin': 1.0,
            'warning_margin': 2.0,
            'max_linear_speed': 2.0,
            'max_angular_speed': 2.5,
            'recovery_speed': 0.5,
            'recovery_angular_gain': 3.0,
            'recovery_heading_tolerance': 0.20,
            'command_timeout': 0.5,
            'control_rate': 20.0,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

        self._pose: Pose | None = None
        self._raw_command: Twist | None = None
        self._raw_received_at = 0.0
        self._last_mode = ''

        self._safe_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self._status_pub = self.create_publisher(
            String, '/turtle_guard/status', 10
        )
        self.create_subscription(Pose, '/turtle1/pose', self._on_pose, 10)
        self.create_subscription(
            Twist, '/turtle_goal/cmd_vel_raw', self._on_raw_command, 10
        )
        self.create_service(SetBool, '/turtle_guard/enable', self._on_enable)
        self.add_on_set_parameters_callback(self._validate_parameters)

        initial_config = self._configuration()
        initial_error = self._configuration_error(initial_config)
        if initial_error:
            raise ValueError(f'Invalid initial configuration: {initial_error}')
        rate = initial_config['control_rate']
        self.create_timer(1.0 / rate, self._control)
        self.get_logger().info(
            'TurtleGuard ready; service: /turtle_guard/enable'
        )

    def _on_pose(self, message: Pose) -> None:
        self._pose = message

    def _on_raw_command(self, message: Twist) -> None:
        self._raw_command = message
        self._raw_received_at = time.monotonic()

    def _configuration(self) -> dict[str, float]:
        return {
            name: float(self.get_parameter(name).value)
            for name in NUMERIC_PARAMETERS
        }

    def _validate_parameters(
        self, parameters: list[Parameter]
    ) -> SetParametersResult:
        candidate = self._configuration()
        enabled = bool(self.get_parameter('enabled').value)
        for parameter in parameters:
            if parameter.name in NUMERIC_PARAMETERS:
                try:
                    candidate[parameter.name] = float(parameter.value)
                except (TypeError, ValueError):
                    return SetParametersResult(
                        successful=False,
                        reason=f'{parameter.name} must be numeric',
                    )
            elif parameter.name == 'enabled':
                if parameter.type_ != Parameter.Type.BOOL:
                    return SetParametersResult(
                        successful=False, reason='enabled must be boolean'
                    )
                enabled = bool(parameter.value)
            else:
                return SetParametersResult(
                    successful=False,
                    reason=f'unsupported parameter: {parameter.name}',
                )

        reason = self._configuration_error(candidate)
        if reason:
            return SetParametersResult(successful=False, reason=reason)
        del enabled  # Type validation above is the only boolean constraint.
        return SetParametersResult(successful=True)

    @staticmethod
    def _configuration_error(config: dict[str, float]) -> str:
        if not all(math.isfinite(value) for value in config.values()):
            return 'numeric parameters must be finite'
        if config['world_max'] <= config['world_min']:
            return 'world_max must be greater than world_min'
        if config['safe_margin'] <= 0.0:
            return 'safe_margin must be greater than 0'
        if config['warning_margin'] <= config['safe_margin']:
            return 'warning_margin must be greater than safe_margin'
        width = config['world_max'] - config['world_min']
        if 2.0 * config['warning_margin'] >= width:
            return 'warning margins must leave a normal region'
        positive = (
            'max_linear_speed', 'max_angular_speed', 'recovery_speed',
            'recovery_angular_gain', 'recovery_heading_tolerance',
            'command_timeout', 'control_rate',
        )
        if any(config[name] <= 0.0 for name in positive):
            return 'speed, gain, tolerance, timeout and rate must be positive'
        return ''

    def _on_enable(
        self, request: SetBool.Request, response: SetBool.Response
    ) -> SetBool.Response:
        results = self.set_parameters([
            Parameter('enabled', Parameter.Type.BOOL, request.data)
        ])
        response.success = bool(results and results[0].successful)
        response.message = (
            f'TurtleGuard enabled={request.data}'
            if response.success else results[0].reason
        )
        return response

    def _bounded(self, raw: Twist, config: dict[str, float]) -> Twist:
        command = Twist()
        command.linear.x = clamp(
            raw.linear.x, 0.0, config['max_linear_speed']
        )
        command.angular.z = clamp(
            raw.angular.z,
            -config['max_angular_speed'],
            config['max_angular_speed'],
        )
        return command

    def _boundary_distance(self, config: dict[str, float]) -> float:
        assert self._pose is not None
        return min(
            self._pose.x - config['world_min'],
            config['world_max'] - self._pose.x,
            self._pose.y - config['world_min'],
            config['world_max'] - self._pose.y,
        )

    def _recovery_command(self, config: dict[str, float]) -> Twist:
        assert self._pose is not None
        center = (config['world_min'] + config['world_max']) / 2.0
        desired = math.atan2(center - self._pose.y, center - self._pose.x)
        error = normalize_angle(desired - self._pose.theta)
        command = Twist()
        command.angular.z = clamp(
            config['recovery_angular_gain'] * error,
            -config['max_angular_speed'],
            config['max_angular_speed'],
        )
        if abs(error) <= config['recovery_heading_tolerance']:
            command.linear.x = min(
                config['recovery_speed'], config['max_linear_speed']
            )
        return command

    def _publish_mode(self, mode: str, distance: float | None = None) -> None:
        detail = mode if distance is None else f'{mode}; distance={distance:.3f}'
        self._status_pub.publish(String(data=detail))
        if mode != self._last_mode:
            log = self.get_logger().warning if mode in {
                'WARNING', 'DANGER', 'COMMAND_TIMEOUT'
            } else self.get_logger().info
            log(detail)
            self._last_mode = mode

    def _control(self) -> None:
        if self._pose is None:
            self.stop()
            self._publish_mode('WAITING_POSE')
            return
        if self._raw_command is None:
            self.stop()
            self._publish_mode('WAITING_COMMAND')
            return

        config = self._configuration()
        error = self._configuration_error(config)
        if error:
            self.stop()
            self._publish_mode('INVALID_CONFIGURATION')
            self.get_logger().error(error)
            return
        if time.monotonic() - self._raw_received_at > config['command_timeout']:
            self.stop()
            self._publish_mode('COMMAND_TIMEOUT')
            return

        bounded = self._bounded(self._raw_command, config)
        if not bool(self.get_parameter('enabled').value):
            self._safe_pub.publish(bounded)
            self._publish_mode('DISABLED')
            return

        distance = self._boundary_distance(config)
        if distance <= config['safe_margin']:
            self._safe_pub.publish(self._recovery_command(config))
            self._publish_mode('DANGER', distance)
        elif distance <= config['warning_margin']:
            scale = (
                (distance - config['safe_margin'])
                / (config['warning_margin'] - config['safe_margin'])
            )
            bounded.linear.x *= clamp(scale, 0.0, 1.0)
            self._safe_pub.publish(bounded)
            self._publish_mode('WARNING', distance)
        else:
            self._safe_pub.publish(bounded)
            self._publish_mode('NORMAL', distance)

    def stop(self) -> None:
        self._safe_pub.publish(Twist())


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SafetyGuard()
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
