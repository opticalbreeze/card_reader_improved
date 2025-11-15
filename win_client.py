#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows版GUIクライアント（改善版）
- nfcpy + PCSC両対応
- PCスピーカー対応
- MACアドレスベースの端末ID自動取得
- サーバー監視機能
- 自動リトライ機能
"""

import time
import sys
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

# 共通モジュールをインポート
from common_utils import (
    get_mac_address,
    load_config,
    check_server_connection,
    send_attendance_to_server,
    get_pcsc_commands,
    is_valid_card_id
)
from constants import (
    DEFAULT_RETRY_INTERVAL,
    CARD_DUPLICATE_THRESHOLD,
    CARD_DETECTION_SLEEP,
    PCSC_POLL_INTERVAL,
    DB_PATH_CACHE,
    PENDING_DATA_MIN_AGE,
    RETRY_CHECK_INTERVAL,
    TIMEOUT_HEALTH_CHECK,
    TIMEOUT_SERVER_REQUEST,
    SERVER_CHECK_INTERVAL,
    PCSC_SUCCESS_SW1,
    PCSC_SUCCESS_SW2,
    INVALID_CARD_IDS
)

# nfcpy
try:
    import nfc
    NFCPY_AVAILABLE = True
except ImportError:
    NFCPY_AVAILABLE = False

# pyscard
try:
    from smartcard.System import readers as pcsc_readers
    from smartcard.Exceptions import CardConnectionException, NoCardException
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False

# PCスピーカー
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


# get_mac_address() は common_utils からインポート済み


# 音パターン（周波数Hz, 時間ms）
SOUNDS = {
    "startup": [(1000, 200), (1200, 100), (1000, 200)],      # 起動音
    "connect": [(1500, 100), (1500, 100), (1500, 100)],      # サーバー接続音
    "read": [(2000, 50)],                                     # カード読み取り音
    "success": [(2500, 100), (2700, 50), (2500, 100)],       # 送信成功音
    "fail": [(800, 300), (600, 100), (800, 300)]             # 送信失敗音
}


def beep(pattern, config=None):
    """
    PCスピーカーで音を鳴らす
    
    Args:
        pattern (str): 音パターン名（"startup", "read", "success", "fail"など）
        config (dict): 設定辞書（音の有効/無効を制御）
    """
    if not WINSOUND_AVAILABLE:
        return
    
    # 設定で音が無効化されている場合はスキップ
    if config:
        beep_settings = config.get('beep_settings', {})
        if not beep_settings.get('enabled', True):
            return
        # 個別の音設定をチェック
        if pattern == 'read' and not beep_settings.get('card_read', True):
            return
        if pattern == 'success' and not beep_settings.get('success', True):
            return
        if pattern == 'fail' and not beep_settings.get('fail', True):
            return
    
    for freq, duration in SOUNDS.get(pattern, [(1000, 100)]):
        try:
            winsound.Beep(freq, duration)
            time.sleep(0.05)
        except:
            pass


# get_pcsc_commands() は common_utils からインポート済み


# ============================================================================
# ローカルキャッシュクラス
# ============================================================================

class LocalCache:
    """
    ローカルキャッシュ管理（送信失敗時のデータ保存）
    SQLiteを使用して未送信データを保持し、定期的に再送信を試みる
    """
    
    def __init__(self, db_path=None):
        """
        Args:
            db_path (str): データベースファイルのパス（Noneの場合はデフォルト）
        """
        self.db_path = db_path or DB_PATH_CACHE
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化（テーブル作成）"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idm TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                terminal_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    
    def save_record(self, idm, timestamp, terminal_id):
        """
        レコードを保存
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
            terminal_id (str): 端末ID
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO pending_records (idm, timestamp, terminal_id, created_at) VALUES (?, ?, ?, ?)",
            (idm, timestamp, terminal_id, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    
    def get_pending_records(self):
        """
        未送信レコードを取得（10分以上経過したもの）
        
        Returns:
            list: (id, idm, timestamp, terminal_id, retry_count) のタプルのリスト
        """
        conn = sqlite3.connect(self.db_path)
        min_age_seconds = PENDING_DATA_MIN_AGE
        min_age_ago = (datetime.now() - timedelta(seconds=min_age_seconds)).isoformat()
        cursor = conn.execute(
            "SELECT id, idm, timestamp, terminal_id, retry_count FROM pending_records WHERE created_at <= ?",
            (min_age_ago,)
        )
        records = cursor.fetchall()
        conn.close()
        return records
    
    def delete_record(self, record_id):
        """
        送信成功したレコードを削除
        
        Args:
            record_id (int): レコードID
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM pending_records WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
    
    def increment_retry_count(self, record_id):
        """
        リトライカウントを増やす
        
        Args:
            record_id (int): レコードID
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE pending_records SET retry_count = retry_count + 1 WHERE id = ?",
            (record_id,)
        )
        conn.commit()
        conn.close()


