"""Load a parameterized TurtleMission and submit it as an action goal."""

from __future__ import annotations

import json
import math
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String

from turtle_painter.action import DrawShape


class MissionRunner(Node):
    """Submit one YAML-configured mission and publish lifecycle events."""

    def __init__(self) -> None:
        super().__init__('mission_runner')
        defaults = {
            'mission_id': 'mission_square_01',
            'shape_name': 'square',
            'size': 2.0,
            'start_x': 4.5,
            'start_y': 4.5,
            'speed': 1.0,
            'cancel_after': 0.0,
            'server_timeout': 10.0,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

        self._status_pub = self.create_publisher(String, 'mission/status', 10)
        self._client = ActionClient(
            self, DrawShape, 'turtle_painter/draw_shape'
        )
        self._goal_handle = None
        self._sent_at = 0.0
        self._cancel_sent = False
        self._finished = False
        self.create_timer(0.1, self._maybe_cancel)

    def _value(self, name: str):
        return self.get_parameter(name).value

    def _publish_event(self, event: str, **fields) -> None:
        payload = {
            'mission_id': str(self._value('mission_id')),
            'event': event,
            'elapsed': (
                0.0 if self._sent_at == 0.0
                else time.monotonic() - self._sent_at
            ),
            **fields,
        }
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        self._status_pub.publish(String(data=text))
        self.get_logger().info(text)

    def _configuration_error(self) -> str:
        mission_id = str(self._value('mission_id')).strip()
        shape = str(self._value('shape_name')).strip().lower()
        numbers = {
            name: float(self._value(name))
            for name in (
                'size', 'start_x', 'start_y', 'speed',
                'cancel_after', 'server_timeout'
            )
        }
        if not mission_id:
            return 'mission_id must not be empty'
        if shape not in {'square', 'triangle'}:
            return 'shape_name must be square or triangle'
        if not all(math.isfinite(value) for value in numbers.values()):
            return 'numeric mission parameters must be finite'
        if numbers['size'] <= 0.0 or numbers['speed'] <= 0.0:
            return 'size and speed must be positive'
        if numbers['cancel_after'] < 0.0:
            return 'cancel_after must be non-negative'
        if numbers['server_timeout'] <= 0.0:
            return 'server_timeout must be positive'
        return ''

    def start(self) -> None:
        error = self._configuration_error()
        if error:
            self._finished = True
            self._publish_event('CONFIGURATION_ERROR', message=error)
            return
        timeout = float(self._value('server_timeout'))
        self._publish_event('WAITING_FOR_SERVER')
        if not self._client.wait_for_server(timeout_sec=timeout):
            self._finished = True
            self._publish_event(
                'SERVER_TIMEOUT',
                message=f'Action server unavailable after {timeout:.1f}s',
            )
            return

        goal = DrawShape.Goal()
        goal.shape_name = str(self._value('shape_name')).strip().lower()
        goal.size = float(self._value('size'))
        goal.start_x = float(self._value('start_x'))
        goal.start_y = float(self._value('start_y'))
        goal.speed = float(self._value('speed'))
        self._sent_at = time.monotonic()
        self._publish_event('GOAL_SENT')
        future = self._client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future) -> None:
        self._goal_handle = future.result()
        if not self._goal_handle.accepted:
            self._finished = True
            self._publish_event('GOAL_REJECTED')
            return
        self._publish_event('GOAL_ACCEPTED')
        future = self._goal_handle.get_result_async()
        future.add_done_callback(self._on_result)

    def _on_feedback(self, message) -> None:
        feedback = message.feedback
        self._publish_event(
            'FEEDBACK',
            progress=round(float(feedback.progress), 4),
            current_segment=int(feedback.current_segment),
            remaining_distance=round(
                float(feedback.remaining_distance), 4
            ),
        )

    def _maybe_cancel(self) -> None:
        cancel_after = float(self._value('cancel_after'))
        if (self._goal_handle is None or self._cancel_sent
                or self._finished or cancel_after <= 0.0):
            return
        if time.monotonic() - self._sent_at >= cancel_after:
            self._cancel_sent = True
            self._publish_event('CANCEL_REQUESTED')
            future = self._goal_handle.cancel_goal_async()
            future.add_done_callback(self._on_cancel_response)

    def _on_cancel_response(self, future) -> None:
        count = len(future.result().goals_canceling)
        self._publish_event('CANCEL_RESPONSE', goals_canceling=count)

    def _on_result(self, future) -> None:
        wrapped = future.result()
        result = wrapped.result
        self._finished = True
        self._publish_event(
            'RESULT',
            action_status=int(wrapped.status),
            success=bool(result.success),
            total_time=round(float(result.total_time), 4),
            position_error=round(float(result.position_error), 4),
            message=result.message,
        )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MissionRunner()
    node.start()
    try:
        while rclpy.ok() and not node._finished:
            rclpy.spin_once(node, timeout_sec=0.2)
    except KeyboardInterrupt:
        if node._goal_handle is not None and not node._finished:
            node._goal_handle.cancel_goal_async()
            node._publish_event('INTERRUPTED')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
