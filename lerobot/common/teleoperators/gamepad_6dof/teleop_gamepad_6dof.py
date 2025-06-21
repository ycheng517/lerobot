#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from typing import Any

from ..teleoperator import Teleoperator
from .configuration_gamepad_6dof import Gamepad6DOFTeleopConfig


# Gripper values: 0.0 = open, 1.0 = closed
gripper_action_map = {
    "close": 1.0,
    "open": 0.0,
}


class Gamepad6DOFTeleop(Teleoperator):
    """
    6-DOF Gamepad Teleoperator for full 6-degree-of-freedom control:
    - Left joystick: Linear X/Y movement
    - Right joystick: Angular X/Y rotation
    - LR bumpers: Angular Z rotation (yaw)
    - LR triggers: Linear Z movement (up/down)
    - Gripper: Normalized values (0.0 = open, 1.0 = closed), defaults open
    """

    config_class = Gamepad6DOFTeleopConfig
    name = "gamepad_6dof"

    def __init__(self, config: Gamepad6DOFTeleopConfig):
        super().__init__(config)
        self.config = config
        self.robot_type = config.type
        self.gamepad = None

    @property
    def action_features(self) -> dict:
        if self.config.use_gripper:
            return {
                "dtype": "float32",
                "shape": (7,),
                "names": {
                    "linear_x": 0,
                    "linear_y": 1,
                    "linear_z": 2,
                    "angular_x": 3,
                    "angular_y": 4,
                    "angular_z": 5,
                    "gripper": 6,
                },
            }
        else:
            return {
                "dtype": "float32",
                "shape": (6,),
                "names": {
                    "linear_x": 0,
                    "linear_y": 1,
                    "linear_z": 2,
                    "angular_x": 3,
                    "angular_y": 4,
                    "angular_z": 5,
                },
            }

    @property
    def feedback_features(self) -> dict:
        return {}

    def connect(self) -> None:
        # Use HidApi for macOS
        if sys.platform == "darwin":
            # NOTE: On macOS, pygame doesn't reliably detect input from some controllers so we fall back to hidapi
            from .gamepad_6dof_utils import Gamepad6DOFControllerHID as Gamepad6DOF
        else:
            from .gamepad_6dof_utils import Gamepad6DOFController as Gamepad6DOF

        self.gamepad = Gamepad6DOF(
            deadzone=self.config.deadzone,
            linear_scale=self.config.linear_scale,
            angular_scale=self.config.angular_scale,
            gripper_close_button=self.config.gripper_close_button,
        )
        self.gamepad.start()

    def get_action(self) -> dict[str, Any]:
        self.gamepad.update()

        # Get 6-DOF movement from controller
        linear_x, linear_y, linear_z, angular_x, angular_y, angular_z = self.gamepad.get_6dof_deltas()

        action_dict = {
            "linear_x": linear_x,
            "linear_y": linear_y,
            "linear_z": linear_z,
            "angular_x": angular_x,
            "angular_y": angular_y,
            "angular_z": angular_z,
        }

        # Handle gripper control - normalized: 0.0 = open, 1.0 = closed
        if self.config.use_gripper:
            gripper_command = self.gamepad.gripper_command()
            gripper_value = gripper_action_map[gripper_command]
            action_dict["gripper"] = gripper_value

        return action_dict

    def disconnect(self) -> None:
        if self.gamepad is not None:
            self.gamepad.stop()
            self.gamepad = None

    def is_connected(self) -> bool:
        return self.gamepad is not None

    def calibrate(self) -> None:
        # No calibration needed for gamepad
        pass

    def is_calibrated(self) -> bool:
        # Gamepad doesn't require calibration
        return True

    def configure(self) -> None:
        # No additional configuration needed
        pass

    def send_feedback(self, feedback: dict) -> None:
        # Gamepad doesn't support feedback
        pass
