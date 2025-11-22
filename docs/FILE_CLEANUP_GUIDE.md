# ファイル整理ガイド

このドキュメントでは、プロジェクト内のファイルを整理し、不要なファイルを削除する方針を説明します。

---

## 📋 ファイル分類

### ✅ **必須ファイル（削除しない）**

#### コアプログラム
- `pi_client.py` - Raspberry Pi版メインクライアント
- `pi_client_simple.py` - Raspberry Pi版シンプルクライアント
- `win_client.py` - Windows版メインクライアント
- `common_utils.py` - 共通ユーティリティ
- `constants.py` - 定数定義
- `gpio_config.py` - GPIO設定
- `lcd_i2c.py` - LCD制御
- `memory_monitor.py` - メモリモニタリング（オプション）
- `config.py` - 設定GUI

#### 設定ファイル
- `client_config.json` - 設定ファイル
- `client_config_sample.json` - 設定ファイルサンプル
- `requirements_unified.txt` - Raspberry Pi依存関係
- `requirements_windows.txt` - Windows依存関係

#### 起動スクリプト
- `start_pi.sh` - Raspberry Pi起動スクリプト
- `start_pi_simple.sh` - Raspberry Piシンプル版起動スクリプト
- `start_win.bat` - Windows起動スクリプト
- `start_venv.bat` - Windows仮想環境起動スクリプト
- `config.bat` - Windows設定GUI起動スクリプト

#### セットアップスクリプト
- `auto_setup.sh` - 自動セットアップ
- `setup.sh` - セットアップスクリプト
- `setup_autostart_fixed.sh` - 自動起動設定（改善版）
- `attendance-client-fixed.service` - systemdサービスファイル（改善版）
- `create_pcscd_group.sh` - pcscdグループ作成
- `fix_pcsc_permissions.sh` - PC/SC権限修正
- `fix_raspberry_locale.sh` - ロケール修正
- `setup_memory_monitor.sh` - メモリモニタリング設定

#### サービス管理スクリプト
- `manage_service.sh` - サービス管理（起動/停止/再起動/状態確認/ログ表示）
- `start_service.sh` - サービス起動
- `stop_service.sh` - サービス停止
- `view_service_logs.sh` - ログ表示
- `remove_autostart.sh` - 自動起動削除

#### ドキュメント
- `README.md` - メインREADME
- `README_ATTENDANCE.md` - 勤怠システム詳細
- `SYSTEM_OVERVIEW.md` - システム概要
- `LICENSE` - ライセンス
- `docs/` フォルダ内のすべてのドキュメント

---

### ⚠️ **削除推奨ファイル（古いバージョン）**

#### 古い自動起動設定
- `setup_autostart.sh` - `setup_autostart_fixed.sh`の古いバージョン
- `attendance-client.service` - `attendance-client-fixed.service`の古いバージョン

**理由**: 改善版が存在し、古いバージョンは使用されていません。

---

### ❓ **検討が必要なファイル（用途を確認）**

#### 更新スクリプト
- `apply_updates.sh` - 更新適用スクリプト
- `raspberry_pi_update_steps.sh` - Raspberry Pi更新手順
- `pull_from_github.sh` - GitHubから取得
- `update_from_github.sh` - GitHubから更新

**検討事項**: 
- これらのスクリプトは実際に使用されていますか？
- `docs/UPDATE_GUIDE.md`に手順が記載されているため、重複の可能性があります。
- 必要に応じて`docs/UPDATE_GUIDE.md`に統合し、スクリプトは削除できます。

#### 古いドキュメント
- `QUICK_SETUP_RASPBERRY_PI.txt` - クイックセットアップガイド

**検討事項**:
- 内容が`docs/RASPBERRY_PI_SETUP_GUIDE.md`と重複している可能性があります。
- 必要に応じて`docs/RASPBERRY_PI_SETUP_GUIDE.md`に統合し、削除できます。

---

## 🗑️ 削除推奨リスト

以下のファイルは削除を推奨します：

### 1. 古いバージョンのファイル
```bash
# 古い自動起動設定
rm setup_autostart.sh
rm attendance-client.service
```

### 2. 重複・未使用の可能性があるファイル
```bash
# 更新スクリプト（使用されていない場合）
rm apply_updates.sh
rm raspberry_pi_update_steps.sh
rm pull_from_github.sh
rm update_from_github.sh

# 古いドキュメント（内容が統合されている場合）
rm QUICK_SETUP_RASPBERRY_PI.txt
```

---

## 📝 整理後の推奨構成

```
card_reader_improved/
├── コアプログラム
│   ├── pi_client.py
│   ├── pi_client_simple.py
│   ├── win_client.py
│   ├── common_utils.py
│   ├── constants.py
│   ├── gpio_config.py
│   ├── lcd_i2c.py
│   ├── memory_monitor.py
│   └── config.py
│
├── 設定ファイル
│   ├── client_config.json
│   ├── client_config_sample.json
│   ├── requirements_unified.txt
│   └── requirements_windows.txt
│
├── 起動スクリプト
│   ├── start_pi.sh
│   ├── start_pi_simple.sh
│   ├── start_win.bat
│   ├── start_venv.bat
│   └── config.bat
│
├── セットアップスクリプト
│   ├── auto_setup.sh
│   ├── setup.sh
│   ├── setup_autostart_fixed.sh
│   ├── attendance-client-fixed.service
│   ├── create_pcscd_group.sh
│   ├── fix_pcsc_permissions.sh
│   ├── fix_raspberry_locale.sh
│   └── setup_memory_monitor.sh
│
├── サービス管理スクリプト
│   ├── manage_service.sh
│   ├── start_service.sh
│   ├── stop_service.sh
│   ├── view_service_logs.sh
│   └── remove_autostart.sh
│
├── ドキュメント
│   ├── README.md
│   ├── README_ATTENDANCE.md
│   ├── SYSTEM_OVERVIEW.md
│   ├── LICENSE
│   └── docs/
│       └── （すべてのドキュメント）
│
└── その他
    ├── send_to_raspberry.ps1
    └── send_to_raspberry.sh
```

---

## 🔍 ファイル使用状況の確認方法

### 1. スクリプトの参照を確認
```bash
# 特定のファイルが参照されているか確認
grep -r "setup_autostart.sh" .
grep -r "attendance-client.service" .
grep -r "apply_updates.sh" .
```

### 2. ドキュメント内の参照を確認
```bash
# ドキュメント内で参照されているか確認
grep -r "QUICK_SETUP_RASPBERRY_PI.txt" docs/
grep -r "pull_from_github.sh" docs/
```

### 3. Git履歴を確認
```bash
# ファイルの最終更新日を確認
git log --format="%ai %s" -- setup_autostart.sh
git log --format="%ai %s" -- attendance-client.service
```

---

## ✅ 整理手順

1. **バックアップを作成**
   ```bash
   git add .
   git commit -m "整理前のバックアップ"
   ```

2. **古いバージョンのファイルを削除**
   ```bash
   rm setup_autostart.sh
   rm attendance-client.service
   ```

3. **未使用ファイルを確認して削除**
   ```bash
   # 使用されていないことを確認してから削除
   rm apply_updates.sh
   rm raspberry_pi_update_steps.sh
   rm pull_from_github.sh
   rm update_from_github.sh
   rm QUICK_SETUP_RASPBERRY_PI.txt
   ```

4. **変更をコミット**
   ```bash
   git add .
   git commit -m "不要なファイルを削除して整理"
   ```

---

## 📚 関連ドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [更新ガイド](UPDATE_GUIDE.md)
- [自動起動設定ガイド](AUTOSTART_GUIDE.md)

