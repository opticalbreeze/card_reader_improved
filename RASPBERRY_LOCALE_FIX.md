# ラズパイのロケール設定をUTF-8に修正する方法

## 問題

ラズパイ側のロケールが`ja_JP.EUC-JP`に設定されているため、UTF-8の文字が正しく表示されません。

## 解決方法

### 方法1: スクリプトを使用（推奨）

```bash
cd ~/Desktop/attendance/card_reader_improved
chmod +x fix_raspberry_locale.sh
./fix_raspberry_locale.sh
```

### 方法2: 手動で設定

#### 現在のセッションのみ（一時的）

```bash
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
```

#### 永続的に設定（~/.bashrcに追加）

```bash
# ~/.bashrcに追加
echo 'export LANG=ja_JP.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=ja_JP.UTF-8' >> ~/.bashrc
echo 'export PYTHONIOENCODING=utf-8' >> ~/.bashrc
echo 'export PYTHONUTF8=1' >> ~/.bashrc

# 設定を読み込み
source ~/.bashrc
```

#### システム全体に設定（オプション）

```bash
# 日本語UTF-8ロケールを生成（まだない場合）
sudo locale-gen ja_JP.UTF-8

# システム全体のロケールを設定
sudo update-locale LANG=ja_JP.UTF-8
sudo update-locale LC_ALL=ja_JP.UTF-8

# 再起動またはログアウト/ログインが必要
```

## 確認

```bash
# 現在のロケール設定を確認
locale

# 利用可能なUTF-8ロケールを確認
locale -a | grep -i utf
```

## 期待される結果

設定後、`locale`コマンドの出力は以下のようになります：

```
LANG=ja_JP.UTF-8
LC_ALL=ja_JP.UTF-8
...
```

## 注意事項

- システム全体の設定を変更する場合は、再起動またはログアウト/ログインが必要です
- `~/.bashrc`の設定は新しいターミナルセッションで有効になります
- 現在のセッションに即座に反映するには、`source ~/.bashrc`を実行してください

