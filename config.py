#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
クライアント設定GUI - サーバーIP設定
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import subprocess
import sys
import sqlite3

# 共通モジュールをインポート
from common_utils import load_config, save_config, send_attendance_to_server
from constants import DEFAULT_SERVER_URL, CONFIG_FILE, DB_PATH_ATTENDANCE


class ConfigGUI:
    """設定GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("打刻システム - クライアント設定")
        self.root.geometry("600x650")
        self.root.resizable(True, True)
        
        # ウィンドウを閉じた時の動作を設定（起動後は閉じてもOK）
        self.client_started = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # ウィンドウを中央に配置
        self.center_window()
        
        self.config_file = "client_config.json"
        self.config = self.load_config()
        
        self.create_widgets()
    
    def center_window(self):
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_config(self):
        """設定ファイルを読み込み"""
        return load_config(self.config_file)
    
    def save_config(self):
        """設定ファイルを保存"""
        if save_config(self.config, self.config_file):
            return True
        else:
            messagebox.showerror("エラー", "設定の保存に失敗しました")
            return False
    
    def create_widgets(self):
        """ウィジェット作成"""
        # スクロール可能なキャンバスとフレームの作成
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # マウスホイールでスクロール
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # メインフレーム
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # キャンバスとスクロールバーの配置
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # タイトル
        title_label = ttk.Label(
            main_frame, 
            text="[打刻システム - クライアント設定]",
            font=("", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 現在の設定表示
        current_frame = ttk.LabelFrame(main_frame, text="現在の設定", padding="10")
        current_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        current_url = self.config.get('server_url', DEFAULT_SERVER_URL)
        ttk.Label(current_frame, text="現在のサーバーURL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.current_url_label = ttk.Label(
            current_frame, 
            text=current_url,
            foreground="blue",
            font=("", 10, "bold")
        )
        self.current_url_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # サーバー設定
        url_frame = ttk.LabelFrame(main_frame, text="サーバー設定", padding="10")
        url_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # IPアドレス設定
        ttk.Label(url_frame, text="サーバーIPアドレス:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ip_entry = ttk.Entry(url_frame, width=20)
        self.ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # ポート設定
        ttk.Label(url_frame, text="ポート番号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_entry = ttk.Entry(url_frame, width=20)
        self.port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # プリセットボタン
        preset_frame = ttk.Frame(url_frame)
        preset_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Label(preset_frame, text="よく使われるIP:").grid(row=0, column=0, sticky=tk.W)
        
        # プリセットIPは設定ファイルから読み込むか、デフォルト値を使用
        preset_buttons = [
            ("192.168.1.24", "192.168.1.24"),
            ("192.168.1.31", "192.168.1.31"),
            ("192.168.11.24", "192.168.11.24"),
            ("localhost", "127.0.0.1")
        ]
        
        for i, (text, ip) in enumerate(preset_buttons):
            btn = ttk.Button(
                preset_frame,
                text=text,
                command=lambda ip=ip: self.set_preset_ip(ip),
                width=12
            )
            btn.grid(row=0, column=i+1, padx=2)
        
        # 現在の設定を表示
        if '://' in current_url:
            current_url = current_url.split('://', 1)[1]
        if ':' in current_url:
            ip, port = current_url.split(':', 1)
            self.ip_entry.insert(0, ip)
            self.port_entry.insert(0, port)
        else:
            self.ip_entry.insert(0, current_url)
            self.port_entry.insert(0, "5000")
        
        # プレビュー
        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(preview_frame, text="新しいURL:").grid(row=0, column=0, sticky=tk.W)
        self.url_preview = ttk.Label(
            preview_frame, 
            text=self.config.get('server_url', ''),
            foreground="green",
            font=("", 10, "bold")
        )
        self.url_preview.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 入力変更時にプレビューを更新
        self.ip_entry.bind('<KeyRelease>', self.update_preview)
        self.port_entry.bind('<KeyRelease>', self.update_preview)
        
        # LCD設定
        lcd_frame = ttk.LabelFrame(main_frame, text="LCD設定", padding="10")
        lcd_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        lcd_settings = self.config.get('lcd_settings', {})
        
        # I2Cアドレス設定
        ttk.Label(lcd_frame, text="I2Cアドレス:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.lcd_addr_var = tk.StringVar(value=f"0x{lcd_settings.get('i2c_addr', 0x27):02X}")
        lcd_addr_entry = ttk.Entry(lcd_frame, textvariable=self.lcd_addr_var, width=10)
        lcd_addr_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(lcd_frame, text="(0x27 または 0x3F)", font=("", 8)).grid(row=0, column=2, sticky=tk.W)
        
        # I2Cバス番号設定
        ttk.Label(lcd_frame, text="I2Cバス番号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.lcd_bus_var = tk.IntVar(value=lcd_settings.get('i2c_bus', 1))
        lcd_bus_spinbox = ttk.Spinbox(lcd_frame, from_=0, to=1, textvariable=self.lcd_bus_var, width=10)
        lcd_bus_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(lcd_frame, text="(Raspberry Pi 3/4は1、初期モデルは0)", font=("", 8)).grid(row=1, column=2, sticky=tk.W)
        
        # バックライト設定
        self.lcd_backlight_var = tk.BooleanVar(value=lcd_settings.get('backlight', True))
        lcd_backlight_check = ttk.Checkbutton(
            lcd_frame,
            text="バックライトON",
            variable=self.lcd_backlight_var
        )
        lcd_backlight_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 接続テストボタン
        test_button = ttk.Button(
            main_frame,
            text="[接続テスト]",
            command=self.test_connection
        )
        test_button.grid(row=5, column=0, columnspan=3, pady=10)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        save_button = ttk.Button(
            button_frame,
            text="[保存]",
            command=self.save_and_close,
            width=15
        )
        save_button.grid(row=0, column=0, padx=5)
        
        start_button = ttk.Button(
            button_frame,
            text="[保存して起動]",
            command=self.save_and_start,
            width=15
        )
        start_button.grid(row=0, column=1, padx=5)
        
        cancel_button = ttk.Button(
            button_frame,
            text="[キャンセル]",
            command=self.on_closing,
            width=15
        )
        cancel_button.grid(row=0, column=2, padx=5)
        
        # ステータスバー
        self.status_label = ttk.Label(
            main_frame,
            text="設定を編集してください",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def set_preset_ip(self, ip):
        """プリセットIPを設定"""
        self.ip_entry.delete(0, tk.END)
        self.ip_entry.insert(0, ip)
        self.update_preview()
        self.status_label.config(text=f"IPアドレスを {ip} に設定しました")
    
    def update_preview(self, event=None):
        """URLプレビューを更新"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if ip and port:
            url = f"http://{ip}:{port}"
            self.url_preview.config(text=url)
        else:
            self.url_preview.config(text="")
    
    def test_connection(self):
        """サーバーへの接続をテスト"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showwarning("警告", "IPアドレスとポートを入力してください")
            return
        
        url = f"http://{ip}:{port}"
        self.status_label.config(text="接続テスト中...")
        self.root.update()
        
        try:
            import requests
            response = requests.get(f"{url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                messagebox.showinfo("成功", f"サーバーに接続できました！\n\nURL: {url}\nメッセージ: {data.get('message')}\n時刻: {data.get('timestamp')}")
                self.status_label.config(text="[OK] 接続成功")
            else:
                messagebox.showwarning("警告", f"サーバーが応答しましたが、ステータスが異常です:\nHTTPステータス: {response.status_code}\nURL: {url}")
                self.status_label.config(text="[WARNING] 異常な応答")
        except ImportError:
            messagebox.showerror("エラー", "requestsモジュールがインストールされていません。\npip install requests を実行してください。")
            self.status_label.config(text="[ERROR] requests未インストール")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("エラー", f"サーバーに接続できません:\n{url}\n\n【確認事項】\n・サーバーが起動しているか\n・IPアドレスが正しいか\n・ファイアウォールの設定")
            self.status_label.config(text="[NG] 接続失敗")
        except requests.exceptions.Timeout:
            messagebox.showerror("エラー", f"接続がタイムアウトしました:\n{url}\n\n【確認事項】\n・ネットワークの接続\n・サーバーの負荷状況")
            self.status_label.config(text="[NG] タイムアウト")
        except Exception as e:
            messagebox.showerror("エラー", f"予期しないエラーが発生しました:\n{url}\n\nエラー: {e}")
            self.status_label.config(text="[NG] エラー発生")
    
    def send_pending_data(self, server_url):
        """
        未送信データをサーバーに送信
        
        Args:
            server_url (str): サーバーURL
        
        Returns:
            tuple: (成功件数, 失敗件数, 総件数)
        """
        db_path = DB_PATH_ATTENDANCE
        if not Path(db_path).exists():
            return (0, 0, 0)
        
        try:
            # 未送信データを取得
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # カラムの存在確認
            cursor.execute("PRAGMA table_info(attendance)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sent_to_server' not in columns:
                # 未送信フラグがない場合はスキップ
                conn.close()
                return (0, 0, 0)
            
            cursor.execute("""
                SELECT id, idm, timestamp, terminal_id
                FROM attendance
                WHERE sent_to_server = 0
                ORDER BY timestamp ASC
                LIMIT 100
            """)
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return (0, 0, 0)
            
            # サーバーに送信
            import requests
            success_count = 0
            fail_count = 0
            
            for record in records:
                record_id, idm, timestamp, terminal_id = record
                
                try:
                    # 共通のサーバー送信関数を使用
                    success, error_msg = send_attendance_to_server(
                        idm, timestamp, terminal_id, server_url
                    )
                    
                    if success:
                        # 送信済みとしてマーク
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE attendance
                            SET sent_to_server = 1
                            WHERE id = ?
                        """, (record_id,))
                        conn.commit()
                        conn.close()
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception:
                    fail_count += 1
            
            return (success_count, fail_count, len(records))
            
        except Exception as e:
            print(f"未送信データ送信エラー: {e}")
            return (0, 0, 0)
    
    def save_and_close(self):
        """設定を保存して閉じる"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showwarning("警告", "IPアドレスとポートを入力してください")
            return
        
        self.config['server_url'] = f"http://{ip}:{port}"
        
        # LCD設定を保存
        try:
            lcd_addr_str = self.lcd_addr_var.get().strip()
            lcd_addr = int(lcd_addr_str, 16) if lcd_addr_str.startswith('0x') else int(lcd_addr_str)
            self.config['lcd_settings'] = {
                'i2c_addr': lcd_addr,
                'i2c_bus': self.lcd_bus_var.get(),
                'backlight': self.lcd_backlight_var.get()
            }
        except ValueError:
            messagebox.showwarning("警告", "LCD I2Cアドレスが正しくありません")
            return
        
        if self.save_config():
            # 現在の設定表示を更新
            self.current_url_label.config(text=self.config['server_url'])
            messagebox.showinfo("成功", f"設定を保存しました\n\n新しいサーバーURL:\n{self.config['server_url']}")
            self.root.destroy()
    
    def save_and_start(self):
        """設定を保存してクライアントを起動"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showwarning("警告", "IPアドレスとポートを入力してください")
            return
        
        self.config['server_url'] = f"http://{ip}:{port}"
        
        # LCD設定を保存
        try:
            lcd_addr_str = self.lcd_addr_var.get().strip()
            lcd_addr = int(lcd_addr_str, 16) if lcd_addr_str.startswith('0x') else int(lcd_addr_str)
            self.config['lcd_settings'] = {
                'i2c_addr': lcd_addr,
                'i2c_bus': self.lcd_bus_var.get(),
                'backlight': self.lcd_backlight_var.get()
            }
        except ValueError:
            messagebox.showwarning("警告", "LCD I2Cアドレスが正しくありません")
            return
        
        if self.save_config():
            # 現在の設定表示を更新
            self.current_url_label.config(text=self.config['server_url'])
            
            # 未送信データを送信
            try:
                self.status_label.config(text="未送信データを確認中...")
                self.root.update()
                
                success, fail, total = self.send_pending_data(self.config['server_url'])
                
                if total > 0:
                    msg = f"未送信データ送信結果:\n\n総件数: {total}件\n成功: {success}件\n失敗: {fail}件"
                    if fail > 0:
                        messagebox.showwarning("送信完了（一部失敗）", msg)
                    else:
                        messagebox.showinfo("送信完了", msg)
            except Exception as e:
                print(f"未送信データ送信エラー: {e}")
            
            # クライアントを起動
            try:
                self.status_label.config(text="クライアントを起動中...")
                self.root.update()
                
                if sys.platform == "win32":
                    # Windows版: win_client.py（参照先変更禁止）
                    subprocess.Popen(["python", "win_client.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # ラズパイ版: pi_client.py（参照先変更禁止 - バージョン管理方針参照: docs/NO_NEW_VERSIONS.md）
                    subprocess.Popen(["python3", "pi_client.py"])
                
                self.client_started = True
                messagebox.showinfo("起動", f"クライアントを起動しました\n\nサーバーURL: {self.config['server_url']}\n\n設定画面を閉じてもクライアントは動作し続けます。")
                self.root.destroy()
            except Exception as e:
                messagebox.showerror("エラー", f"クライアントの起動に失敗しました:\n{e}")
                self.status_label.config(text="[ERROR] 起動失敗")
    
    def on_closing(self):
        """ウィンドウを閉じる時の処理"""
        if self.client_started:
            # クライアントが起動済みの場合は閉じる
            self.root.destroy()
        else:
            # まだ起動していない場合は確認
            if messagebox.askokcancel("終了", "設定を保存せずに終了しますか？"):
                self.root.destroy()
    
    def run(self):
        """GUIを実行"""
        self.root.mainloop()


def main():
    """エントリーポイント"""
    app = ConfigGUI()
    app.run()


if __name__ == "__main__":
    main()

