# 📘 mediapipe-face-servo-control 專案手冊

## 🧠 專案簡介
此專案結合：
- **MediaPipe FaceMesh** 人臉特徵點檢測
- **雙軸 PID 控制演算法**
- **G-code 控制訊號輸出**

用於控制雙自由度機構自動追蹤使用者的臉部位置，適合智慧攝影機、互動裝置、機器人應用等場景。

---

## 📂 專案架構

```
mediapipe-face-servo-control/
├── rmvc.py             # 主程式：偵測 + PID + 串口傳送
├── pid.py              # PID 控制邏輯
├── config.ini          # 設定檔（攝影機與 PID 參數）
├── csic.dest           # MediaPipe 模型（臉部特徵點）
├── DynamicTable.py     # Rich 終端表格視覺化
├── rmvc.spec           # pyinstaller 打包規格檔
```

---

## ⚙️ 執行步驟

### 1️⃣ 建立虛擬環境（建議）並安裝依賴套件

你可以使用以下步驟建立一個乾淨的虛擬環境來避免相依問題：

```bash
# 建立虛擬環境（可自定 venv 名稱）
python -m venv venv

# 啟動虛擬環境
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安裝必要套件
pip install -r requirements.txt
```

如未提供 `requirements.txt`，可手動安裝下列套件：


```bash
pip install opencv-python mediapipe numpy pyserial rich
```

產出 `requirements.txt` 的方式如下：

```bash
pip freeze > requirements.txt
```

### 2️⃣ 編輯設定檔（config.ini）

```ini
[settings]
port = COM10            # 串口（依照設備修改）
baudrate = 115200
draw_grid = false       # 是否顯示臉部網格
cam_id = 0              # 攝影機 ID

[PID_X]
Kp = 0.004
Ki = 0.006
Kd = 0.005
setpoint = 0
output_limits_min = -3
output_limits_max = 3
rate_limit = 0.5

[PID_Y]
Kp = 0.004
Ki = 0.006
Kd = 0.005
setpoint = 0
output_limits_min = -3
output_limits_max = 3
rate_limit = 0.5
```

### 3️⃣ 安裝相依套件（若提供 requirements.txt）

若專案中已包含 `requirements.txt`，可直接安裝所有必要套件：

```bash
pip install -r requirements.txt
```

---
    
### 4️⃣ 執行程式

```bash
python rmvc.py
```

---

## 🧮 系統流程說明

### 👁️ 人臉定位
- 使用 MediaPipe 模型 (`csic.dest`) 偵測 468 個臉部特徵點
- 使用鼻尖（Landmark #1）為追蹤點
- 計算其相對畫面中心的偏移 `(x, y)`

### 🧠 PID 控制（`pid.py`）
- 每軸建立 `PIDController` 實例
- 每 0.5 秒更新控制量
- 限制最大變化速率與輸出範圍

### 🧵 串口控制
- 發送 G-code 指令：`G1 X[修正量] Y[修正量] F1000`

### 📊 即時表格（`DynamicTable.py`）
- 使用 Rich 套件顯示誤差與修正量

---

## 🛠️ 實用技巧與除錯建議

| 問題                       | 解法與建議                                                   |
|--------------------------|------------------------------------------------------------|
| 攝影機無影像              | 檢查 `cam_id` 是否正確，建議使用 `0` 或試試外接 USB 攝影機     |
| 串口失敗（連不上）        | 確認 COM 編號與 Baudrate 設定與硬體一致                        |
| 人臉長時間消失無動作      | 超過 4 秒無法偵測人臉，系統自動發送 `G1 X0 Y0` 指令歸位         |
| 表格亂碼或不刷新          | 建議使用 Windows CMD 或支援 ANSI 的終端環境（如 VSCode）        |

---

## 🔧 可擴展方向

- 依臉部角度控制更多自由度
- 將 G-code 改為伺服命令或 PWM 控制
- 導入自適應 PID 或 Kalman 濾波器提升穩定性

---

## 📄 授權與貢獻

本專案採用 MIT 授權，歡迎開源貢獻、報 issue、改進功能。