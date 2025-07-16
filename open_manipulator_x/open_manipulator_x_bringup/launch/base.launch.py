#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    declared_arguments = [
        DeclareLaunchArgument('start_rviz', default_value='false', description='Whether to launch RViz2'),
        DeclareLaunchArgument('prefix', default_value='""', description='Prefix for joint names'),
        DeclareLaunchArgument('use_sim', default_value='true', description='Use Gazebo simulation'),
        DeclareLaunchArgument('use_fake_hardware', default_value='false', description='Use fake hardware'),
        DeclareLaunchArgument('fake_sensor_commands', default_value='false', description='Fake sensor commands'),
        DeclareLaunchArgument('port_name', default_value='/dev/ttyUSB0', description='Serial port for hardware')
    ]

    start_rviz = LaunchConfiguration('start_rviz')
    prefix = LaunchConfiguration('prefix')
    use_sim = LaunchConfiguration('use_sim')
    use_fake_hardware = LaunchConfiguration('use_fake_hardware')
    fake_sensor_commands = LaunchConfiguration('fake_sensor_commands')
    port_name = LaunchConfiguration('port_name')

    description_pkg = 'open_manipulator_x_description'
    xacro_file = PathJoinSubstitution([
        FindPackageShare(description_pkg),
        'urdf',
        'open_manipulator_x_robot.urdf.xacro'
    ])

    robot_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'), ' ',
                xacro_file,
                ' prefix:=', prefix,
                ' use_sim:=', use_sim,
                ' use_fake_hardware:=', use_fake_hardware,
                ' fake_sensor_commands:=', fake_sensor_commands,
                ' port_name:=', port_name
            ]),
            value_type=str
        )
    }

    controller_manager_config = PathJoinSubstitution([
        FindPackageShare('open_manipulator_x_bringup'),
        'config',
        'hardware_controller_manager.yaml',
    ])

    rviz_config_file = PathJoinSubstitution([
        FindPackageShare('open_manipulator_x_bringup'),
        'rviz',
        'open_manipulator_x.rviz'
    ])
    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description, {'use_sim_time': use_sim}],
        output='screen'
    )

    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controller_manager_config],
        output='both',
        condition=UnlessCondition(use_sim)
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen',
        condition=IfCondition(start_rviz)
    )

    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    arm_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller'],
        output='screen'
    )

    delay_rviz = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[rviz_node],
        )
    )

    delay_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[arm_controller],
        )
    )
    nodes = [
        robot_state_pub_node,
        control_node,
        joint_state_broadcaster,
        delay_rviz,
        delay_arm
    ]

    return LaunchDescription(declared_arguments + nodes)