# ============================================================================
# メインGUIクライアントクラス
# ============================================================================

class WindowsClientGUI:
    """
    Windows GUIクライアント
    ICカードリーダーからカードを読み取り、サーバーに送信する
    """
    
    def __init__(self, server_url, config=None):
        """
        Args:
            server_url (str): サーバーURL
            config (dict): 設定辞書
        """
        self.server = server_url
        self.terminal = get_mac_address()  # MACアドレスを端末IDとして使用
        self.cache = LocalCache()
        self.count = 0
        self.history = {}  # {card_id: last_seen_time}
        self.lock = threading.Lock()
        self.running = True
        self.server_connected = False
        self.config = config or {}
        # リトライ間隔（秒、デフォルト600秒=10分）
        self.retry_interval = self.config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
        # リーダー監視フラグ
        self.reader_threads = []
        self.reader_check_interval = 30  # リーダー再検出間隔（秒）
        self.active_readers = {}  # {reader_id: thread_info} - アクティブなリーダーの管理
        self.reader_lock = threading.Lock()  # リーダー管理用ロック
        
        # GUI作成
        self.root = tk.Tk()
        self.root.title("打刻システム - Windowsクライアント（改善版）")
        self.root.geometry("850x650")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.create_widgets()
        
        # 起動音
        beep("startup", self.config)
        
        # バックグラウンドスレッド開始
        threading.Thread(target=self.monitor_server, daemon=True).start()
        threading.Thread(target=self.monitor_readers, daemon=True).start()
        threading.Thread(target=self.retry_worker, daemon=True).start()
        threading.Thread(target=self.periodic_reader_check, daemon=True).start()
    
    def create_widgets(self):
        """GUIウィジェットを作成"""
        # タイトル
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(
            title_frame, 
            text="🔖 打刻システム - Windowsクライアント", 
            font=("", 14, "bold")
        ).pack()
        
        # ステータスフレーム
        status_frame = ttk.LabelFrame(self.root, text="ステータス", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 日時表示
        self.time_label = ttk.Label(status_frame, text="", font=("", 12))
        self.time_label.pack()
        
        # 端末ID表示
        terminal_frame = ttk.Frame(status_frame)
        terminal_frame.pack(fill=tk.X, pady=2)
        ttk.Label(terminal_frame, text="端末ID:").pack(side=tk.LEFT)
        ttk.Label(terminal_frame, text=self.terminal, font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)
        
        # サーバー状態
        server_frame = ttk.Frame(status_frame)
        server_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(server_frame, text="サーバー:").pack(side=tk.LEFT)
        self.server_label = ttk.Label(
            server_frame, 
            text="接続確認中...", 
            font=("", 10, "bold"), 
            foreground="orange"
        )
        self.server_label.pack(side=tk.LEFT, padx=5)
        
        # サーバーURL表示
        ttk.Label(server_frame, text=f"({self.server})", font=("", 8)).pack(side=tk.LEFT, padx=5)
        
        # リーダー状態
        reader_frame = ttk.Frame(status_frame)
        reader_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(reader_frame, text="リーダー:").pack(side=tk.LEFT)
        self.reader_label = ttk.Label(reader_frame, text="検出中...", font=("", 10))
        self.reader_label.pack(side=tk.LEFT, padx=5)
        
        # カウンター
        counter_frame = ttk.Frame(status_frame)
        counter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(counter_frame, text="読み取り数:").pack(side=tk.LEFT)
        self.counter_label = ttk.Label(
            counter_frame, 
            text="0 枚", 
            font=("", 10, "bold"), 
            foreground="blue"
        )
        self.counter_label.pack(side=tk.LEFT, padx=5)
        
        # メッセージエリア
        msg_frame = ttk.LabelFrame(self.root, text="メッセージ", padding="10")
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.message_label = ttk.Label(
            msg_frame, 
            text="カードをかざしてください", 
            font=("", 12, "bold"), 
            foreground="green"
        )
        self.message_label.pack()
        
        # ログエリア
        log_frame = ttk.LabelFrame(self.root, text="ログ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="設定", command=self.open_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="ログクリア", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="終了", command=self.on_close).pack(side=tk.RIGHT)
        
        # 時刻更新タイマー
        self.update_time()
        
        # 初期ログ
        self.log("="*70)
        self.log("打刻システム - Windowsクライアント（改善版）")
        self.log("="*70)
        self.log(f"サーバー: {self.server}")
        self.log(f"端末ID: {self.terminal}")
        self.log(f"nfcpy: {'利用可能' if NFCPY_AVAILABLE else '利用不可'}")
        self.log(f"pyscard: {'利用可能' if PYSCARD_AVAILABLE else '利用不可'}")
        self.log(f"PCスピーカー: {'利用可能' if WINSOUND_AVAILABLE else '利用不可'}")
        self.log("="*70)
    
    def update_time(self):
        """時刻表示を更新（1秒ごと）"""
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self.update_time)
    
    def log(self, message):
        """
        ログを出力
        
        Args:
            message (str): ログメッセージ
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """ログをクリア"""
        self.log_text.delete(1.0, tk.END)
        self.log("ログをクリアしました")
    
    def update_message(self, text, color="black", duration=0):
        """
        メッセージを更新
        
        Args:
            text (str): メッセージ
            color (str): 文字色
            duration (int): 表示時間（秒）。0の場合は自動で戻らない
        """
        self.message_label.config(text=text, foreground=color)
        
        if duration > 0:
            def reset():
                time.sleep(duration)
                self.message_label.config(text="カードをかざしてください", foreground="green")
            threading.Thread(target=reset, daemon=True).start()
    
    def open_config(self):
        """設定GUIを起動"""
        import subprocess
        try:
            subprocess.Popen([sys.executable, "client_config_gui.py"])
        except:
            self.log("[エラー] 設定GUIを起動できません")
    
    # ========================================================================
    # サーバー監視
    # ========================================================================
    
    def monitor_server(self):
        """
        サーバーの接続状態を定期的に監視
        再接続を試みて、状態をGUIに反映
        """
        retry_count = 0
        max_retries = 2
        
        while self.running:
            try:
                response = requests.get(f"{self.server}/api/health", timeout=TIMEOUT_HEALTH_CHECK)
                if response.status_code == 200:
                    self.server_connected = True
                    self.server_label.config(text="接続OK", foreground="green")
                    
                    if retry_count > 0:
                        self.log("[サーバー] 再接続成功")
                        beep("connect", self.config)
                    
                    retry_count = 0
                else:
                    self.server_connected = False
                    self.server_label.config(text="接続NG", foreground="red")
                    self.log(f"[サーバー] 応答異常: HTTP {response.status_code}")
            
            except requests.exceptions.ConnectionError:
                self.server_connected = False
                self.server_label.config(text="接続NG", foreground="red")
                
                if retry_count < max_retries:
                    retry_count += 1
                    self.log(f"[サーバー] 再接続試行 {retry_count}/{max_retries}")
                    time.sleep(5)
                    continue
                else:
                    if retry_count == max_retries:
                        self.log("[サーバー] 再接続失敗 - 1時間後に再試行")
                        retry_count += 1
            
            except Exception as e:
                self.server_connected = False
                self.server_label.config(text="接続NG", foreground="red")
                self.log(f"[サーバー] エラー: {e}")
            
            time.sleep(SERVER_CHECK_INTERVAL)
    
    # ========================================================================
    # リーダー監視
    # ========================================================================
    
    def periodic_reader_check(self):
        """
        定期的にリーダーの状態をチェック（スリープ復帰対応）
        リーダーが切断された場合は再検出を試みる
        """
        last_check_time = time.time()
        last_reader_count = 0
        
        while self.running:
            time.sleep(5)  # 5秒ごとにチェック
            
            # 設定された間隔が経過したら再検出
            if time.time() - last_check_time >= self.reader_check_interval:
                last_check_time = time.time()
                
                # 現在のリーダー数をカウント
                nfcpy_count = 0
                pcsc_count = 0
                detected_nfcpy_paths = []
                detected_pcsc_readers = []
                
                # nfcpy検出（AI_TROUBLESHOOTING_GUIDEの推奨方法）
                if NFCPY_AVAILABLE:
                    try:
                        clf = nfc.ContactlessFrontend('usb')
                        if clf:
                            nfcpy_count = 1
                            detected_nfcpy_paths.append(('usb', 1))
                            clf.close()
                    except:
                        pass
                
                # PC/SC検出
                if PYSCARD_AVAILABLE:
                    try:
                        reader_list = pcsc_readers()
                        pcsc_count = len(reader_list)
                        detected_pcsc_readers = [(reader, nfcpy_count + i + 1) for i, reader in enumerate(reader_list)]
                    except:
                        pass
                
                total_readers = nfcpy_count + pcsc_count
                
                # リーダー数が変化した場合（切断または再接続）
                if total_readers != last_reader_count:
                    if total_readers == 0:
                        self.log("[警告] カードリーダーが切断されました - 再接続を待機中")
                        self.reader_label.config(text="リーダー切断", foreground="red")
                        # アクティブなリーダースレッドをクリア
                        with self.reader_lock:
                            self.active_readers.clear()
                    elif total_readers > last_reader_count:
                        # リーダーが再接続された - 再起動
                        self.log(f"[復帰] カードリーダーを検出しました ({total_readers}台) - 監視を再開します")
                        self.reader_label.config(text=f"{total_readers}台検出", foreground="green")
                        # リーダー監視を再起動
                        self.restart_reader_monitoring(detected_nfcpy_paths, detected_pcsc_readers)
                    else:
                        # リーダー数が減った（一部切断）
                        self.log(f"[警告] リーダー数が減少しました ({total_readers}台)")
                        self.reader_label.config(text=f"{total_readers}台検出", foreground="orange")
                        # リーダー監視を再起動
                        self.restart_reader_monitoring(detected_nfcpy_paths, detected_pcsc_readers)
                    
                    last_reader_count = total_readers
    
    def restart_reader_monitoring(self, nfcpy_paths, pcsc_readers):
        """
        リーダー監視を再起動（スリープ復帰対応）
        
        Args:
            nfcpy_paths: [(path, idx), ...] - 検出されたnfcpyリーダーのリスト
            pcsc_readers: [(reader, idx), ...] - 検出されたPC/SCリーダーのリスト
        """
        # 既存のリーダースレッドを停止（実際にはdaemonスレッドなので自然終了を待つ）
        with self.reader_lock:
            self.active_readers.clear()
        
        # nfcpy リーダーの監視開始
        for path, idx in nfcpy_paths:
            reader_id = f"nfcpy_{idx}"
            thread = threading.Thread(
                target=self.nfcpy_worker, 
                args=(path, idx), 
                daemon=True
            )
            thread.start()
            with self.reader_lock:
                self.active_readers[reader_id] = {'thread': thread, 'type': 'nfcpy', 'path': path, 'idx': idx}
            self.log(f"[再起動] nfcpyリーダー #{idx} の監視を開始")
        
        # PC/SC リーダーの監視開始
        for reader, idx in pcsc_readers:
            reader_id = f"pcsc_{idx}"
            thread = threading.Thread(
                target=self.pcsc_worker,
                args=(reader, str(reader), idx),
                daemon=True
            )
            thread.start()
            with self.reader_lock:
                self.active_readers[reader_id] = {'thread': thread, 'type': 'pcsc', 'reader': reader, 'idx': idx}
            self.log(f"[再起動] PC/SCリーダー #{idx}: {str(reader)[:40]}")
    
    def monitor_readers(self):
        """
        利用可能なカードリーダーを検出し、各リーダーの監視スレッドを起動
        """
        nfcpy_count = 0
        pcsc_count = 0
        detected_nfcpy_paths = []
        detected_pcsc_readers = []
        
        # nfcpy検出（AI_TROUBLESHOOTING_GUIDEの推奨方法）
        if NFCPY_AVAILABLE:
            try:
                # 'usb' だけを指定すれば自動的にリーダーを見つける
                clf = nfc.ContactlessFrontend('usb')
                if clf:
                    nfcpy_count = 1
                    detected_nfcpy_paths.append(('usb', 1))
                    self.log(f"[検出] nfcpyリーダー: {clf}")
                    clf.close()
            except Exception as e:
                self.log(f"[情報] nfcpyリーダー未検出: {e}")
        
        # PC/SC検出
        if PYSCARD_AVAILABLE:
            try:
                reader_list = pcsc_readers()
                pcsc_count = len(reader_list)
                detected_pcsc_readers = [(reader, nfcpy_count + i + 1) for i, reader in enumerate(reader_list)]
            except:
                pass
        
        # リーダーが見つからない場合
        if nfcpy_count == 0 and pcsc_count == 0:
            self.log("[エラー] カードリーダーが見つかりません")
            self.log("[ヒント] リーダーを接続してプログラムを再起動してください")
            self.reader_label.config(text="リーダーなし", foreground="red")
            return
        
        # リーダー検出成功
        self.log(f"[検出] nfcpy:{nfcpy_count}台 / PC/SC:{pcsc_count}台")
        self.reader_label.config(text=f"{nfcpy_count+pcsc_count}台検出", foreground="green")
        
        # リーダー監視を開始
        self.restart_reader_monitoring(detected_nfcpy_paths, detected_pcsc_readers)
        
        self.log("[起動] 全リーダーの監視を開始しました")
    
    def nfcpy_worker(self, path, idx):
        """
        nfcpy用リーダー監視ワーカー
        
        Args:
            path (str): nfcpyデバイスパス（例: 'usb:000'）
            idx (int): リーダー番号
        """
        last_id = None
        last_time = 0
        clf = None
        
        try:
            # ContactlessFrontendを1回だけ開く（再利用することで高速化）
            clf = nfc.ContactlessFrontend(path)
            if not clf:
                self.log(f"[エラー] nfcpyリーダー#{idx}を開けません")
                return
            
            consecutive_errors = 0
            max_consecutive_errors = 10  # 連続エラーが10回続いたら再初期化
            
            while self.running:
                try:
                    # カード検出（短いタイムアウトで高速化: 0.5秒）
                    tag = clf.connect(rdwr={
                        'on-connect': lambda tag: False,
                        'beep-on-connect': False
                    }, terminate=lambda: not self.running)
                    
                    if tag:
                        # IDmを取得（AI_TROUBLESHOOTING_GUIDEの推奨方法）
                        try:
                            if hasattr(tag, 'idm'):
                                card_id = tag.idm.hex().upper()
                            elif hasattr(tag, '_nfcid'):
                                card_id = tag._nfcid.hex().upper()
                            elif hasattr(tag, 'identifier'):
                                card_id = tag.identifier.hex().upper()
                            else:
                                card_id = None
                        except:
                            card_id = None
                        
                        if card_id and card_id != last_id:
                            self.process_card(card_id, idx)
                            last_id = card_id
                            last_time = time.time()
                        
                        consecutive_errors = 0  # 成功したらエラーカウントをリセット
                    
                except IOError:
                    # カードなし - 正常な状態
                    consecutive_errors = 0
                    pass
                except Exception as e:
                    # エラーが発生した場合
                    consecutive_errors += 1
                    
                    # 連続エラーが一定回数に達した場合、リーダーが切断された可能性がある
                    if consecutive_errors >= max_consecutive_errors:
                        self.log(f"[警告] nfcpyリーダー#{idx}で連続エラー - リーダーが切断された可能性があります")
                        # ContactlessFrontendを閉じて再初期化を試みる
                        try:
                            clf.close()
                        except:
                            pass
                        clf = None
                        
                        # 再初期化を試みる（最大3回）
                        for retry in range(3):
                            try:
                                time.sleep(1)  # 1秒待機してから再試行
                                clf = nfc.ContactlessFrontend(path)
                                if clf:
                                    self.log(f"[復帰] nfcpyリーダー#{idx}を再初期化しました")
                                    consecutive_errors = 0
                                    break
                            except:
                                if retry < 2:
                                    time.sleep(1)
                                else:
                                    # 再初期化に失敗した場合、このワーカーを終了
                                    self.log(f"[エラー] nfcpyリーダー#{idx}の再初期化に失敗しました")
                                    return
                
                # カードが離れた判定（2秒以上検出なし）
                if last_time > 0 and time.time() - last_time > 2:
                    last_id = None
                
                # 短いスリープで応答性を向上
                time.sleep(CARD_DETECTION_SLEEP)
        
        finally:
            # 終了時にContactlessFrontendをクローズ
            if clf:
                try:
                    clf.close()
                except:
                    pass
    
    def pcsc_worker(self, reader, reader_name, idx):
        """
        PC/SC用リーダー監視ワーカー
        
        Args:
            reader: smartcard.Readerオブジェクト
            reader_name (str): リーダー名
            idx (int): リーダー番号
        """
        last_id = None
        last_time = 0
        consecutive_errors = 0
        max_consecutive_errors = 10  # 連続エラーが10回続いたら再取得
        
        while self.running:
            try:
                # スリープ復帰時にreaderオブジェクトが無効になる可能性があるため、毎回取得
                try:
                    current_readers = pcsc_readers()
                    # 現在のリーダー名に一致するリーダーを探す
                    current_reader = None
                    for r in current_readers:
                        if str(r) == reader_name:
                            current_reader = r
                            break
                    
                    if not current_reader:
                        # リーダーが見つからない場合
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            self.log(f"[警告] PC/SCリーダー#{idx} ({reader_name[:40]}) が見つかりません - 切断された可能性があります")
                            # リーダーを再取得して試みる
                            time.sleep(2)
                            try:
                                current_readers = pcsc_readers()
                                for r in current_readers:
                                    if str(r) == reader_name or reader_name in str(r):
                                        current_reader = r
                                        self.log(f"[復帰] PC/SCリーダー#{idx}を再検出しました")
                                        consecutive_errors = 0
                                        break
                            except:
                                pass
                        
                        if not current_reader:
                            time.sleep(1)
                            continue
                    else:
                        consecutive_errors = 0  # リーダーが見つかったらエラーカウントをリセット
                        reader = current_reader  # 最新のreaderオブジェクトを使用
                    
                except Exception as e:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.log(f"[警告] PC/SCリーダー#{idx}の検出エラー: {e}")
                    time.sleep(1)
                    continue
                
                connection = reader.createConnection()
                connection.connect()
                
                # 複数のコマンドを試してカードIDを取得
                card_id = None
                commands = get_pcsc_commands(reader_name)
                
                for cmd in commands:
                    try:
                        response, sw1, sw2 = connection.transmit(cmd)
                        
                        # 成功応答かつ有効なデータがある場合
                        if sw1 == PCSC_SUCCESS_SW1 and sw2 == PCSC_SUCCESS_SW2 and len(response) >= 4:
                            uid_len = min(len(response), 16)
                            card_id = ''.join([f'{b:02X}' for b in response[:uid_len]])
                            
                            # 無効なIDをフィルタリング
                            if is_valid_card_id(card_id):
                                break
                    except Exception:
                        continue
                
                if card_id and card_id != last_id:
                    self.process_card(card_id, idx)
                    last_id = card_id
                    last_time = time.time()
                    consecutive_errors = 0  # 成功したらエラーカウントをリセット
                
                connection.disconnect()
                
            except (CardConnectionException, NoCardException):
                # カードなし、接続エラーは正常な状態
                consecutive_errors = 0
                pass
            except Exception as e:
                # その他のエラー
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    self.log(f"[警告] PC/SCリーダー#{idx}で連続エラー: {e}")
                pass
            
            # カードが離れた判定（2秒以上検出なし）
            if time.time() - last_time > 2:
                last_id = None
            
            time.sleep(PCSC_POLL_INTERVAL)
    
    # ========================================================================
    # カード処理
    # ========================================================================
    
    def process_card(self, card_id, reader_idx):
        """
        カードを処理（サーバー送信またはローカル保存）
        
        Args:
            card_id (str): カードID
            reader_idx (int): リーダー番号
        """
        with self.lock:
            now = time.time()
            
            # 重複チェック
            if card_id in self.history and now - self.history[card_id] < CARD_DUPLICATE_THRESHOLD:
                return
            
            self.history[card_id] = now
            self.count += 1
            
            # GUI更新
            self.counter_label.config(text=f"{self.count} 枚")
            self.update_message("カードを読み取りました", "blue", 2)
            
            # ログ出力
            self.log(f"[カード#{self.count}] IDm: {card_id} (リーダー{reader_idx})")
            
            # 読み取り音（ハードウェアブザー付きリーダーの場合は無効化推奨）
            beep("read", self.config)
            
            # サーバー送信
            ts = datetime.now().isoformat()
            
            try:
                # 共通のサーバー送信関数を使用
                success, error_msg = send_attendance_to_server(
                    card_id, ts, self.terminal, self.server
                )
                
                if success:
                    self.log(f"[送信成功] サーバーに記録")
                    self.update_message("サーバーに記録しました", "green", 2)
                    beep("success", self.config)
                else:
                    self.log(f"[送信失敗] {error_msg} - ローカルに保存")
                    self.cache.save_record(card_id, ts, self.terminal)
                    self.update_message("ローカルに保存しました", "orange", 2)
                    beep("fail", self.config)
            
            except Exception as e:
                self.log(f"[送信失敗] エラー: {e} - ローカルに保存")
                self.cache.save_record(card_id, ts, self.terminal)
                self.update_message("ローカルに保存しました", "orange", 2)
                beep("fail", self.config)
    
    # ========================================================================
    # リトライワーカー
    # ========================================================================
    
    def retry_worker(self):
        """
        設定された間隔で未送信レコードを再送信
        GUIで設定したリトライ間隔の変更に対応
        """
        last_retry_time = 0
        
        while self.running:
            # リトライ間隔の変更に対応するため、短い間隔でチェック
            time.sleep(RETRY_CHECK_INTERVAL)
            
            current_time = time.time()
            elapsed = current_time - last_retry_time
            
            # 設定されたリトライ間隔が経過したらリトライ実行
            if elapsed >= self.retry_interval:
                last_retry_time = current_time
                
                records = self.cache.get_pending_records()
                if records:
                    self.log(f"[リトライ] {len(records)}件の未送信データを再送信します（間隔: {self.retry_interval}秒）")
                    
                    for record_id, idm, timestamp, terminal_id, retry_count in records:
                        try:
                            data = {
                                'idm': idm,
                                'timestamp': timestamp,
                                'terminal_id': terminal_id
                            }
                            
                            response = requests.post(
                                f"{self.server}/api/attendance",
                                json=data,
                                timeout=TIMEOUT_SERVER_REQUEST
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('status') == 'success':
                                    self.cache.delete_record(record_id)
                                    self.log(f"[リトライ成功] IDm: {idm} (試行回数: {retry_count + 1})")
                                else:
                                    # 重複データの場合も成功として扱う
                                    message = result.get('message', '').lower()
                                    if '重複' in message or 'duplicate' in message or '既に' in message:
                                        self.cache.delete_record(record_id)
                                        self.log(f"[リトライ成功（重複）] IDm: {idm} - {result.get('message')}")
                                    else:
                                        self.cache.increment_retry_count(record_id)
                                        self.log(f"[リトライ失敗] IDm: {idm} - {result.get('message')} (試行回数: {retry_count + 1})")
                            else:
                                self.cache.increment_retry_count(record_id)
                                self.log(f"[リトライ失敗] IDm: {idm} HTTP {response.status_code} (試行回数: {retry_count + 1})")
                        
                        except Exception as e:
                            self.cache.increment_retry_count(record_id)
                            self.log(f"[リトライ失敗] IDm: {idm} - {e}")
    
    # ========================================================================
    # 終了処理
    # ========================================================================
    
    def on_close(self):
        """アプリケーション終了処理"""
        self.running = False
        self.log("プログラムを終了します...")
        self.log(f"総読み取り数: {self.count} 枚")
        self.log(f"ユニークカード数: {len(self.history)} 枚")
        time.sleep(0.5)
        self.root.destroy()
    
    def run(self):
        """GUIメインループを開始"""
        self.root.mainloop()


# ============================================================================
# 設定ファイル管理
# ============================================================================

# load_config() は common_utils からインポート済み


# ============================================================================
# エントリーポイント
# ============================================================================

def main():
    """メイン関数"""
    print("="*70)
    print("打刻システム - Windowsクライアント（改善版）")
    print("="*70)
    
    # 必須ライブラリチェック
    if not NFCPY_AVAILABLE and not PYSCARD_AVAILABLE:
        print("[エラー] nfcpy または pyscard のいずれかが必要です")
        print("  pip install nfcpy")
        print("  または")
        print("  pip install pyscard")
        sys.exit(1)
    
    # 設定読み込み
    config = load_config()
    server_url = config.get('server_url', 'http://192.168.1.31:5000')
    
    print(f"サーバーURL: {server_url}")
    print(f"端末ID: {get_mac_address()}")
    print("="*70)
    print()
    
    # GUIクライアント起動
    try:
        client = WindowsClientGUI(server_url, config)
        client.run()
    except KeyboardInterrupt:
        print("\n[終了] プログラムを終了します")
    except Exception as e:
        print(f"[エラー] 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

