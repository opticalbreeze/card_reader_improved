# トラブルシューティングガイド

このガイドでは、よくある問題とその解決方法を説明します。

---

## 🔧 PC/SCアクセス権限エラー

### 症状
- カードリーダーが検出されない
- `Permission denied`エラーが発生

### 解決方法

#### 1. pcscdグループにユーザーを追加

```bash
sudo usermod -a -G pcscd $USER
```

#### 2. グループが存在しない場合は作成

```bash
sudo groupadd pcscd
sudo usermod -a -G pcscd $USER
```

#### 3. 再ログイン

```bash
# 現在のセッションを終了して再ログイン
# または
newgrp pcscd
```

#### 4. サービスファイルの確認

`attendance-client-fixed.service`に以下が含まれているか確認：

```ini
[Service]
Group=pcscd
```

---

## 🌐 エンコーディング問題

### 症状
- 日本語が文字化けする
- WindowsでUTF-8が正しく表示されない

### 解決方法

#### Windows環境での文字化け対策

`common_utils.py`の`setup_windows_encoding()`関数が自動的に処理します。

手動で設定する場合：

```python
import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
```

---

## 🍓 ラズパイロケール設定

### 症状
- ロケール関連のエラーが発生
- 日本語が正しく表示されない

### 解決方法

```bash
# ロケールを設定
sudo locale-gen ja_JP.UTF-8
sudo update-locale LANG=ja_JP.UTF-8

# 再起動
sudo reboot
```

---

## 🔌 カードリーダーが検出されない

### 確認事項

1. **USB接続の確認**
   ```bash
   lsusb
   # カードリーダーが表示されるか確認
   ```

2. **PC/SCサービスの状態**
   ```bash
   sudo systemctl status pcscd
   # 起動しているか確認
   ```

3. **リーダーの再検出**
   - USBケーブルを抜き差し
   - 別のUSBポートで試す
   - システムを再起動

4. **権限の確認**
   ```bash
   groups
   # pcscdグループに含まれているか確認
   ```

---

## 🚀 自動起動が動作しない

### 確認事項

1. **サービスファイルの確認**
   ```bash
   sudo systemctl status attendance-client-fixed.service
   ```

2. **ログの確認**
   ```bash
   sudo journalctl -u attendance-client-fixed.service -n 100
   ```

3. **環境変数の確認**
   - 仮想環境のパスが正しいか
   - 作業ディレクトリが正しいか
   - PC/SCソケットパスが正しいか

---

## 📊 プロセス環境の検証

手動起動と自動起動で環境が異なる場合の確認方法：

```bash
# 検証スクリプトを実行
chmod +x check_actual_difference.sh
./check_actual_difference.sh
```

確認すべき項目：
- PATHに仮想環境のパスが含まれているか
- VIRTUAL_ENV環境変数が設定されているか
- LANG, LC_ALLが設定されているか

---

## 🔍 その他の問題

### サーバーに接続できない

1. サーバーが起動しているか確認
2. ファイアウォール設定を確認
3. 同じネットワークに接続しているか確認
4. `client_config.json`のサーバーIPを確認

### データベースエラー

```bash
# データベースを再生成（注意：既存データは削除されます）
rm attendance.db
python3 pi_client.py
```

---

## 📞 サポート

問題が解決しない場合は、以下を確認してください：

1. ログファイルの内容
2. エラーメッセージの全文
3. 実行環境（OS、Pythonバージョン等）
4. ハードウェア情報（カードリーダーの型番等）

