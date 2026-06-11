# import math

# class TargetPID:
#     def __init__(self, center_x: int, center_y: int):
#         self.center_x = center_x
#         self.center_y = center_y

#         # PID state for pan
#         self._integral_pan = 0.0
#         self._last_error_pan = 0.0

#         # PID state for tilt
#         self._integral_tilt = 0.0
#         self._last_error_tilt = 0.0

#     def update(self, cx: int, cy: int,
#                kp: float, ki: float, kd: float, 
#                min_rpm: float, max_rpm: float,
#                enable_aim: bool, enable_shoot: bool,
#                shoot_region_radius: float):
#         """
#         Returns: pan_velocity, tilt_velocity, shoot(bool), erMsg(str)
#         """
        
#         try:
#             if not enable_aim:
#                 return 0.0, 0.0, False, ""  # no aiming if disabled

#             # calculate errors
#             error_pan = self.center_x - cx
#             error_tilt = self.center_y - cy

#             # PID for pan
#             self._integral_pan += error_pan
#             d_error_pan = error_pan - self._last_error_pan
#             pan_cmd = (kp * error_pan) + (ki * self._integral_pan) + (kd * d_error_pan)
#             self._last_error_pan = error_pan

#             # PID for tilt
#             self._integral_tilt += error_tilt
#             d_error_tilt = error_tilt - self._last_error_tilt
#             tilt_cmd = (kp * error_tilt) + (ki * self._integral_tilt) + (kd * d_error_tilt)
#             self._last_error_tilt = error_tilt

#             # Clamp speed commands
#             # Define a helper function to apply minimum RPM
#             # This ensures that if the command is below the minimum RPM, it will be set to the minimum RPM 
#             # this way we avoid very small, ineffective outputs.
#             # and if it exceeds the maximum RPM, it will be clamped to the maximum RPM
#             def apply_min(cmd, min_val):
#                 if cmd == 0:
#                     return 0.0
#                 if abs(cmd) < abs(min_val):
#                     return math.copysign(abs(min_val), cmd)
#                 return cmd

#             pan_cmd = apply_min(pan_cmd, min_rpm)
#             tilt_cmd = apply_min(tilt_cmd, min_rpm)
#             pan_cmd = max(-max_rpm, min(max_rpm, pan_cmd))
#             tilt_cmd = max(-max_rpm, min(max_rpm, tilt_cmd))

#             # Check if we are within the shoot region
#             dist_to_center = math.sqrt(error_pan**2 + error_tilt**2)
#             if enable_shoot and dist_to_center <= shoot_region_radius:
#                 shoot = True
#             else:
#                 shoot = False

#             return pan_cmd, tilt_cmd, shoot, ""

#         except Exception as e:
#             return 0.0, 0.0, False, f"❌ PID update error: {e}"
        
#     def reset(self):
#         self._integral_pan = 0.0
#         self._last_error_pan = 0.0
#         self._integral_tilt = 0.0
#         self._last_error_tilt = 0.0

import math

class TargetPID:
    def __init__(self, center_x: int, center_y: int):
        # Center coordinates for aiming
        self.center_x = center_x
        self.center_y = center_y

        # PID error state for pan and tilt
        self._integral_pan = 0.0
        self._last_error_pan = 0.0
        self._integral_tilt = 0.0
        self._last_error_tilt = 0.0

        # # PID coefficients
        # # These will be set later using set_params()
        # kp_pan = 0.0
        # self.ki_pan = 0.0
        # self.kd_pan = 0.0
        # self.kp_tilt = 0.0
        # self.ki_tilt = 0.0
        # self.kd_tilt = 0.0

        # # RPM limits
        # # These will also be set later using set_params()
        # self.min_rpm = 0.0
        # self.max_rpm = 0.0

        # # Shoot region radius
        # self.shoot_region_radius = 0.0

    def reset(self):
        self._integral_pan = 0.0
        self._last_error_pan = 0.0
        self._integral_tilt = 0.0
        self._last_error_tilt = 0.0

    # Update PID based on current target position
    def update(self, cx: int, cy: int,
               enable_pid: bool,
               enable_aim: bool,
               enable_shoot: bool,
               kp_pan: float, ki_pan: float, kd_pan: float,
               kp_tilt: float, ki_tilt: float, kd_tilt: float,
               min_rpm: float, max_rpm: float,
               shoot_region_radius: float):
        """
        Returns: pan_velocity, tilt_velocity, shoot(bool), erMsg(str)
        """
        try:
            if not enable_pid:
                self.reset()
                return 0.0, 0.0, False, ""

            # Calculate errors
            error_pan = self.center_x - cx
            error_tilt = self.center_y - cy

            # Calculate PID for pan
            self._integral_pan += error_pan
            d_error_pan = error_pan - self._last_error_pan
            pan_cmd = (kp_pan * error_pan) + (ki_pan * self._integral_pan) + (kd_pan * d_error_pan)
            self._last_error_pan = error_pan

            # Calculate PID for tilt
            self._integral_tilt += error_tilt
            d_error_tilt = error_tilt - self._last_error_tilt
            tilt_cmd = (kp_tilt * error_tilt) + (ki_tilt * self._integral_tilt) + (kd_tilt * d_error_tilt)
            self._last_error_tilt = error_tilt

            # ----Clamp speed commands----

            # Clamping to minimum RPM
            # Define a helper function to apply minimum RPM
            # This ensures that if the command is below the minimum RPM, it will be set to the minimum RPM
            # this way we avoid very small, ineffective outputs.
            # def apply_min(cmd, min_val):
            #     if cmd == 0:
            #         return 0.0
            #     if abs(cmd) < abs(min_val):
            #         return math.copysign(abs(min_val), cmd)
            #     return cmd
            def apply_min(cmd, min_val):
                if abs(cmd) < abs(min_val):
                    return 0.0
                return cmd

            pan_cmd = apply_min(pan_cmd, min_rpm)
            tilt_cmd = apply_min(tilt_cmd, min_rpm)

            # Clamping to maximum RPM
            pan_cmd = max(-max_rpm, min(max_rpm, pan_cmd))
            tilt_cmd = max(-max_rpm, min(max_rpm, tilt_cmd))

            # shoot logic
            # Check if we are within the shoot region
            dist_to_center = math.sqrt(error_pan**2 + error_tilt**2)
            shoot = False
            shoot = enable_shoot and dist_to_center <= shoot_region_radius
            # if shoot:
            #     self.reset()

            if not enable_aim:
                return 0.0, 0.0, shoot, ""
            
            return pan_cmd, tilt_cmd, shoot, ""

        except Exception as e:
            return 0.0, 0.0, False, f"❌ PID update error: {e}"
