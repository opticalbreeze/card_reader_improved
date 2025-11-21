# メモリモニタリングガイド

## 📊 概要

このシステムには、メモリリーク検出のためのメモリモニタリング機能が組み込まれています。

## 🚀 使用方法

### 1. メモリモニタリングを有効化

`client_config.json` を編集:

```json
{
  "server_url": "http://192.168.1.31:5000",
  "memory_monitor": {
    "enabled": true,
    "interval": 300,
    "tracemalloc": false
  }
}
```

**設定項目:**
- `enabled`: メモリモニタリングを有効化 (true/false)
- `interval`: モニタリング間隔（秒）- デフォルト300秒（5分）
- `tracemalloc`: 詳細なメモリトレース（遅くなる可能性あり）(true/false)

### 2. クライアントを起動

```bash
cd /home/raspberry/Desktop/attendance/card_reader_improved
source venv/bin/activate
python pi_client.py
```

または

```bash
bash start_pi.sh
```

### 3. ログファイルの確認

メモリ使用量は `memory_usage.log` に記録されます:

```bash
tail -f memory_usage.log
```

## 📈 ログの見方

### 通常のログエントリ

```
[2025-11-21 14:30:00] 経過: 00:05:00 | RSS: 45.23MB (初期比: +2.15MB) | VMS: 123.45MB | ピーク: 47.12MB | システム: 35.2% (512MB空き)
```

**各項目の説明:**
- `経過`: プログラム開始からの経過時間
- `RSS`: 実際に使用している物理メモリ
- `初期比`: 起動時からのメモリ増加量
- `VMS`: 仮想メモリサイズ
- `ピーク`: これまでの最大メモリ使用量
- `システム`: システム全体のメモリ使用率と空きメモリ

### 警告メッセージ

メモリが50MB以上増加すると警告が出ます:

```
⚠️ [警告] メモリが初期値から 52.34MB 増加しています
```

### tracemalloc情報（有効化時）

10回ごとに詳細なメモリトレース情報が記録されます:

```
  [tracemalloc] Current: 38.45MB, Peak: 42.12MB
  [Top 10 メモリ消費箇所]
    /path/to/file.py:123: size=5.2 MiB, count=1234, average=4.3 KiB
    ...
```

## 🔍 メモリリークの診断

### 正常なパターン

- 起動時にメモリが増加し、その後安定
- 初期比が±10MB以内で推移

### 異常なパターン（メモリリーク）

- 時間経過とともに継続的にメモリが増加
- 初期比が50MB以上増加
- 数時間後にプログラムがクラッシュ

### 対処方法

1. **ログを確認**
   ```bash
   grep "警告" memory_usage.log
   ```

2. **tracemalloc有効化して詳細調査**
   ```json
   {
     "memory_monitor": {
       "enabled": true,
       "interval": 60,
       "tracemalloc": true
     }
   }
   ```

3. **ログを開発者に送付**
   - `memory_usage.log` をメールまたはGitHubのissueに添付

## 🧪 テストモード

メモリモニター単体でテスト:

```bash
python memory_monitor.py test
```

これにより、メモリを徐々に消費しながら5分間モニタリングを行います。

## 📊 ログの分析

### グラフ化（推奨）

ログファイルをExcelやLibreOffice Calcにインポートしてグラフ化:

1. `memory_usage.log` を開く
2. RSSやVMSの値を抽出
3. 時系列グラフを作成

### コマンドラインで確認

```bash
# メモリ増加のトレンドを確認
grep "初期比" memory_usage.log | tail -20

# 警告を確認
grep "警告" memory_usage.log

# 最大メモリ使用量を確認
grep "ピーク" memory_usage.log | tail -1
```

## ⚙️ パフォーマンスへの影響

- **interval=300（5分）**: ほぼ影響なし
- **interval=60（1分）**: 軽微な影響
- **tracemalloc有効**: 5-10%のパフォーマンス低下

**推奨設定:**
- 通常運用: `enabled: false`
- 問題調査時: `enabled: true, interval: 300, tracemalloc: false`
- 詳細調査時: `enabled: true, interval: 60, tracemalloc: true`

## 📝 注意事項

- メモリモニタリングを有効化すると、わずかにメモリとCPUを消費します
- `tracemalloc`を有効化すると、プログラムが遅くなる可能性があります
- ログファイルは自動的に上書きされます（バックアップ推奨）

## 🐛 既知のメモリリーク原因

### 1. カード読み取りループでのオブジェクト蓄積

**症状**: カードを読み取るたびにメモリが増加

**対策**: 
- カード読み取り後に明示的にオブジェクトを削除
- ガベージコレクションを定期実行

### 2. スレッドの未解放

**症状**: スレッドが終了せずに溜まる

**対策**:
- `daemon=True` を設定
- スレッドの適切な終了処理

### 3. データベース接続のリーク

**症状**: DB接続がクローズされない

**対策**:
- `with` 文を使用
- 明示的に `conn.close()`

## 📞 サポート

問題が解決しない場合:

1. `memory_usage.log` を保存
2. GitHubのissueに報告: https://github.com/opticalbreeze/card_reader_improved/issues
3. ログファイルを添付

---

**最終更新**: 2025-11-21
