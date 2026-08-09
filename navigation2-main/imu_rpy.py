#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
from geometry_msgs.msg import Twist, Point
from nav_msgs.msg import Odometry
import numpy as np
import math
from tf_transformations import euler_from_quaternion, quaternion_from_euler
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
import tf2_ros
from geometry_msgs.msg import TransformStamped
import yaml
import os
from datetime import datetime
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from collections import deque
import sys
from scipy import signal
from scipy.optimize import least_squares


# ================== 核心算法库 (重写部分) ==================

def low_pass_filter(data, fs, cutoff=5.0, order=4):
    """巴特沃斯低通滤波"""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    if normal_cutoff >= 1.0:
        normal_cutoff = 0.99
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return signal.filtfilt(b, a, data)


def estimate_time_delay(t1, data1, t2, data2):
    """通过角速度互相关估计时间延迟"""
    t_start = max(t1[0], t2[0])
    t_end = min(t1[-1], t2[-1])
    if t_end <= t_start:
        return 0.0

    t_interp = np.linspace(t_start, t_end, min(len(t1), len(t2), 2000))
    dt = t_interp[1] - t_interp[0]

    d1 = np.interp(t_interp, t1, data1)
    d2 = np.interp(t_interp, t2, data2)

    correlation = signal.correlate(d1 - np.mean(d1), d2 - np.mean(d2), mode='full')
    lags = signal.correlation_lags(len(d1), len(d2), mode='full')
    lag = lags[np.argmax(correlation)]

    return lag * dt


