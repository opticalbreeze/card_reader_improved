# 自動起動設定ガイド

このガイドでは、Windows版とラズパイ版の自動起動設定方法を説明します。

---

## 📋 目次

1. [Windows版の自動起動設定](#windows版の自動起動設定)
2. [ラズパイ版の自動起動設定](#ラズパイ版の自動起動設定)
3. [トラブルシューティング](#トラブルシューティング)

---

## 🪟 Windows版の自動起動設定

### 方法1: 仮想環境付き自動起動バッチファイル（推奨）

#### 📝 使い方

1. **バッチファイルを実行**
   ```
   start_venv.bat をダブルクリック
   ```

2. **初回実行時の動作**
   - 仮想環境が自動で作成されます
   - 必要なパッケージが自動インストールされます
   - クライアントが起動します

3. **2回目以降**
   - 仮想環境に自動で入り、すぐにクライアントが起動します

#### 🔧 スタートアップフォルダに登録（Windows起動時に自動起動）

1. **Windowsキー + R** を押して「ファイル名を指定して実行」を開く
2. 以下を入力して **OK**
   ```
   shell:startup
   ```
3. 開いたフォルダに `start_venv.bat` のショートカットを作成
4. 次回のWindows起動時から自動起動されます

#### ⚠️ スリープ復帰時の注意事項

- **スリープ復帰後のカードリーダー切断対策を実装済み**
- 30秒ごとにリーダーの状態を自動チェックします
- リーダーが切断された場合は自動で検出し、警告を表示します
- リーダーを再接続すると自動的に再検出されます

---

### 方法2: タスクスケジューラで自動起動

#### 📝 手順

1. **タスクスケジューラを起動**
   - Windowsキー + R → `taskschd.msc` と入力

2. **基本タスクの作成**
   - 「基本タスクの作成」をクリック
   - 名前: `打刻システムクライアント`
   - トリガー: `コンピューターの起動時`

3. **操作の設定**
   - 操作: `プログラムの開始`
   - プログラム/スクリプト: `start_venv.bat` のフルパスを入力
   - 開始: `start_venv.bat` があるフォルダのパスを入力

4. **完了**

---

## 🍓 ラズパイ版の自動起動設定

### 方法1: 自動設定スクリプト（推奨）

#### 📝 使い方

1. **スクリプトに実行権限を付与**
   ```bash
   cd /path/to/card_reader_improved
   chmod +x setup_autostart.sh
   chmod +x remove_autostart.sh
   ```

2. **自動起動を設定**
   ```bash
   sudo bash setup_autostart.sh
   ```

3. **確認メッセージ**
   - 今すぐ起動するか聞かれるので、必要に応じて `y` または `n` を入力

4. **次回の起動から自動起動されます**

#### 🔧 サービスの制御コマンド

```bash
# 状態確認
sudo systemctl status attendance-client

# 起動
sudo systemctl start attendance-client

# 停止
sudo systemctl stop attendance-client

# 再起動
sudo systemctl restart attendance-client

# ログ確認（リアルタイム）
sudo journalctl -u attendance-client -f

# ログ確認（最新100行）
sudo journalctl -u attendance-client -n 100

# 自動起動の有効化
sudo systemctl enable attendance-client

# 自動起動の無効化
sudo systemctl disable attendance-client
```

#### 🗑️ 自動起動を解除

```bash
sudo bash remove_autostart.sh
```

---

### 方法2: 手動でsystemdサービスを設定

#### 📝 手順

1. **サービスファイルを配置**
   ```bash
   sudo cp attendance-client.service /etc/systemd/system/
   ```

2. **サービスファイルを編集（パスを修正）**
   ```bash
   sudo nano /etc/systemd/system/attendance-client.service
   ```
   
   以下の項目を実際の環境に合わせて修正：
   - `User=pi` （実際のユーザー名）
   - `WorkingDirectory=/home/pi/card_reader_improved` （実際のパス）
   - `ExecStart=/usr/bin/python3 /home/pi/card_reader_improved/pi_client.py` （実際のパス）

3. **systemdをリロード**
   ```bash
   sudo systemctl daemon-reload
   ```

4. **自動起動を有効化**
   ```bash
   sudo systemctl enable attendance-client.service
   ```

5. **サービスを起動**
   ```bash
   sudo systemctl start attendance-client.service
   ```

6. **状態を確認**
   ```bash
   sudo systemctl status attendance-client.service
   ```

---

## 🔧 トラブルシューティング

### Windows版

#### ❌ 問題: バッチファイルを実行しても何も起きない

**解決策:**
1. バッチファイルを右クリック → 「編集」
2. パスが正しいか確認
3. コマンドプロンプトから直接実行してエラーを確認

#### ❌ 問題: スリープから復帰後にカードが読み取れない

**解決策:**
1. 30秒待つ（自動再検出が動作します）
2. ログに「リーダー切断」と表示されている場合:
   - USBケーブルを抜き差しする
   - または、クライアントを再起動する

#### ❌ 問題: 仮想環境の作成に失敗する

**解決策:**
1. Pythonが正しくインストールされているか確認
   ```
   python --version
   ```
2. 古いvenvフォルダを削除してから再実行
   ```
   rmdir /s /q venv
   start_venv.bat
   ```

---

### ラズパイ版

#### ❌ 問題: サービスが起動しない

**解決策1: ログを確認**
```bash
sudo journalctl -u attendance-client -n 50
```

**解決策2: パスを確認**
```bash
# サービスファイルを編集
sudo nano /etc/systemd/system/attendance-client.service

# WorkingDirectoryとExecStartのパスが正しいか確認
# 修正後、リロードして再起動
sudo systemctl daemon-reload
sudo systemctl restart attendance-client
```

**解決策3: 権限を確認**
```bash
# pi_client.pyに実行権限があるか確認
ls -l /path/to/pi_client.py

# 権限がない場合は付与
chmod +x /path/to/pi_client.py
```

#### ❌ 問題: カードリーダーが認識されない

**解決策:**
```bash
# サービスを停止
sudo systemctl stop attendance-client

# 手動で実行してエラーを確認
cd /path/to/card_reader_improved
python3 pi_client.py

# USBデバイスを確認
lsusb

# 必要なら権限を設定
sudo usermod -a -G plugdev pi
```

#### ❌ 問題: ネットワーク起動前にサービスが開始される

**解決策:**
サービスファイルに以下を追加：
```ini
[Unit]
After=network-online.target
Wants=network-online.target
```

---

## 📚 参考情報

### Windows版の動作確認

1. **タスクマネージャーで確認**
   - Ctrl + Shift + Esc
   - 「詳細」タブで `python.exe` または `pythonw.exe` を探す

2. **プロセス確認**
   ```
   tasklist | findstr python
   ```

### ラズパイ版の動作確認

1. **プロセス確認**
   ```bash
   ps aux | grep pi_client
   ```

2. **ポート確認（サーバー接続）**
   ```bash
   sudo netstat -tuln | grep 5000
   ```

3. **GPIO権限確認**
   ```bash
   groups pi | grep gpio
   ```

---

## ✅ 完了チェックリスト

### Windows版
- [ ] `start_venv.bat` を実行してクライアントが起動する
- [ ] スタートアップフォルダにショートカットを作成した
- [ ] Windows再起動後に自動起動することを確認した
- [ ] スリープ復帰後もカードが読み取れることを確認した

### ラズパイ版
- [ ] `setup_autostart.sh` を実行した
- [ ] `sudo systemctl status attendance-client` で状態を確認した
- [ ] ラズパイを再起動して自動起動を確認した
- [ ] カードリーダーが正常に動作することを確認した

---

## 📞 サポート

問題が解決しない場合は、以下の情報を添えて報告してください：

### Windows版
- Windowsのバージョン
- Pythonのバージョン
- エラーメッセージ
- `start_venv.bat` の実行ログ

### ラズパイ版
- Raspberry Piのモデル
- OSのバージョン（`uname -a`）
- サービスログ（`sudo journalctl -u attendance-client -n 100`）
- 手動実行時のエラーメッセージ

---

**最終更新日: 2024年**

