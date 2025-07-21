#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    # Paths
    amr_with_arm_description_pkg = '/home/azif/projetcs/amr_with_arm/amr_with_arm_description'
    open_manipulator_x_moveit_config_pkg = '/home/azif/projetcs/amr_with_arm/open_manipulator_x/open_manipulator_x_moveit_config'

    # Custom world path
    custom_world = os.path.join(
        amr_with_arm_description_pkg,
        'world',
        'no_roof_small_warehouse.world'
    )

    # Generate robot description from xacro (FIXED)
    robot_description_content = ParameterValue(
        Command([
            'xacro ',
            os.path.join(amr_with_arm_description_pkg, 'urdf', 'amr_with_arm.xacro')
        ]),
        value_type=str
    )

    # Declare world launch argument
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=custom_world,
        description='Gazebo world file'
    )

    # Gazebo Launch with custom world
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])]
        ),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}]
    )

    # Controller Manager (wheel + arm controllers)
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            os.path.join(amr_with_arm_description_pkg, 'config', 'controllers.yaml'),
            {'robot_description': robot_description_content}
        ],
        output='screen'
    )

    # Spawner Nodes
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

    controller_manager_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'linear_guide_controller','--controller-manager', '/controller_manager'],
    )


    # Static TF world -> base_footprint
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'base_footprint'],
        output='screen'
    )

    # Spawn robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'amr_with_arm'],
        output='screen'
    )

    # Move Group (for MoveIt)
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(open_manipulator_x_moveit_config_pkg, 'launch', 'move_group.launch.py')
        )
    )

    # RViz with MoveIt config
    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(open_manipulator_x_moveit_config_pkg, 'launch', 'moveit_rviz.launch.py')
        )
    )

    return LaunchDescription([
        world_arg,
        gazebo,
        robot_state_publisher_node,
        controller_manager,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner,
        arm_controller_spawner,
        controller_manager_spawner,
        static_tf,
        spawn_entity,
        move_group,
        rviz
    ])
