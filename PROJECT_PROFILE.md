# Project Profile

## 使用者目標

- 專案名稱：Ridgeback + Franka + D455 YOLO 工廠貨架感知展示。
- 以 `/home/rci05/User/Lin/test_claude_mcp_04` 的已驗證 Ridgeback、Franka Panda、手腕 D455、IK target、RGB 與深度量測架構為唯讀基準，在本工作區建立衍生專案。
- 第一版只處理感知，不執行機械手臂抓取或路徑規劃。
- 在工廠貨架情境中即時辨識最多 20 件物品，固定類別為：
  1. 箱子（`box`）
  2. 瓶子（`bottle`）
  3. 手工具（`hand_tool`）
  4. 球（`ball`）
  5. 機械零件（`mechanical_part`）
- 每個類別至少使用五種不同形狀、尺寸與顏色的物品；預設準備六種以上，以便保留未參與訓練的外觀作為泛化測試。
- 每個可信辨識結果顯示「類別／信心分數／表面世界座標」，例如 `瓶子／94%／世界座標 (...)`。
- 每個物體提供：
  - 相機量到的代表性可見表面點之世界座標；
  - 相機到該表面點的歐幾里得距離；
  - 該物體可見表面的三維世界座標範圍。
- 正式操作畫面與主要輸出不顯示相機座標，不估算或輸出物體中心。
- 無可靠類別但具有有效深度表面的候選物，顯示為「未知物體」，不得強制猜測成五個已知類別之一。

## 預期 GUI 操作流程

1. 開啟預計建立的 `scenes/ridgeback_franka_d455_yolo_demo.usd`。
2. 按下 **Play**。
3. 在 Isaac Sim Script Editor 執行預計建立的啟動 script；預設入口為 `scripts/demo_start.py` 中的 `demo_start()`。
4. 拖曳或旋轉 `/World/IKTarget`，讓手腕 D455 改變觀察位置。
5. 預計建立一個 Isaac Sim dockable 即時感知視窗，至少包含：
   - 左眼 RGB 與 YOLO instance mask、類別及信心分數；
   - 深度預覽與代表性表面點；
   - 各物體的類別、信心、表面距離、表面世界座標及可見三維範圍。
6. 即時流程預計以 `demo_perception_status()` 回報模型、FPS、延遲、有效深度及錯誤狀態。
7. 在 Script Editor 輸入 `demo_capture()`，擷取當下左右 RGB、深度、辨識視覺化、表面量測與結構化結果。
8. 使用 `demo_stop()` 停止 IK 與感知 callbacks，釋放 render products 與推論資源。

## 現有專案事實

- 正式 working copy 位於 `/home/rci05/User/Lin/test_codex_claude_mcp_1/ridgeback-franka-d455-yolo-demo`，追蹤 GitHub `hayashimatsu/ridgeback-franka-d455-yolo-demo` 的 `main` branch。
- M0 已從唯讀基準導入目前的 USD、三支 runtime scripts、必要文件、manifest、歷史 compact acceptance 與五張 golden images；來源 commit 與逐檔 SHA-256 記錄於 `validation/baseline/provenance.json`。
- 唯讀基準專案：`/home/rci05/User/Lin/test_claude_mcp_04`。
- 基準專案目前位於 Git `main`，既有 release acceptance 為 `pass`。
- 歷史 release acceptance 記錄的場景 SHA-256 為 `b3e83bd6...`，目前導入場景為 `ce5690e4...`；兩者不一致，因此歷史 pass 不可直接繼承，目前場景仍需 clean-reopen 驗證。
- 基準場景：`/home/rci05/User/Lin/test_claude_mcp_04/scenes/ridgeback_franka_d455_demo.usd`。
- 基準場景已驗證：
  - Ridgeback + Franka Panda；
  - `/World/IKTarget` GUI 操作；
  - 手腕安裝的 D455；
  - 左、右及 color RGB；
  - 左眼 axial/radial depth 與右眼 axial depth；
  - runtime 相機世界姿態；
  - 表面點的相機到世界座標轉換；
  - 唯一且不覆寫的 `demo_capture()` 輸出目錄；
  - capture 前後 root USD hash 不變。
- 基準 capture 使用 `640 x 480` 解析度，驗證的左右目 baseline 為 `0.095 m ± 0.002 m`。
- 既有深度區域演算法辨識的是可見表面，不是語意物件；深度相近或接觸的物體可能合併。
- 既有輸出是 RTX axial/radial depth 與 depth preview，不是真正由左右 RGB 計算的 stereo disparity。
- Isaac Sim runtime 與 Codex MCP ping 可達，資產根目錄顯示 Isaac Sim Assets 6.0。
- Claude CLI 的 `isaac-sim` MCP user registration 目前存在，但唯讀檢查時回報連線失敗；執行階段需重新驗證。
- Isaac Sim 6.0 安裝包含 Replicator、semantic labels、semantic/instance segmentation 與 2D bounding-box synthetic-data 能力。
- Isaac Sim 內建 Python 的唯讀檢查未發現 PyTorch、TorchVision、Ultralytics、ONNX Runtime 或 TensorRT Python package；OpenCV 可用。
- 基準 repo 目前有一份使用者未追蹤文件 `docs/explanation-for-the-measurements.md`，不得刪除、覆寫或納入本專案時改寫其來源內容。

