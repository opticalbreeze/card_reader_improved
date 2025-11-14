# プロセスの違いを検証する方法

## ラズパイ側で実行

```bash
cd ~/Desktop/attendance/card_reader_improved

# 検証スクリプトを実行
chmod +x check_actual_difference.sh
./check_actual_difference.sh
```

## 確認すべき項目

### 1. 手動起動時の環境
- PATHに仮想環境のパスが含まれているか
- VIRTUAL_ENV環境変数が設定されているか
- LANG, LC_ALLが設定されているか

### 2. 自動起動時の環境（サービスが実行中の場合）
- サービスプロセスのPIDを取得
- `/proc/$PID/environ`から環境変数を確認
- PATHに仮想環境のパスが含まれているか
- VIRTUAL_ENV環境変数が設定されているか

### 3. サービスログの確認
```bash
sudo journalctl -u attendance-client-fixed.service -n 100 --no-pager
```

ログに以下が表示されているか確認：
- "カードリーダーが見つかりません"
- "仮想環境を有効化中..."
- エラーメッセージ

## 実際の違いがあった場合

サービスファイルの環境変数設定を修正する必要があります。

## 実際の違いがなかった場合

別の原因を調査する必要があります：
- USBデバイスの認識タイミング
- PC/SCサービスの起動タイミング
- 権限の問題
- その他

