"""Record TurtleMission trajectory, commands, safety and mission events."""

from __future__ import annotations

import csv
from datetime import datetime
import json
from pathlib import Path
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String
from turtlesim.msg import Pose


class PerformanceLogger(Node):
    """Write synchronized snapshots to CSV and a JSON run summary."""

    def __init__(self) -> None:
        super().__init__('performance_logger')
        self.declare_parameter(
            'output_directory', '~/.ros/turtle_mission'
        )
        self.declare_parameter('sample_period', 0.1)
        period = float(self.get_parameter('sample_period').value)
        if period <= 0.0:
            raise ValueError('sample_period must be greater than 0')

        output = Path(str(
            self.get_parameter('output_directory').value
        )).expanduser()
        output.mkdir(parents=True, exist_ok=True)
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._csv_path = output / f'{run_id}_trajectory.csv'
        self._summary_path = output / f'{run_id}_summary.json'
        self._stream = self._csv_path.open(
            'w', encoding='utf-8', newline=''
        )
        self._writer = csv.DictWriter(
            self._stream,
            fieldnames=[
                'elapsed', 'x', 'y', 'theta', 'safety_mode',
                'raw_linear', 'raw_angular', 'safe_linear',
                'safe_angular', 'mission_event'
            ],
        )
        self._writer.writeheader()
        self._started_at = time.monotonic()
        self._pose: Pose | None = None
        self._raw = Twist()
        self._safe = Twist()
        self._safety_mode = 'UNKNOWN'
        self._mission_event = 'WAITING'
        self._sample_count = 0
        self._closed = False

        self.create_subscription(Pose, 'turtle1/pose', self._on_pose, 10)
        self.create_subscription(
            Twist, 'turtle_goal/cmd_vel_raw', self._on_raw, 10
        )
        self.create_subscription(
            Twist, 'turtle1/cmd_vel', self._on_safe, 10
        )
        self.create_subscription(
            String, 'turtle_guard/status', self._on_safety, 10
        )
        self.create_subscription(
            String, 'mission/status', self._on_mission, 10
        )
        self.create_timer(period, self._sample)
        self.get_logger().info(f'Recording CSV: {self._csv_path}')

    def _on_pose(self, message: Pose) -> None:
        self._pose = message

    def _on_raw(self, message: Twist) -> None:
        self._raw = message

    def _on_safe(self, message: Twist) -> None:
        self._safe = message

    def _on_safety(self, message: String) -> None:
        self._safety_mode = message.data

    def _on_mission(self, message: String) -> None:
        try:
            self._mission_event = json.loads(message.data).get(
                'event', 'UNKNOWN'
            )
        except json.JSONDecodeError:
            self._mission_event = 'INVALID_STATUS_JSON'

    def _sample(self) -> None:
        if self._pose is None:
            return
        self._writer.writerow({
            'elapsed': f'{time.monotonic() - self._started_at:.3f}',
            'x': f'{self._pose.x:.4f}',
            'y': f'{self._pose.y:.4f}',
            'theta': f'{self._pose.theta:.4f}',
            'safety_mode': self._safety_mode,
            'raw_linear': f'{self._raw.linear.x:.4f}',
            'raw_angular': f'{self._raw.angular.z:.4f}',
            'safe_linear': f'{self._safe.linear.x:.4f}',
            'safe_angular': f'{self._safe.angular.z:.4f}',
            'mission_event': self._mission_event,
        })
        self._stream.flush()
        self._sample_count += 1

    def finish(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._stream.close()
        summary = {
            'duration': round(time.monotonic() - self._started_at, 3),
            'samples': self._sample_count,
            'final_mission_event': self._mission_event,
            'final_safety_mode': self._safety_mode,
            'trajectory_csv': str(self._csv_path),
        }
        self._summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        self.get_logger().info(f'Summary: {self._summary_path}')


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = PerformanceLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.finish()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