## 預計建立的內容

以下項目尚未建立，或只有需要擴充的 M0 基準版本：

- `scenes/ridgeback_franka_d455_yolo_demo.usd`
  - 從基準場景建立的新 revision；
  - 加入工廠貨架與五類目標資產；
  - 目標物預設可不受重力，但必須位於相機有效深度與可視範圍內。
- `config/object_catalog.yaml`
  - 記錄五類 taxonomy、每類資產、授權／來源、尺度範圍及 train/validation/held-out 分組。
- `config/perception.yaml`
  - 記錄模型、信心門檻、深度範圍、即時更新率及 RGB-D fusion 設定。
- `scripts/generate_yolo_dataset.py`
  - 使用 Isaac Sim Replicator 產生左眼 RGB、instance/semantic labels、instance masks 與 YOLO segmentation 標註；
  - 隨機化 1–20 個物品的位置、旋轉、尺度、材質、光線、遮擋與相機視角；
  - 貨架、牆面、地板、機器人與其他工廠設備作為負樣本。
- `training/`
  - 存放 YOLO dataset 設定、訓練、驗證、benchmark 與 export 設定；
  - 訓練在與 Isaac Sim 隔離的 Python 環境執行；
  - 從預訓練的小型 YOLO segmentation 模型開始，並與中型模型比較；
  - 選擇達到精度門檻的最快模型；
  - 匯出 ONNX 或 TensorRT 部署格式前，先在實際 Isaac Sim runtime benchmark。
- `scripts/realtime_perception.py`
  - 對 depth-aligned 左眼 RGB 執行 YOLO segmentation；
  - 將 instance mask 與有效左眼深度融合；
  - 計算代表性可見表面點、距離、世界座標與可見三維範圍；
  - 保留相機座標作內部轉換與驗證，但不作主要使用者輸出；
  - 對有深度候選但無可信分類的表面回報「未知物體」。
- `scripts/perception_ui.py`
  - 建立 Isaac Sim dockable 即時 RGB／YOLO、深度與結果表格視窗。
- `scripts/demo_start.py`
  - M0 已導入未修改的基準入口；後續預計在新 revision 工作中擴充；
  - 預計公開 `demo_start()`、`demo_capture()`、`demo_perception_status()` 與 `demo_stop()`；
  - 重複啟動不得累積 callbacks 或 render products。
- `outputs/datasets/`
  - 合成訓練資料，預計建立且預設不納入 Git。
- `outputs/training/`
  - checkpoints、metrics、plots 與模型比較結果，預計建立且預設不納入 Git。
- `outputs/captures/<YYYY-MMDD-sequence>/`
  - 預計建立且不得覆寫既有 capture；
  - 預計包含左右 RGB、深度陣列與預覽、YOLO overlay、深度／表面 overlay、perception JSON、measurements JSON 與 capture provenance。
- `validation/release_acceptance.json`
  - 單一、精簡、可驗證的 release acceptance record。
- 操作、資料產生、訓練、資產擴充與驗證文件。

## 保護與保存政策

- `/home/rci05/User/Lin/test_claude_mcp_04` 整個來源 repo 為唯讀工程基準；未經使用者明確授權，不得在其中寫入、安裝、改名、刪除或提交任何內容。
- 不得覆寫基準場景 `scenes/ridgeback_franka_d455_demo.usd`。
- 場景修改一律建立新 USD revision，驗證通過前不得改變預設場景指標。
- 不得將 Play 中的機械手臂姿態、診斷狀態或暫時 runtime 狀態意外存入 release USD root layer。
- 不得把使用者未追蹤的 `docs/explanation-for-the-measurements.md` 視為可清理檔案。
- 產生訓練資料、模型 checkpoints、probe、失敗嘗試及 benchmark 放在 ignored `outputs/` 或 `validation/tmp/`。
- release 只保存必要設定、scripts、部署所需模型檔、少量人工檢查過的 golden images 與一份 acceptance record。
- capture 期間與 capture 後必須確認 root USD hash 不變，並恢復 IK target 原有可見性。
- 任何外部資產納入 catalog 前須記錄來源與使用條件；不得假設所有 Omniverse／SimReady 資產都可任意重新散布。
- 模型依賴使用隔離環境或明確部署 artifact；不得未經驗證直接修改 Isaac Sim 內建 Python 環境。
- 未經使用者明確授權，不得修改 MCP server implementation、credentials 或 user-level registration。

## 執行與交接文件

- 每次 milestone 工作前必讀 `milestones/CURRENT.md`、
  `milestones/AGENT_HANDOFF.md`、目標 milestone 的 `STATUS.md` 與累積
  `LOG.md`。
- Agent 1 依序負責 M1-M3，Agent 2 依序負責 M4-M5，Agent 3 依序負責
  M6-M7；前段 handoff gate 未通過時，後段不得開始。
