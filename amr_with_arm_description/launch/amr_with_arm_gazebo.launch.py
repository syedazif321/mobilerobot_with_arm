#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    amr_with_arm_description_pkg = '/home/azif/projetcs/amr_with_arm/amr_with_arm_description'
    open_manipulator_x_moveit_config_pkg = '/home/azif/projetcs/amr_with_arm/open_manipulator_x/open_manipulator_x_moveit_config'

    # Generate robot description from xacro
    robot_description_content = Command([
        'xacro ',
        os.path.join(amr_with_arm_description_pkg, 'urdf', 'amr_with_arm.xacro')
    ])

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}]
    )

    # Spawn Entity in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'amr_with_arm'],
        output='screen'
    )

    # Gazebo Launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])]
        )
    )

    # Controller Manager with both wheel + arm controller
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            os.path.join(amr_with_arm_description_pkg, 'config', 'controllers.yaml'),  # Use combined YAML
            {'robot_description': robot_description_content}
        ],
        output='screen'
    )

    # Spawners
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    # Static TF world -> base_footprint
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'base_footprint'],
        output='screen'
    )

    # Launch Move Group
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(open_manipulator_x_moveit_config_pkg, 'launch', 'move_group.launch.py')
        )
    )

    # Launch RViz
    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(open_manipulator_x_moveit_config_pkg, 'launch', 'moveit_rviz.launch.py')
        )
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher_node,
        controller_manager,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner,  # <--- Added wheel controller
        arm_controller_spawner,
        spawn_entity,
        static_tf,
        move_group,
        rviz
    ])
