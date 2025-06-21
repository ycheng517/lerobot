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

import logging


class Gamepad6DOFController:
    """
    6-DOF Gamepad Controller using pygame for 6-degree-of-freedom control:
    - Left joystick: Linear X/Y movement
    - Right joystick: Angular X/Y rotation
    - LR bumpers: Angular Z rotation (yaw)
    - LR triggers: Linear Z movement (up/down)
    - Button: Gripper control (nominally open, close when pressed)
    """

    def __init__(self, deadzone=0.1, linear_scale=1.0, angular_scale=1.0, gripper_close_button="A"):
        self.deadzone = deadzone
        self.linear_scale = linear_scale
        self.angular_scale = angular_scale
        self.gripper_close_button = gripper_close_button
        self.joystick = None
        self.running = True

        # Gripper state - defaults to open
        self.gripper_close_command = False

        # Button mapping for different controllers
        self.button_map = {
            "A": 0,  # A/Cross button
            "B": 1,  # B/Circle button
            "X": 2,  # X/Square button
            "Y": 3,  # Y/Triangle button
            "LB": 4,  # Left bumper
            "RB": 5,  # Right bumper
            "LT": 6,  # Left trigger (as button)
            "RT": 7,  # Right trigger (as button)
        }

    def start(self):
        """Initialize pygame and gamepad."""
        import pygame

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            logging.error("No gamepad detected. Please connect a gamepad and try again.")
            self.running = False
            return

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        logging.info(f"Initialized 6-DOF gamepad: {self.joystick.get_name()}")

        print("6-DOF Gamepad controls:")
        print("  Left stick: Linear X/Y movement")
        print("  Right stick: Angular X/Y rotation")
        print("  Left/Right bumpers: Angular Z rotation (yaw)")
        print("  Left/Right triggers: Linear Z movement (up/down)")
        print(f"  {self.gripper_close_button} button: Close gripper (normally open)")
        print("  B button: Exit")

    def stop(self):
        """Clean up pygame resources."""
        import pygame

        if pygame.joystick.get_init():
            if self.joystick:
                self.joystick.quit()
            pygame.joystick.quit()
        pygame.quit()

    def update(self):
        """Process pygame events to get fresh gamepad readings."""
        import pygame

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                # Gripper close button
                if event.button == self.button_map.get(self.gripper_close_button, 0):
                    self.gripper_close_command = True
                # B button for exit
                elif event.button == 1:  # B button
                    self.running = False

            elif event.type == pygame.JOYBUTTONUP:
                # Release gripper close button
                if event.button == self.button_map.get(self.gripper_close_button, 0):
                    self.gripper_close_command = False

    def get_6dof_deltas(self):
        """Get 6-DOF movement deltas from gamepad state."""
        import pygame

        try:
            # Left stick for linear X/Y movement (axes 0, 1)
            left_x = self.joystick.get_axis(0)  # Left/Right
            left_y = self.joystick.get_axis(1)  # Up/Down (often inverted)

            # Right stick for angular X/Y rotation (axes 2, 3)
            right_x = self.joystick.get_axis(3)  # Roll rotation
            right_y = self.joystick.get_axis(4)  # Pitch rotation

            # Bumpers for angular Z (yaw) - LB/RB (buttons 4, 5)
            left_bumper = self.joystick.get_button(4)
            right_bumper = self.joystick.get_button(5)

            # Triggers for linear Z movement (axes 4, 5 or separate axes)
            # Try different axis mappings for triggers
            try:
                # triggers mapped from -1,1 to 0,1
                left_trigger = (self.joystick.get_axis(2) + 1) / 2
                right_trigger = (self.joystick.get_axis(5) + 1) / 2
            except pygame.error:
                # Fallback if triggers aren't separate axes
                left_trigger = 1.0 if self.joystick.get_button(6) else 0.0
                right_trigger = 1.0 if self.joystick.get_button(7) else 0.0

            # Apply deadzone
            left_x = 0 if abs(left_x) < self.deadzone else left_x
            left_y = 0 if abs(left_y) < self.deadzone else left_y
            right_x = 0 if abs(right_x) < self.deadzone else right_x
            right_y = 0 if abs(right_y) < self.deadzone else right_y
            left_trigger = 0 if abs(left_trigger) < self.deadzone else left_trigger
            right_trigger = 0 if abs(right_trigger) < self.deadzone else right_trigger

            # Calculate deltas
            delta_x = -left_x * self.linear_scale  # Forward/backward
            delta_y = left_y * self.linear_scale  # Left/right
            delta_z = (right_trigger - left_trigger) * self.linear_scale  # Up/down

            angular_x = right_y * self.angular_scale  # Pitch
            angular_y = right_x * self.angular_scale  # Roll
            angular_z = -(right_bumper - left_bumper) * self.angular_scale  # Yaw

            return delta_x, delta_y, delta_z, angular_x, angular_y, angular_z

        except pygame.error:
            logging.error("Error reading gamepad. Is it still connected?")
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    def gripper_command(self) -> str:
        """Return gripper command - normally open, close when button pressed."""
        if self.gripper_close_command:
            return "close"
        else:
            return "open"  # Default to open

    def should_quit(self):
        """Return True if user requested to quit."""
        return not self.running