- 每次執行結束都必須追加 milestone log、更新 status 與 current pointer，
  並記錄 evidence、失敗、決策、commit SHA 與下一個最小動作。
- 既有 log 只能追加，不得改寫或刪除；修正以新的 dated entry 說明。

## 可觀察的 acceptance gates

1. **乾淨開啟與 Play 穩定性**
   - 新 USD revision 可從乾淨 GUI session 直接開啟；
   - Play 不使手臂、相機、貨架或物體非預期跳動；
   - IK controller error count 為 0。
2. **IK 與相機 attachment**
   - 僅有一個 IK callback；
   - 拖曳 `/World/IKTarget` 可移動 Panda 七個手臂關節；
   - D455 在兩個差異明顯且可達的 pose 間保持相對 `panda_hand` 剛性。
3. **資料集完整性**
   - 五個類別皆有至少五種不同資產；預設目標為每類六種以上；
   - train、validation 與 held-out asset identities 不重疊；
   - 每張訓練影像與標註一一對應，類別、mask 與 image dimensions 有效；
   - 資料包含 1–20 件物品、遮擋、光照、材質、尺度、背景與視角變化。
4. **辨識精度**
   - 獨立 validation set 的每類 precision 至少 `0.90`；
   - 獨立 validation set 的每類 recall 至少 `0.90`；
   - 整體 `mAP50` 至少 `0.90`；
   - 記錄 `mAP50-95`，但在第一輪 benchmark 前不將其設為阻擋 release 的硬門檻。
5. **20 件物品場景**
   - 同一畫面可包含最多 20 件、涵蓋五類的物品；
   - 結果不因物件排序而覆寫或混用；
   - 每個可信 instance 都有獨立類別、信心、mask 與表面量測結果。
6. **RGB-D fusion 與座標**
   - 報告的代表性表面點必須位於該 YOLO instance mask 內且具有有效深度；
   - 輸出的正式座標為世界座標；
   - 相機點轉世界座標的閉合誤差不超過 `1 mm`；
   - 距離為相機光學中心到同一代表性表面點的歐幾里得距離；
   - 不把表面座標稱為或替換成物體中心。
7. **即時效能**
   - 在 `640 x 480`、最多 20 件物品的指定展示場景中，目標至少 `10` 次完整感知更新／秒；
   - 報告 median 與 p95 inference／end-to-end latency；
   - 即時感知不得阻塞 IK 操作或累積重複 callback；
   - 若中型模型未達效能門檻，使用小型模型或已驗證的 ONNX／TensorRT export。
8. **未知物體行為**
   - 有有效深度表面但沒有達信心門檻的 YOLO instance 時，顯示「未知物體」；
   - 未知物體不得被強制歸入五類之一；
   - 貨架、地板與機器人不得被回報為五類目標物。
9. **即時 GUI**
   - GUI 同步顯示 RGB／YOLO、深度／表面點與結構化結果；
   - 每筆主要結果至少包含類別、信心、表面距離、表面世界座標與可見三維範圍；
   - 不在主要操作畫面顯示相機座標或物體中心估計。
10. **擷取與保存**
    - `demo_capture()` 產生非黑 RGB、有效深度、YOLO overlay、量測 overlay 與結構化 JSON；
    - 左右目 baseline 為 `0.095 m ± 0.002 m`；
    - 連續兩次無標籤 capture 使用不同目錄且不覆寫；
    - capture 後 IK target 可見性恢復；
    - capture 前後 root USD SHA-256 相同。
11. **Release 證據**
    - 從乾淨 GUI reopen 執行完整操作流程；
    - 人工檢視代表性 RGB、YOLO mask、深度與表面 overlay；
    - `validation/release_acceptance.json` 記錄 stage provenance、模型 hash、dataset split、精度、FPS、latency、座標檢查、capture 完整性、限制與失敗探針。

## 尚未決定的選配項目

- **真正的 stereo disparity**：第一版預設使用既有且已驗證的 RTX axial/radial depth 完成 YOLO 與世界座標融合，同時保存左右 RGB。真正由左右 RGB 計算 disparity、深度與誤差比較，保留為後續廉價雙鏡頭里程碑，不阻擋第一版 acceptance。
- **實體廉價雙鏡頭移植**：本專案保留相機模型、內外參、影像與部署介面，但第一版不宣稱 sim-to-real 成功。
- **自動抓取與 motion planning**：不在第一版範圍；第一版輸出可供未來抓取流程消費的表面世界座標。
- **最終 YOLO 版本與模型尺寸**：由 validation 精度及實際 Isaac Sim runtime benchmark 決定；預設比較小型與中型 segmentation 模型。
- **TensorRT 部署**：只有在 runtime 確認 GPU、driver、TensorRT 相容性且能改善 acceptance 指標時啟用。
- **更嚴格的 `mAP50-95` release 門檻**：先完成第一輪資料與模型 benchmark，再以實測結果提出門檻，不在尚無基準時任意指定。
