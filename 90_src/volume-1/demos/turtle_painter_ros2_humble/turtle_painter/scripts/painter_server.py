#!/usr/bin/env python3
"""TurtlePainter action server for ROS 2 Humble."""

from __future__ import annotations

import math
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import (
    MutuallyExclusiveCallbackGroup,
    ReentrantCallbackGroup,
)
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from turtlesim.msg import Pose
from turtlesim.srv import SetPen

from turtle_painter.action import DrawShape


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def make_path(shape: str, size: float, start_x: float,
              start_y: float) -> list[tuple[float, float]]:
    """Return ordered vertices; the first vertex is the requested start."""
    if shape == 'square':
        return [
            (start_x, start_y),
            (start_x + size, start_y),
            (start_x + size, start_y + size),
            (start_x, start_y + size),
            (start_x, start_y),
        ]
    height = size * math.sqrt(3.0) / 2.0
    return [
        (start_x, start_y),
        (start_x + size, start_y),
        (start_x + size / 2.0, start_y + height),
        (start_x, start_y),
    ]


class TurtlePainterServer(Node):
    """Execute one square or triangle drawing goal at a time."""

    def __init__(self) -> None:
        super().__init__('turtle_painter_server')
        defaults = {
            'linear_gain': 1.5,
            'angular_gain': 5.0,
            'max_angular_speed': 3.0,
            'distance_tolerance': 0.06,
            'heading_tolerance': 0.18,
            'pose_timeout': 1.0,
            'segment_timeout': 20.0,
            'control_period': 0.05,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

        self._pose: Pose | None = None
        self._pose_received_at = 0.0
        self._goal_lock = threading.Lock()
        self._goal_reserved = False
        self._pose_group = MutuallyExclusiveCallbackGroup()
        # Cancel callbacks must run while the long execute callback is active.
        self._action_group = ReentrantCallbackGroup()
        self._service_group = MutuallyExclusiveCallbackGroup()
        self._cmd_pub = self.create_publisher(
            Twist, '/turtle_goal/cmd_vel_raw', 10
        )
        self.create_subscription(
            Pose,
            '/turtle1/pose',
            self._on_pose,
            10,
            callback_group=self._pose_group,
        )
        self._pen_client = self.create_client(
            SetPen,
            '/turtle1/set_pen',
            callback_group=self._service_group,
        )
        self._action_server = ActionServer(
            self,
            DrawShape,
            '/turtle_painter/draw_shape',
            execute_callback=self._execute,
            goal_callback=self._on_goal,
            cancel_callback=self._on_cancel,
            callback_group=self._action_group,
        )
        self.get_logger().info(
            'TurtlePainter ready: /turtle_painter/draw_shape'
        )

    def _on_pose(self, message: Pose) -> None:
        self._pose = message
        self._pose_received_at = time.monotonic()

    def _on_goal(self, request: DrawShape.Goal) -> GoalResponse:
        shape = request.shape_name.strip().lower()
        values = (
            request.size, request.start_x, request.start_y, request.speed
        )
        if shape not in {'square', 'triangle'}:
            self.get_logger().warning('Rejected: shape must be square/triangle')
            return GoalResponse.REJECT
        if not all(math.isfinite(value) for value in values):
            self.get_logger().warning('Rejected: goal values must be finite')
            return GoalResponse.REJECT
        path = make_path(shape, request.size, request.start_x, request.start_y)
        if request.size <= 0.0 or request.speed <= 0.0:
            self.get_logger().warning('Rejected: size and speed must be positive')
            return GoalResponse.REJECT
        if any(not (0.5 <= x <= 10.5 and 0.5 <= y <= 10.5)
               for x, y in path):
            self.get_logger().warning('Rejected: path leaves valid workspace')
            return GoalResponse.REJECT
        with self._goal_lock:
            if self._goal_reserved:
                self.get_logger().warning('Rejected: another goal is active')
                return GoalResponse.REJECT
            self._goal_reserved = True
        return GoalResponse.ACCEPT

    def _on_cancel(self, _goal_handle) -> CancelResponse:
        self.get_logger().warning('Cancellation requested')
        return CancelResponse.ACCEPT

    def _number(self, name: str) -> float:
        return float(self.get_parameter(name).value)

    def _stop(self) -> None:
        self._cmd_pub.publish(Twist())

    def _set_pen(self, off: bool) -> bool:
        if not self._pen_client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error('/turtle1/set_pen service unavailable')
            return False
        request = SetPen.Request()
        request.r = 30
        request.g = 90
        request.b = 200
        request.width = 3
        request.off = 1 if off else 0
        future = self._pen_client.call_async(request)
        deadline = time.monotonic() + 2.0
        while not future.done() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not future.done() or future.exception() is not None:
            self.get_logger().error('Failed to change pen state')
            return False
        return True

    def _remaining_distance(
        self, path: list[tuple[float, float]], segment: int
    ) -> float:
        assert self._pose is not None
        remaining = math.hypot(
            path[segment][0] - self._pose.x,
            path[segment][1] - self._pose.y,
        )
        for index in range(segment, len(path) - 1):
            remaining += math.dist(path[index], path[index + 1])
        return remaining

    def _execute(self, goal_handle):
        started_at = time.monotonic()
        goal = goal_handle.request
        shape = goal.shape_name.strip().lower()
        path = make_path(shape, goal.size, goal.start_x, goal.start_y)
        total_length = sum(
            math.dist(path[index], path[index + 1])
            for index in range(len(path) - 1)
        )
        # Include the approach to the requested start in progress estimation.
        if self._pose is not None:
            total_length += math.hypot(
                path[0][0] - self._pose.x, path[0][1] - self._pose.y
            )
        total_length = max(total_length, 1e-6)
        result = DrawShape.Result()
        final_error = float('inf')

        try:
            self.get_logger().info(
                f'Accepted {shape}: size={goal.size:.2f}, speed={goal.speed:.2f}'
            )
            if not self._set_pen(off=True):
                goal_handle.abort()
                return self._result(
                    result, False, started_at, final_error,
                    'Cannot disable pen before approaching start.'
                )
            for segment, target in enumerate(path):
                segment_started = time.monotonic()
                while rclpy.ok():
                    if goal_handle.is_cancel_requested:
                        self._stop()
                        goal_handle.canceled()
                        return self._result(
                            result, False, started_at, final_error,
                            'Task canceled; zero velocity published.'
                        )
                    if self._pose is None or (
                        time.monotonic() - self._pose_received_at
                        > self._number('pose_timeout')
                    ):
                        self._stop()
                        goal_handle.abort()
                        return self._result(
                            result, False, started_at, final_error,
                            'Pose missing or stale; task aborted.'
                        )
                    if (time.monotonic() - segment_started
                            > self._number('segment_timeout')):
                        self._stop()
                        goal_handle.abort()
                        return self._result(
                            result, False, started_at, final_error,
                            f'Segment {segment} timed out.'
                        )

                    dx = target[0] - self._pose.x
                    dy = target[1] - self._pose.y
                    final_error = math.hypot(dx, dy)
                    remaining = self._remaining_distance(path, segment)
                    feedback = DrawShape.Feedback()
                    feedback.current_segment = segment
                    feedback.remaining_distance = float(remaining)
                    feedback.progress = float(clamp(
                        1.0 - remaining / total_length, 0.0, 1.0
                    ))
                    goal_handle.publish_feedback(feedback)

                    if final_error <= self._number('distance_tolerance'):
                        self._stop()
                        if segment == 0 and not self._set_pen(off=False):
                            goal_handle.abort()
                            return self._result(
                                result, False, started_at, final_error,
                                'Cannot enable pen at drawing start.'
                            )
                        break
                    heading_error = normalize_angle(
                        math.atan2(dy, dx) - self._pose.theta
                    )
                    command = Twist()
                    command.angular.z = clamp(
                        self._number('angular_gain') * heading_error,
                        -self._number('max_angular_speed'),
                        self._number('max_angular_speed'),
                    )
                    if abs(heading_error) <= self._number('heading_tolerance'):
                        command.linear.x = min(
                            self._number('linear_gain') * final_error,
                            float(goal.speed),
                        )
                    self._cmd_pub.publish(command)
                    time.sleep(self._number('control_period'))

            self._stop()
            goal_handle.succeed()
            return self._result(
                result, True, started_at, final_error,
                f'{shape} completed with {len(path) - 1} drawing segments.'
            )
        finally:
            self._stop()
            self._set_pen(off=False)
            with self._goal_lock:
                self._goal_reserved = False

    @staticmethod
    def _result(result, success: bool, started_at: float,
                error: float, message: str):
        result.success = success
        result.total_time = float(time.monotonic() - started_at)
        result.position_error = float(error)
        result.message = message
        return result

    def destroy_node(self):
        self._action_server.destroy()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TurtlePainterServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node._stop()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