# ================== GUI界面类 (保持大部分UI逻辑) ==================
class IMUCalibrationGUI:
    def __init__(self, ros_node):
        self.node = ros_node
        self.root = tk.Tk()
        self.root.title("四轮麦轮车IMU标定系统 - 鲁棒优化版")
        self.root.geometry("1200x850")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.bg_color = '#2b2b2b'
        self.fg_color = '#ffffff'
        self.root.configure(bg=self.bg_color)

        self.create_menu()
        self.create_main_layout()
        self.create_status_bar()
        self.create_result_display()

        self.ros_thread = threading.Thread(target=self.spin_ros, daemon=True)
        self.ros_thread.start()

        self.plot_data = {
            'time': deque(maxlen=200),
            'roll': deque(maxlen=200), 'pitch': deque(maxlen=200), 'yaw': deque(maxlen=200),
            'acc_x': deque(maxlen=200), 'acc_y': deque(maxlen=200), 'acc_z': deque(maxlen=200),
            'odom_x': deque(maxlen=200), 'odom_y': deque(maxlen=200)
        }
        self.plot_start_time = time.time()
        self.update_ui()

    def spin_ros(self):
        while rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0.1)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出结果", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_app)

    def create_main_layout(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_frame.pack_propagate(False)
        self.create_control_panel(left_frame)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 数据显示区
        data_frame = ttk.Frame(right_frame)
        data_frame.pack(fill=tk.X)
        self.create_data_display(data_frame)

        # 图表区
        chart_frame = ttk.Frame(right_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.create_chart_display(chart_frame)

    def create_control_panel(self, parent):
        ttk.Label(parent, text="操作面板", font=('Arial', 14, 'bold')).pack(pady=(0, 10))

        # 状态
        status_frame = ttk.LabelFrame(parent, text="状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_label_var = tk.StringVar(value="待机")
        ttk.Label(status_frame, textvariable=self.status_label_var, foreground='#00ff00').pack(anchor=tk.W)
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(5, 0))

        # 按钮
        btn_frame = ttk.LabelFrame(parent, text="标定流程", padding="10")
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="1. 开始静态标定 (5秒)", command=self.start_static).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="2. 开始动态标定 (画8字)", command=self.start_dynamic).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="停止", command=self.stop_calibration).pack(fill=tk.X, pady=5)

        # 参数
        param_frame = ttk.LabelFrame(parent, text="参数配置", padding="10")
        param_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(param_frame, text="标定速度 (m/s):").pack(anchor=tk.W)
        self.speed_var = tk.StringVar(value="0.3")
        ttk.Entry(param_frame, textvariable=self.speed_var).pack(fill=tk.X, pady=(0, 5))

        ttk.Label(param_frame, text="标定时间 (s):").pack(anchor=tk.W)
        self.time_var = tk.StringVar(value="40.0")
        ttk.Entry(param_frame, textvariable=self.time_var).pack(fill=tk.X)

        # 日志
        log_frame = ttk.LabelFrame(parent, text="日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_data_display(self, parent):
        # 简化的数据显示
        f1 = ttk.LabelFrame(parent, text="IMU实时", padding=5)
        f1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.imu_labels = {}
        for k in ['ax', 'ay', 'wz']:
            frame = ttk.Frame(f1)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=f"{k}:").pack(side=tk.LEFT)
            self.imu_labels[k] = ttk.Label(frame, text="0.00")
            self.imu_labels[k].pack(side=tk.RIGHT)

        f2 = ttk.LabelFrame(parent, text="Odom实时", padding=5)
        f2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.odom_labels = {}
        for k in ['vx', 'vy', 'wz']:
            frame = ttk.Frame(f2)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=f"{k}:").pack(side=tk.LEFT)
            self.odom_labels[k] = ttk.Label(frame, text="0.00")
            self.odom_labels[k].pack(side=tk.RIGHT)

    def create_chart_display(self, parent):
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor='#2b2b2b')
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)

        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')

        self.ax1.set_title("Acc (m/s^2)", color='white')
        self.ax2.set_title("Angular Vel (rad/s)", color='white')

        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_result_display(self):
        frame = ttk.LabelFrame(self.root, text="标定结果", padding=10)
        frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.res_labels = {}
        params = ['x_offset', 'y_offset', 'yaw_offset', 'roll_offset', 'pitch_offset', 'time_delay']
        for i, p in enumerate(params):
            f = ttk.Frame(frame)
            f.pack(side=tk.LEFT, expand=True, padx=5)
            ttk.Label(f, text=p).pack()
            self.res_labels[p] = ttk.Label(f, text="--", font=('Arial', 12, 'bold'), foreground='#00BFFF')
            self.res_labels[p].pack()

    def create_status_bar(self):
        pass

    def update_ui(self):
        try:
            # 更新数值
            imu = self.node.latest_imu
            self.imu_labels['ax'].config(text=f"{imu.linear_acceleration.x:.2f}")
            self.imu_labels['ay'].config(text=f"{imu.linear_acceleration.y:.2f}")
            self.imu_labels['wz'].config(text=f"{imu.angular_velocity.z:.2f}")

            if self.node.latest_odom:
                odom = self.node.latest_odom
                self.odom_labels['vx'].config(text=f"{odom.twist.twist.linear.x:.2f}")
                self.odom_labels['vy'].config(text=f"{odom.twist.twist.linear.y:.2f}")
                self.odom_labels['wz'].config(text=f"{odom.twist.twist.angular.z:.2f}")

            # 更新图表
            t = time.time() - self.plot_start_time
            self.plot_data['time'].append(t)
            self.plot_data['acc_x'].append(imu.linear_acceleration.x)
            self.plot_data['acc_y'].append(imu.linear_acceleration.y)
            if self.node.latest_odom:
                self.plot_data['odom_x'].append(self.node.latest_odom.twist.twist.angular.z)
            else:
                self.plot_data['odom_x'].append(0)

            if len(self.plot_data['time']) % 5 == 0:  # 降频刷新
                self.ax1.clear()
                self.ax2.clear()
                self.ax1.plot(self.plot_data['time'], self.plot_data['acc_x'], 'r', label='Ax')
                self.ax1.plot(self.plot_data['time'], self.plot_data['acc_y'], 'g', label='Ay')
                self.ax1.legend(loc='upper right')
                self.ax1.set_title("Acc", color='white')

                self.ax2.plot(self.plot_data['time'], self.plot_data['odom_x'], 'y', label='Odom Wz')
                self.ax2.set_title("Gyro/Odom Wz", color='white')

                # 美化
                for ax in [self.ax1, self.ax2]:
                    ax.set_facecolor('#1e1e1e')
                    ax.tick_params(colors='white')
                    for spine in ax.spines.values():
                        spine.set_color('white')
                    ax.grid(True, alpha=0.2)

                self.canvas.draw()

            # 更新状态
            if self.node.is_calibrating:
                self.status_label_var.set("正在采集数据...")
                self.progress.start()
            elif self.node.is_static_calibrating:
                self.status_label_var.set("正在静态采集...")
                self.progress.start()
            else:
                self.status_label_var.set("就绪 / 已完成")
                self.progress.stop()

            # 更新结果
            if self.node.calibration_complete:
                self.res_labels['x_offset'].config(text=f"{self.node.x_offset:.4f} m")
                self.res_labels['y_offset'].config(text=f"{self.node.y_offset:.4f} m")
                self.res_labels['yaw_offset'].config(text=f"{math.degrees(self.node.dyaw_result):.2f}°")
                self.res_labels['roll_offset'].config(text=f"{math.degrees(self.node.static_roll):.2f}°")
                self.res_labels['pitch_offset'].config(text=f"{math.degrees(self.node.static_pitch):.2f}°")
                self.res_labels['time_delay'].config(text=f"{self.node.time_delay * 1000:.1f} ms")

        except Exception as e:
            pass
        self.root.after(100, self.update_ui)

    def log(self, msg):
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)

    def start_static(self):
        self.node.start_static_calibration()
        self.log("开始静态标定...")

    def start_dynamic(self):
        if not self.node.static_calibration_complete:
            if not messagebox.askyesno("警告", "建议先做静态标定。继续吗？"):
                return

        try:
            speed = float(self.speed_var.get())
            duration = float(self.time_var.get())
            self.node.start_dynamic_calibration(speed, duration)
            self.log(f"开始动态标定: 速度={speed}, 时间={duration}")
        except ValueError:
            messagebox.showerror("错误", "参数无效")

    def stop_calibration(self):
        self.node.stop_calibration()
        self.log("强制停止")

    def export_results(self):
        if not self.node.calibration_complete:
            messagebox.showwarning("提示", "未完成标定")
            return
        self.node.export_to_yaml()
        messagebox.showinfo("成功", f"结果已保存到 {self.node.save_path}")

    def quit_app(self):
        self.node.stop_robot()
        self.root.destroy()
        self.root.quit()
        rclpy.shutdown()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.mainloop()


