from rich.table import Table
from rich.console import Console
import os

class DynamicTable:
    def __init__(self):
        # 初始化Console对象
        self.console = Console()
        os.system('cls')
    def render_table(self, relative_x, relative_y, pidXout, pidYout):
        """
        渲染包含數值與修正值的表格
        :param relative_x: 相對x值
        :param relative_y: 相對y值
        :param pidXout: x修正值
        :param pidYout: y修正值
        """
        # 創建表格
        table = Table(title="位置與修正值")

        # 添加表頭
        table.add_column("描述", justify="left", style="cyan")
        table.add_column("值", justify="right", style="magenta")
        table.add_column("修正值", justify="right", style="green")

        # 添加數據行
        table.add_row("Green point relative to red point (x)", str(relative_x), str(pidXout))
        table.add_row("Green point relative to red point (y)", str(relative_y), str(pidYout))

        # 清空屏幕并渲染新的表格
        self.console.clear()
        self.console.print(table)
        self.console.print("請點視訊畫面後按q，即可關閉程序")

# 使用示例
if __name__ == "__main__":
    table = DynamicTable()

    # 示例數據
    relative_x = 10
    relative_y = 5
    pidXout = 0.15
    pidYout = -0.12

    # 渲染表格
    table.render_table(relative_x, relative_y, pidXout, pidYout)
