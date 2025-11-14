# 自動起動設定ガイド

このガイドでは、Windows版とRaspberry Pi版の自動起動設定方法を説明します。

---

## 📋 目次

1. [Windows版の自動起動設定](#windows版の自動起動設定)
2. [Raspberry Pi版の自動起動設定](#raspberry-pi版の自動起動設定)
3. [トラブルシューティング](#トラブルシューティング)

---

## 🪟 Windows版の自動起動設定

### 方法1: スタートアップフォルダに登録（推奨）

#### 手順

1. **Windowsキー + R** を押して「ファイル名を指定して実行」を開く
2. 以下を入力して **OK**
   ```
   shell:startup
   ```
3. 開いたフォルダに `start_win.bat` のショートカットを作成
4. 次回のWindows起動時から自動起動されます

### 方法2: タスクスケジューラで自動起動

1. **タスクスケジューラを起動**
   - Windowsキー + R → `taskschd.msc` と入力

2. **基本タスクの作成**
   - 「基本タスクの作成」をクリック
   - 名前: `打刻システムクライアント`
   - トリガー: `コンピューターの起動時`

3. **操作の設定**
   - 操作: `プログラムの開始`
   - プログラム/スクリプト: `start_win.bat` のフルパスを入力

---

## 🍓 Raspberry Pi版の自動起動設定

### 自動設定スクリプトを使用（推奨）

```bash
cd ~/Desktop/attendance/card_reader_improved
chmod +x setup_autostart_fixed.sh
sudo bash setup_autostart_fixed.sh
```

このスクリプトが自動的に行うこと：
- サービスファイルを `/etc/systemd/system/` にコピー
- パスとユーザー名を自動調整
- `pcscd` グループの確認と作成
- ユーザーを `pcscd` グループに追加
- systemdをリロード
- サービスを有効化

### サービスの制御コマンド

```bash
# 状態確認
sudo systemctl status attendance-client-fixed.service

# 起動
sudo systemctl start attendance-client-fixed.service

# 停止
sudo systemctl stop attendance-client-fixed.service

# 再起動
sudo systemctl restart attendance-client-fixed.service

# ログ確認（リアルタイム）
sudo journalctl -u attendance-client-fixed.service -f

# ログ確認（最新100行）
sudo journalctl -u attendance-client-fixed.service -n 100

# 自動起動の有効化
sudo systemctl enable attendance-client-fixed.service

# 自動起動の無効化
sudo systemctl disable attendance-client-fixed.service
```

### 自動起動を解除

```bash
sudo systemctl disable attendance-client-fixed.service
sudo systemctl stop attendance-client-fixed.service
sudo rm /etc/systemd/system/attendance-client-fixed.service
sudo systemctl daemon-reload
```

---

## 🔧 トラブルシューティング

### Windows版

#### バッチファイルを実行しても何も起きない

1. バッチファイルを右クリック → 「編集」
2. パスが正しいか確認
3. コマンドプロンプトから直接実行してエラーを確認

#### スリープ復帰後にカードが読み取れない

- 30秒待つ（自動再検出が動作します）
- USBケーブルを抜き差しする
- クライアントを再起動する

### Raspberry Pi版

#### サービスが起動しない

**ログを確認:**
```bash
sudo journalctl -u attendance-client-fixed.service -n 50
```

**パスを確認:**
```bash
sudo nano /etc/systemd/system/attendance-client-fixed.service
# WorkingDirectoryとExecStartのパスが正しいか確認
sudo systemctl daemon-reload
sudo systemctl restart attendance-client-fixed.service
```

#### カードリーダーが認識されない

```bash
# サービスを停止
sudo systemctl stop attendance-client-fixed.service

# 手動で実行してエラーを確認
python3 pi_client.py

# USBデバイスを確認
lsusb
```

---

## 📚 関連ドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)

