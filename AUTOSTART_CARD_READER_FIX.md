# 自動起動でカードリーダーが認識されない問題の修正

## 問題

- 自動起動時: カードリーダーが認識されない
- 手動起動時: 問題なく動作する

## 原因

1. **USBデバイスの認識タイミング**: 自動起動時、USBデバイスがまだ認識されていない
2. **PC/SCサービスの起動タイミング**: `pcscd`サービスが起動していない
3. **待機時間の不足**: デバイス認識前にプログラムが起動している

## 修正内容

### 1. `start_pi.sh`の修正

- USBデバイスの認識を待つ処理を追加（最大30秒）
- PC/SCサービスの起動確認・起動処理を追加
- ステップ番号を1/3から1/4に変更

### 2. `attendance-client-fixed.service`の修正

- `After=network.target pcscd.service`に変更（PC/SCサービスの起動を待つ）
- `Wants=pcscd.service`を追加
- `ExecStartPre=/bin/sleep 5`を追加（USBデバイス認識のための待機時間）

## 修正後の動作

1. システム起動
2. ネットワークとPC/SCサービスが起動するまで待機
3. 5秒待機（USBデバイス認識のため）
4. `start_pi.sh`を実行
5. USBデバイスの認識を待機（最大30秒）
6. PC/SCサービスの起動確認・起動
7. Pythonプログラムを起動

## 確認方法

```bash
# サービスログを確認
sudo journalctl -u attendance-client-fixed.service -f

# USBデバイスの認識を確認
lsusb | grep -E "054c:06c1|Sony|PaSoRi|NFC"

# PC/SCサービスの状態を確認
systemctl status pcscd
```

