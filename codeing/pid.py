class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, output_limits=(-3, 3), rate_limit=None):
        """
        初始化PID控制器參數
        :param Kp: 比例增益
        :param Ki: 積分增益
        :param Kd: 微分增益
        :param setpoint: 目標絕對位置
        :param output_limits: (最小值, 最大值) 控制器輸出的範圍限制
        :param rate_limit: 每次輸出最大變化量的限制
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.rate_limit = rate_limit
        self.integral = 0
        self.previous_error = 0
        self.previous_output = 0

    def reset(self):
        """
        重置PID控制器的所有迭代參數，包括積分和上一次誤差
        """
        self.integral = 0
        self.previous_error = 0
        self.previous_output = 0
    def compute(self, current_value, dt, reverse=False):
        """
        計算PID控制輸出，將結果限制在 ±3 之內，並可以選擇是否限制變化速率
        :param current_value: 當前值
        :param dt: 與上次更新的時間間隔
        :param reverse: 如果為 True，則進行X軸輸入反轉
        :return: 限制在 -3 到 3 之間的控制絕對輸出座標
        """
        # 如果X軸需要反向，對當前值取反
        if reverse:
            current_value = -current_value

        # 計算誤差
        error = self.setpoint - current_value

        # 比例項
        P = self.Kp * error

        # 積分項
        self.integral += error * dt
        I = self.Ki * self.integral

        # 微分項
        derivative = (error - self.previous_error) / dt if dt > 0 else 0
        D = self.Kd * derivative

        # 更新上一個誤差
        self.previous_error = error

        # 計算PID輸出
        output = P + I + D

        # 限制輸出變化速率
        if self.rate_limit is not None:
            delta_output = output - self.previous_output
            if delta_output > self.rate_limit:
                output = self.previous_output + self.rate_limit
            elif delta_output < -self.rate_limit:
                output = self.previous_output - self.rate_limit

        # 更新上一個輸出
        self.previous_output = output

        # 限制最終輸出範圍
        output = max(self.output_limits[0], min(self.output_limits[1], output))

        # 保留三位小數
        output = round(output, 3)

        return output
