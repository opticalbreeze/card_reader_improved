# pcscdグループが存在しない場合の対処法

## 問題

`usermod: group 'pcscd' does not exist` というエラーが発生

## 解決方法

### 方法1: スクリプトを使用（推奨）

```bash
cd ~/Desktop/attendance/card_reader_improved
chmod +x create_pcscd_group.sh
./create_pcscd_group.sh
```

### 方法2: 手動で実行

```bash
# 1. pcscdグループを作成
sudo groupadd pcscd

# 2. ユーザーをグループに追加
sudo usermod -a -G pcscd raspberry

# 3. 確認
groups | grep pcscd
```

### 方法3: グループを作成せずにサービスファイルを修正

サービスファイルで`Group=pcscd`を削除し、別の方法で権限を設定する

## 確認

```bash
# グループが作成されたか確認
getent group pcscd

# ユーザーがグループに属しているか確認（ログアウト/ログイン後）
groups | grep pcscd
```

## 注意事項

- グループへの追加後、ログアウト/ログインが必要です
- または、新しいターミナルセッションを開始してください

