from rich.table import Table
from rich.console import Console
import time

console = Console()

# 動態更新表格數值
for i in range(10):
    # 每次都重新創建表格，避免清空數據時出錯
    table = Table(title="動態表格範例")

    # 添加表頭
    table.add_column("項目", justify="right", style="cyan", no_wrap=True)
    table.add_column("數值", style="magenta")

    # 填充數據
    data = [("A", i * 10), ("B", i * 20)]
    for row in data:
        table.add_row(row[0], str(row[1]))

    # 清空屏幕
    console.clear()

    # 渲染新的表格
    console.print(table)

    # 模擬數據更新
    time.sleep(1)
