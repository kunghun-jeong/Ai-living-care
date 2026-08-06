"""limo-MCP 전용 Gazebo + Nav2 시뮬레이션 브링업.

turtlebot3_gazebo(카메라 브리지 포함된 waffle 로봇)와 nav2_bringup(slam_toolbox
기반 실시간 매핑 + Nav2 스택)을 그대로 재사용해서 엮는다. gzserver/gzclient/
robot_state_publisher/spawn/nav2 bringup 하나하나는 각 패키지의 공식 launch
파일이 하는 것을 그대로 따라감 — 커스텀 로봇 자산은 없음.

월드는 turtlebot3_world 대신 `aws_small_house/`(aws-robomaker-small-house-world
저장소 gzweb 브랜치에서 worlds/models/maps만 sparse checkout)를 사용한다. 이
저장소는 클래식 Gazebo(ODE, gazebo_ros) 대상이라 gz-sim(Harmonic)에서 그대로
로드되지 않았음 — 헤드리스 로드 시 "A link named link has invalid inertia"로
전체 월드 로드가 실패함. 원인 두 가지를 찾아 고침(둘 다 `aws_small_house/` 안에서
직접 수정, 원본 저장소는 안 건드림):
  1. `aws_robomaker_residential_ShoeRack_01/model.sdf`: `<inertia>` 텐서에
     `<ixx>`가 중복되고 `<izz>`가 누락된 원본 벤더 오타 — `<izz>`로 고침.
  2. furniture 모델 46종이 `<inertial><mass>`만 있고 `<inertia>` 텐서가 아예
     없음(클래식 Gazebo는 관대하게 넘어갔지만 gz-sim은 정색함) — world 파일의
     해당 `<model>` include 인스턴스마다 `<static>true</static>`를 추가해서
     동역학 계산 자체를 건너뛰게 함(가구는 어차피 정적이어야 맞음).

단, 로봇 스폰 + ROS<->Gazebo 브리지만은 `turtlebot3_world.launch.py`가
내부적으로 부르는 `spawn_turtlebot3.launch.py`를 통째로 include하지 않고 직접
풀어서 구성한다. 이유(실제 시험 중 발견): 그 패키지의 스톡
`turtlebot3_waffle_bridge.yaml`은 `cmd_vel`을 `TwistStamped`로 선언하는데, 이
ROS2 Jazzy + nav2_bringup 스톡 파라미터 조합에서는 Nav2의 collision_monitor가
최종 `/cmd_vel`을 `Twist`(스탬프 없음)로 발행함 — 타입이 안 맞으면 ROS2는 그
둘을 다른 토픽 인스턴스로 취급해 아무 것도 브리지되지 않고, 로봇이 목표를
향해 계속 재계획만 하고 실제로는 한 발짝도 안 움직인다("Failed to make
progress" 반복, `/odom` 위치 불변으로 확인함). 그래서 `cmd_vel`만 `Twist`로
고친 `waffle_bridge_fixed.yaml`을 대신 사용한다 (같은 폴더).

turtlebot3_world용으로 미리 만들어둔 정적 지도가 없어서 AMCL 대신
slam_toolbox로 실시간 매핑하면서 동시에 내비게이션하는 방식(slam:=True)을 쓴다.

카메라/라이다 렌더링은 이 저장소를 Claude Code가 (사람 인터랙티브 터미널이
아니라) `wsl.exe -e bash -lc "... &"`로 비대화형 배경 실행하며 검증하는 동안
두 경로 다 막혔다(실제로 겪음):
  - `--headless-rendering`(GUI 없이 오프스크린 렌더): 프로세스는 안 죽지만
    `/camera/image_raw`가 gz 쪽에서부터 100초 넘게 기다려도 프레임을 한 장도
    안 만듦. 이 WSL2 인스턴스에 `/dev/dri`(DRM 렌더 노드)가 아예 없어서 EGL
    오프스크린 컨텍스트가 붙을 디바이스가 없는 것으로 보임 — 이건 world와
    무관한 이 WSL2 인스턴스 자체의 제약으로 보임.
  - GUI(`gz sim -g`) 붙이는 기본 경로: 매번 "Aborted (core dumped)"로 죽는데,
    스택 트레이스를 까보면 원인은 렌더링/부하 문제가 아니라
    `qt.qpa.xcb: could not connect to display :0` — 단순 X11 연결 실패였음.
    DISPLAY=:0/WAYLAND_DISPLAY=wayland-0 env는 잡혀 있는데도 연결이 안 되는
    걸 보면, WSLg의 X/Wayland 서버가 사람이 대화형으로 연 WSL 세션에 묶여
    있어서 Claude Code가 새로 붙인 비대화형 wsl.exe 세션에서는 그 소켓에
    접근이 안 되는 것으로 추정됨(미확인). 즉 이 GUI 크래시는 small_house
    world나 nav2 동시 부하와는 무관할 가능성이 높음 — 실제 사람이 자기
    WSL 터미널에서 대화형으로 이 launch 파일을 돌리면(이전 세션에
    turtlebot3_world로 카메라가 검증된 방식과 동일한 조건) 문제없이 카메라가
    뜰 수 있음. 아직 대화형 세션에서 재검증은 못 했음.

gzserver는 기본(비-headless) 렌더 경로를 쓰고 GUI(`gzclient`)를 붙인다.
`on_exit_shutdown=false`로 둬서 GUI가 어떤 이유로든 죽어도 나머지(로봇
제어/Nav2)는 계속 동작하게 한다. nav2를 spawn 이후 15초 더 늦게 띄우는
`delayed_nav2`는 애초에 "nav2 부하가 GUI를 죽인다"는(위에서 틀린 것으로
확인된) 가설로 넣었던 것 — 틀린 가설이었지만 유지해도 해는 없어서 안전
마진으로 남겨둠.

실행:
    source /opt/ros/jazzy/setup.bash
    ros2 launch Simulation/sim_bringup.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ROBOT_MODEL = "waffle"


def generate_launch_description():
    turtlebot3_gazebo_dir = get_package_share_directory("turtlebot3_gazebo")
    ros_gz_sim_dir = get_package_share_directory("ros_gz_sim")
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    nav2_params_file = os.path.join(nav2_bringup_dir, "params", "nav2_params.yaml")
    # os.path.dirname(__file__)만 쓰면 `ros2 launch Simulation/sim_bringup.launch.py`처럼
    # 상대경로로 실행했을 때 __file__ 자체가 상대경로로 남아서 GZ_SIM_RESOURCE_PATH도
    # 상대경로로 등록됨 — sdformat이 file:// 메쉬 URI를 해석할 때 이 상대 경로를
    # 이중으로 이어붙여서(.../aws_small_house/models/X/aws_small_house/models/X/meshes/...)
    # 대부분의 furniture collision mesh 로드가 실패하는 걸 실제로 겪음. abspath로 고정.
    this_dir = os.path.dirname(os.path.abspath(__file__))
    small_house_dir = os.path.join(this_dir, "aws_small_house")
    world = os.path.join(small_house_dir, "worlds", "small_house.world")
    robot_sdf = os.path.join(
        turtlebot3_gazebo_dir, "models", f"turtlebot3_{ROBOT_MODEL}", "model.sdf"
    )
    bridge_params = os.path.join(this_dir, "waffle_bridge_fixed.yaml")

    # small_house.world의 furniture model:// URI 해석용. README 권장대로 (0,0,0)은
    # lounge chair와 충돌해서 피하고 (3.5, 1.0) 근처를 스폰 지점으로 사용.
    SPAWN_X, SPAWN_Y, SPAWN_Z = "3.5", "1.0", "0.01"

    # robot_state_publisher.launch.py가 os.environ['TURTLEBOT3_MODEL']을 직접
    # 읽어서 urdf 경로를 정한다 (launch configuration이 아니라 진짜 프로세스
    # 환경변수).
    set_tb3_model = SetEnvironmentVariable("TURTLEBOT3_MODEL", ROBOT_MODEL)

    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(turtlebot3_gazebo_dir, "models")
    )
    set_env_vars_resources_house = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(small_house_dir, "models")
    )

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": ["-r -s -v2 ", world], "on_exit_shutdown": "true"}.items(),
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": "-g -v2 ", "on_exit_shutdown": "false"}.items(),
    )

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo_dir, "launch", "robot_state_publisher.launch.py")
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    spawn_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", ROBOT_MODEL, "-file", robot_sdf, "-x", SPAWN_X, "-y", SPAWN_Y, "-z", SPAWN_Z],
        output="screen",
    )

    bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_params}"],
        output="screen",
    )

    image_bridge_cmd = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"],
        output="screen",
    )

    nav2_bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "slam": "True",
            "use_sim_time": use_sim_time,
            "autostart": "True",
            "params_file": nav2_params_file,
        }.items(),
    )

    # small_house.world는 furniture 메시가 82MB라 turtlebot3_world보다 훨씬 오래
    # 걸린다(측정: 단독 기동 시 /gazebo/worlds 서비스가 뜨는 데 ~15초, nav2 등과
    # 동시에 뜰 땐 더 걸림). `ros_gz_sim create`의 월드 조회 타임아웃은 이보다
    # 훨씬 짧아서 곧바로 실행하면 "Timed out when getting world names"로 스폰이
    # 죽고, 로봇이 없으니 odom TF도 안 생겨서 Nav2가 계속 대기하는 연쇄 실패가
    # 났음(실제로 겪음). 스폰 관련 노드들을 world 준비 이후로 지연시켜 회피.
    delayed_spawn = TimerAction(
        period=20.0,
        actions=[spawn_cmd, bridge_cmd, image_bridge_cmd],
    )

    # nav2(특히 bt_navigator/docking_server 등 lifecycle configure 구간)는 CPU를
    # 크게 튀게 만드는데, 이게 gzclient(GUI) 렌더 초기화와 겹치면 GUI가
    # "Aborted (core dumped)"로 죽는 걸 실제로 겪었음. spawn(20초) 이후 GUI/카메라가
    # 먼저 안정화될 시간(15초)을 더 주고 nav2를 띄운다.
    delayed_nav2 = TimerAction(period=35.0, actions=[nav2_bringup_cmd])

    return LaunchDescription(
        [
            set_tb3_model,
            set_env_vars_resources,
            set_env_vars_resources_house,
            gzserver_cmd,
            gzclient_cmd,
            robot_state_publisher_cmd,
            delayed_spawn,
            delayed_nav2,
        ]
    )