# ================== ROS节点类 (核心改进) ==================
class IMUCalibration4WDNode(Node):
    def __init__(self):
        super().__init__('imu_calibration_robust_node')

        # 参数
        self.declare_parameter('save_path', './calibration_results')
        self.save_path = self.get_parameter('save_path').value
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        # 数据容器
        self.imu_buffer = []
        self.odom_buffer = []
        self.static_imu_buffer = []

        # 状态标志
        self.is_calibrating = False
        self.is_static_calibrating = False
        self.calibration_complete = False
        self.static_calibration_complete = False

        # 结果变量
        self.static_roll = 0.0
        self.static_pitch = 0.0
        self.dyaw_result = 0.0
        self.x_offset = 0.0
        self.y_offset = 0.0
        self.time_delay = 0.0

        self.latest_imu = Imu()
        self.latest_odom = None

        # 订阅与发布
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_cb, 100)  # 增大队列防止丢包
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 100)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.get_logger().info("IMU标定节点(鲁棒优化版)已启动")

    def imu_cb(self, msg):
        self.latest_imu = msg
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        # 提取数据
        q = msg.orientation
        roll, pitch, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])

        data = {
            't': t,
            'ax': msg.linear_acceleration.x,
            'ay': msg.linear_acceleration.y,
            'wz': msg.angular_velocity.z,
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw
        }

        if self.is_static_calibrating:
            self.static_imu_buffer.append(data)
        elif self.is_calibrating:
            self.imu_buffer.append(data)

    def odom_cb(self, msg):
        self.latest_odom = msg
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        if self.is_calibrating:
            self.odom_buffer.append({
                't': t,
                'vx': msg.twist.twist.linear.x,
                'vy': msg.twist.twist.linear.y,
                'wz': msg.twist.twist.angular.z,
                # 保存yaw用于对齐
                'yaw': 0  # 里程计yaw在dxdy计算中通常用不到，仅用于yaw对齐
            })

    # -------- 静态标定 --------
    def start_static_calibration(self):
        self.static_imu_buffer = []
        self.is_static_calibrating = True
        self.create_timer(5.0, self.finish_static_calibration)  # 5秒后结束

    def finish_static_calibration(self):
        self.is_static_calibrating = False
        if len(self.static_imu_buffer) < 100:
            self.get_logger().error("静态数据不足")
            return

        axs = np.array([d['ax'] for d in self.static_imu_buffer])
        ays = np.array([d['ay'] for d in self.static_imu_buffer])
        azs = np.array([math.sqrt(9.81 ** 2 - d['ax'] ** 2 - d['ay'] ** 2) for d in self.static_imu_buffer])

        avg_ax = np.mean(axs)
        avg_ay = np.mean(ays)
        avg_az = np.mean(azs)

        self.static_pitch = math.atan2(-avg_ax, math.sqrt(avg_ay ** 2 + avg_az ** 2))
        self.static_roll = math.atan2(avg_ay, avg_az)

        self.static_calibration_complete = True
        self.get_logger().info(
            f"静态标定完成: Roll={math.degrees(self.static_roll):.2f}, Pitch={math.degrees(self.static_pitch):.2f}")

    # -------- 动态标定 (核心修改) --------
    def start_dynamic_calibration(self, speed, duration):
        self.imu_buffer = []
        self.odom_buffer = []
        self.is_calibrating = True

        # 启动八字运动
        self.motion_thread = threading.Thread(target=self.run_motion_pattern, args=(speed, duration))
        self.motion_thread.start()

    def run_motion_pattern(self, speed, duration):
        start_t = time.time()
        rate = self.create_rate(10)

        # 预先等待一秒静止
        time.sleep(1.0)

        while rclpy.ok() and self.is_calibrating and (time.time() - start_t < duration):
            elapsed = time.time() - start_t
            cmd = Twist()
            cmd.linear.x = speed
            # 变频正弦波 (Chirp signal) 激励，比纯8字包含更多频率信息，利于标定
            cmd.angular.z = 1.0 * math.sin(0.5 * elapsed) + 0.5 * math.cos(0.2 * elapsed)
            self.cmd_pub.publish(cmd)
            time.sleep(0.1)

        self.stop_robot()
        self.is_calibrating = False
        self.process_dynamic_data()

    def stop_calibration(self):
        self.is_calibrating = False
        self.stop_robot()

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

    # -------- 数据处理与优化 (核心算法) --------
    def process_dynamic_data(self):
        self.get_logger().info(f"开始处理数据: IMU帧数={len(self.imu_buffer)}, Odom帧数={len(self.odom_buffer)}")

        if len(self.imu_buffer) < 50 or len(self.odom_buffer) < 50:
            self.get_logger().error("数据太少，标定失败")
            return

        # 1. 转换为numpy数组并按时间排序
        imu_t = np.array([d['t'] for d in self.imu_buffer])
        imu_ax = np.array([d['ax'] for d in self.imu_buffer])
        imu_ay = np.array([d['ay'] for d in self.imu_buffer])
        imu_wz = np.array([d['wz'] for d in self.imu_buffer])

        odom_t = np.array([d['t'] for d in self.odom_buffer])
        odom_vx = np.array([d['vx'] for d in self.odom_buffer])
        odom_vy = np.array([d['vy'] for d in self.odom_buffer])
        odom_wz = np.array([d['wz'] for d in self.odom_buffer])

        # 2. 估计时间延迟
        self.time_delay = estimate_time_delay(imu_t, imu_wz, odom_t, odom_wz)
        self.get_logger().info(f"估计时间延迟 (IMU领先Odom): {self.time_delay * 1000:.2f} ms")

        # 3. 对齐数据
        odom_t_shifted = odom_t + self.time_delay

        t_start = max(imu_t[0], odom_t_shifted[0]) + 0.5
        t_end = min(imu_t[-1], odom_t_shifted[-1]) - 0.5
        mask = (imu_t > t_start) & (imu_t < t_end)

        t_aligned = imu_t[mask]
        imu_ax = imu_ax[mask]
        imu_ay = imu_ay[mask]
        imu_wz = imu_wz[mask]

        # 插值Odom数据到对齐的时间点
        odom_vx_interp = np.interp(t_aligned, odom_t_shifted, odom_vx)
        odom_vy_interp = np.interp(t_aligned, odom_t_shifted, odom_vy)
        odom_wz_interp = np.interp(t_aligned, odom_t_shifted, odom_wz)

        # 4. 低通滤波 (可调参数)
        fs = 1.0 / np.mean(np.diff(t_aligned))
        cutoff = 2.0  # 2Hz截止频率，滤除振动
        imu_ax_filt = low_pass_filter(imu_ax, fs, cutoff)
        imu_ay_filt = low_pass_filter(imu_ay, fs, cutoff)
        imu_wz_filt = low_pass_filter(imu_wz, fs, cutoff)
        odom_vx_filt = low_pass_filter(odom_vx_interp, fs, cutoff)
        odom_vy_filt = low_pass_filter(odom_vy_interp, fs, cutoff)
        odom_wz_filt = low_pass_filter(odom_wz_interp, fs, cutoff)

        # 5. 计算Odom加速度
        dt = np.gradient(t_aligned)
        odom_ax = np.gradient(odom_vx_filt, t_aligned) - odom_wz_filt * odom_vy_filt
        odom_ay = np.gradient(odom_vy_filt, t_aligned) + odom_wz_filt * odom_vx_filt

        alpha_z = np.gradient(odom_wz_filt, t_aligned)

        # 6. 构建优化问题
        def residual_func(params):
            dx, dy, ba_x, ba_y = params
            w2 = odom_wz_filt ** 2

            # 预测的IMU加速度
            pred_ax = odom_ax - w2 * dx - alpha_z * dy + ba_x
            pred_ay = odom_ay + alpha_z * dx - w2 * dy + ba_y

            res_x = imu_ax_filt - pred_ax
            res_y = imu_ay_filt - pred_ay
            return np.concatenate([res_x, res_y])

        x0 = [0.1, 0.0, 0.0, 0.0]  # 初始猜测

        # 执行优化
        try:
            res = least_squares(residual_func, x0, loss='soft_l1', f_scale=0.1)
            self.x_offset, self.y_offset, bx, by = res.x
            self.get_logger().info(f"优化成功: dx={self.x_offset:.4f}, dy={self.y_offset:.4f}")
            self.get_logger().info(f"Acc Bias: bx={bx:.4f}, by={by:.4f}")
            self.calibration_complete = True

            # 发布TF验证
            self.publish_result_tf()

        except Exception as e:
            self.get_logger().error(f"优化计算出错: {e}")

    def publish_result_tf(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'imu_link_calibrated'
        t.transform.translation.x = self.x_offset
        t.transform.translation.y = self.y_offset
        t.transform.translation.z = 0.0
        q = quaternion_from_euler(self.static_roll, self.static_pitch, 0.0)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

    def export_to_yaml(self):
        data = {
            'imu_calibration': {
                'x_offset': float(self.x_offset),
                'y_offset': float(self.y_offset),
                'roll_offset': float(self.static_roll),
                'pitch_offset': float(self.static_pitch),
                'time_delay': float(self.time_delay),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        with open(os.path.join(self.save_path, 'calibration_result.yaml'), 'w') as f:
            yaml.dump(data, f)


# ================== 主入口 ==================
def main(args=None):
    rclpy.init(args=args)
    node = IMUCalibration4WDNode()
    gui = IMUCalibrationGUI(node)

    try:
        gui.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
