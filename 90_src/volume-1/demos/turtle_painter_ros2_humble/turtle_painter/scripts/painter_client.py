#!/usr/bin/env python3
"""Parameter-driven TurtlePainter action client."""

from __future__ import annotations

import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from turtle_painter.action import DrawShape


class TurtlePainterClient(Node):
    def __init__(self) -> None:
        super().__init__('turtle_painter_client')
        defaults = {
            'shape_name': 'square',
            'size': 2.0,
            'start_x': 4.5,
            'start_y': 4.5,
            'speed': 1.0,
            'cancel_after': 0.0,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self._client = ActionClient(
            self, DrawShape, '/turtle_painter/draw_shape'
        )
        self._goal_handle = None
        self._sent_at = 0.0
        self._cancel_sent = False
        self.create_timer(0.1, self._maybe_cancel)

    def send_goal(self) -> None:
        if not self._client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server unavailable after 5 seconds')
            rclpy.shutdown()
            return
        goal = DrawShape.Goal()
        goal.shape_name = str(self.get_parameter('shape_name').value)
        goal.size = float(self.get_parameter('size').value)
        goal.start_x = float(self.get_parameter('start_x').value)
        goal.start_y = float(self.get_parameter('start_y').value)
        goal.speed = float(self.get_parameter('speed').value)
        self.get_logger().info(f'Sending {goal.shape_name} goal')
        future = self._client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future) -> None:
        self._goal_handle = future.result()
        if not self._goal_handle.accepted:
            self.get_logger().error('Goal rejected')
            rclpy.shutdown()
            return
        self._sent_at = time.monotonic()
        self.get_logger().info('Goal accepted')
        result_future = self._goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

    def _on_feedback(self, message) -> None:
        feedback = message.feedback
        self.get_logger().info(
            f'progress={feedback.progress * 100.0:5.1f}%, '
            f'segment={feedback.current_segment}, '
            f'remaining={feedback.remaining_distance:.2f}'
        )

    def _maybe_cancel(self) -> None:
        cancel_after = float(self.get_parameter('cancel_after').value)
        if (self._goal_handle is None or self._cancel_sent
                or cancel_after <= 0.0):
            return
        if time.monotonic() - self._sent_at >= cancel_after:
            self._cancel_sent = True
            self.get_logger().warning('Cancel timer expired; requesting cancel')
            future = self._goal_handle.cancel_goal_async()
            future.add_done_callback(self._on_cancel_response)

    def _on_cancel_response(self, future) -> None:
        response = future.result()
        self.get_logger().info(
            f'Cancel response: {len(response.goals_canceling)} goal(s)'
        )

    def _on_result(self, future) -> None:
        wrapped = future.result()
        result = wrapped.result
        self.get_logger().info(
            f'status={wrapped.status}, success={result.success}, '
            f'time={result.total_time:.2f}, '
            f'error={result.position_error:.3f}, message={result.message}'
        )
        rclpy.shutdown()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TurtlePainterClient()
    node.send_goal()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node._goal_handle is not None:
            node._goal_handle.cancel_goal_async()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