class Gamepad6DOFControllerHID:
    """
    6-DOF Gamepad Controller using HIDAPI for macOS compatibility.
    Same control scheme as pygame version but using HID for better macOS support.
    """

    def __init__(self, deadzone=0.1, linear_scale=1.0, angular_scale=1.0, gripper_close_button="A"):
        self.deadzone = deadzone
        self.linear_scale = linear_scale
        self.angular_scale = angular_scale
        self.gripper_close_button = gripper_close_button
        self.device = None
        self.device_info = None
        self.running = True

        # Controller state
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0
        self.left_bumper = 0.0
        self.right_bumper = 0.0

        # Gripper state - defaults to open
        self.gripper_close_command = False
        self.buttons = {}

    def find_device(self):
        """Look for gamepad device by vendor and product ID."""
        import hid

        devices = hid.enumerate()
        for device in devices:
            device_name = device["product_string"]
            if any(controller in device_name for controller in ["Logitech", "Xbox", "PS4", "PS5"]):
                return device

        logging.error("No gamepad found, check connection and product string in HID to add your gamepad")
        return None

    def start(self):
        """Connect to gamepad using HIDAPI."""
        import hid

        self.device_info = self.find_device()
        if not self.device_info:
            self.running = False
            return

        try:
            logging.info(f"Connecting to 6-DOF gamepad at path: {self.device_info['path']}")
            self.device = hid.device()
            self.device.open_path(self.device_info["path"])
            self.device.set_nonblocking(1)

            manufacturer = self.device.get_manufacturer_string()
            product = self.device.get_product_string()
            logging.info(f"Connected to {manufacturer} {product}")

            print("6-DOF Gamepad controls (HID mode):")
            print("  Left stick: Linear X/Y movement")
            print("  Right stick: Angular X/Y rotation")
            print("  Left/Right bumpers: Angular Z rotation (yaw)")
            print("  Left/Right triggers: Linear Z movement (up/down)")
            print(f"  {self.gripper_close_button} button: Close gripper (normally open)")
            print("  B button: Exit")

        except OSError as e:
            logging.error(f"Error opening gamepad: {e}")
            logging.error("You might need to run with sudo/admin privileges on some systems")
            self.running = False

    def stop(self):
        """Close HID device connection."""
        if self.device:
            self.device.close()
            self.device = None

    def update(self):
        """Read and process latest gamepad data."""
        for _ in range(10):  # Read multiple times for stable reading
            self._update()

    def _update(self):
        """Read and process the latest gamepad data."""
        if not self.device or not self.running:
            return

        try:
            data = self.device.read(64)
            if data and len(data) >= 8:
                # Normalize joystick values from 0-255 to -1.0-1.0
                self.left_x = (data[1] - 128) / 128.0
                self.left_y = (data[2] - 128) / 128.0
                self.right_x = (data[3] - 128) / 128.0
                self.right_y = (data[4] - 128) / 128.0

                # Apply deadzone
                self.left_x = 0 if abs(self.left_x) < self.deadzone else self.left_x
                self.left_y = 0 if abs(self.left_y) < self.deadzone else self.left_y
                self.right_x = 0 if abs(self.right_x) < self.deadzone else self.right_x
                self.right_y = 0 if abs(self.right_y) < self.deadzone else self.right_y

                # Parse button states (byte 5 for buttons, byte 6 for triggers/bumpers)
                buttons = data[5]
                triggers_bumpers = data[6]

                # Bumpers (for angular Z control)
                self.left_bumper = 1.0 if triggers_bumpers & 0x01 else 0.0
                self.right_bumper = 1.0 if triggers_bumpers & 0x02 else 0.0

                # Triggers (for linear Z control) - normalize from button press to analog
                self.left_trigger = 1.0 if triggers_bumpers & 0x04 else 0.0
                self.right_trigger = 1.0 if triggers_bumpers & 0x08 else 0.0

                # Gripper button (A/Cross typically bit 0)
                self.gripper_close_command = bool(buttons & 0x01)

                # B button for quit (typically bit 1)
                if buttons & 0x02:
                    self.running = False

        except OSError as e:
            logging.error(f"Error reading from gamepad: {e}")

    def get_6dof_deltas(self):
        """Get 6-DOF movement deltas from gamepad state."""
        # Calculate deltas with proper scaling
        delta_x = -self.left_y * self.linear_scale  # Forward/backward
        delta_y = -self.left_x * self.linear_scale  # Left/right
        delta_z = (self.right_trigger - self.left_trigger) * self.linear_scale  # Up/down

        angular_x = -self.right_y * self.angular_scale  # Pitch
        angular_y = -self.right_x * self.angular_scale  # Roll
        angular_z = (self.right_bumper - self.left_bumper) * self.angular_scale  # Yaw

        return delta_x, delta_y, delta_z, angular_x, angular_y, angular_z

    def gripper_command(self):
        """Return gripper command - normally open, close when button pressed."""
        if self.gripper_close_command:
            return "close"
        else:
            return "open"  # Default to open

    def should_quit(self):
        """Return True if user requested to quit."""
        return not self.running
