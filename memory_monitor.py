#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メモリ使用量モニタリングツール
- プロセスのメモリ使用量を定期的にログに記録
- メモリリーク検出のためのデバッグツール
"""

import psutil
import time
import os
import sys
from datetime import datetime
from pathlib import Path
import tracemalloc
import gc

class MemoryMonitor:
    """メモリ使用量モニタリングクラス"""
    
    def __init__(self, log_file="memory_usage.log", interval=60, enable_tracemalloc=False):
        """
        初期化
        
        Args:
            log_file: ログファイルのパス
            interval: モニタリング間隔（秒）
            enable_tracemalloc: tracemalloc（詳細メモリトレース）を有効化
        """
        self.log_file = Path(log_file)
        self.interval = interval
        self.enable_tracemalloc = enable_tracemalloc
        self.process = psutil.Process(os.getpid())
        self.running = False
        self.start_time = None
        self.initial_memory = None
        self.peak_memory = 0
        self.log_count = 0
        
        # tracemalloc開始
        if self.enable_tracemalloc:
            tracemalloc.start()
            print(f"[MemoryMonitor] tracemalloc有効化")
        
        # ログファイル初期化
        self._init_log_file()
    
    def _init_log_file(self):
        """ログファイルの初期化"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"メモリモニタリング開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"PID: {os.getpid()}\n")
            f.write(f"モニタリング間隔: {self.interval}秒\n")
            f.write("=" * 80 + "\n\n")
        
        print(f"[MemoryMonitor] ログファイル: {self.log_file.absolute()}")
    
    def get_memory_info(self):
        """現在のメモリ使用量を取得"""
        try:
            # プロセスのメモリ情報
            mem_info = self.process.memory_info()
            
            # RSS (Resident Set Size) - 実際に使用している物理メモリ
            rss_mb = mem_info.rss / 1024 / 1024
            
            # VMS (Virtual Memory Size) - 仮想メモリ
            vms_mb = mem_info.vms / 1024 / 1024
            
            # システム全体のメモリ情報
            sys_mem = psutil.virtual_memory()
            sys_total_mb = sys_mem.total / 1024 / 1024
            sys_available_mb = sys_mem.available / 1024 / 1024
            sys_percent = sys_mem.percent
            
            return {
                'rss_mb': rss_mb,
                'vms_mb': vms_mb,
                'sys_total_mb': sys_total_mb,
                'sys_available_mb': sys_available_mb,
                'sys_percent': sys_percent
            }
        except Exception as e:
            print(f"[MemoryMonitor] メモリ情報取得エラー: {e}")
            return None
    
    def get_tracemalloc_info(self):
        """tracemalloc情報を取得"""
        if not self.enable_tracemalloc:
            return None
        
        try:
            # 現在のメモリ使用量
            current, peak = tracemalloc.get_traced_memory()
            current_mb = current / 1024 / 1024
            peak_mb = peak / 1024 / 1024
            
            # トップ10のメモリ消費箇所
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            return {
                'current_mb': current_mb,
                'peak_mb': peak_mb,
                'top_stats': top_stats[:10]
            }
        except Exception as e:
            print(f"[MemoryMonitor] tracemalloc情報取得エラー: {e}")
            return None
    
    def log_memory_usage(self):
        """メモリ使用量をログに記録"""
        mem_info = self.get_memory_info()
        if not mem_info:
            return
        
        # 経過時間
        elapsed = time.time() - self.start_time if self.start_time else 0
        elapsed_str = f"{int(elapsed // 3600):02d}:{int((elapsed % 3600) // 60):02d}:{int(elapsed % 60):02d}"
        
        # メモリ増加量
        if self.initial_memory is None:
            self.initial_memory = mem_info['rss_mb']
            memory_delta = 0
        else:
            memory_delta = mem_info['rss_mb'] - self.initial_memory
        
        # ピークメモリ更新
        if mem_info['rss_mb'] > self.peak_memory:
            self.peak_memory = mem_info['rss_mb']
        
        # ログ出力
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = (
            f"[{timestamp}] 経過: {elapsed_str} | "
            f"RSS: {mem_info['rss_mb']:.2f}MB (初期比: {memory_delta:+.2f}MB) | "
            f"VMS: {mem_info['vms_mb']:.2f}MB | "
            f"ピーク: {self.peak_memory:.2f}MB | "
            f"システム: {mem_info['sys_percent']:.1f}% ({mem_info['sys_available_mb']:.0f}MB空き)\n"
        )
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # コンソール出力（10回ごと）
        self.log_count += 1
        if self.log_count % 10 == 0:
            print(f"[MemoryMonitor] {log_entry.strip()}")
        
        # メモリ増加が大きい場合は警告
        if memory_delta > 50:  # 50MB以上増加
            warning = f"⚠️ [警告] メモリが初期値から {memory_delta:.2f}MB 増加しています\n"
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(warning)
            print(warning.strip())
        
        # tracemalloc情報
        if self.enable_tracemalloc and self.log_count % 10 == 0:
            trace_info = self.get_tracemalloc_info()
            if trace_info:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"  [tracemalloc] Current: {trace_info['current_mb']:.2f}MB, Peak: {trace_info['peak_mb']:.2f}MB\n")
                    f.write("  [Top 10 メモリ消費箇所]\n")
                    for stat in trace_info['top_stats']:
                        f.write(f"    {stat}\n")
                    f.write("\n")
    
    def start(self):
        """モニタリング開始"""
        if self.running:
            print("[MemoryMonitor] 既に実行中です")
            return
        
        self.running = True
        self.start_time = time.time()
        print(f"[MemoryMonitor] モニタリング開始 (間隔: {self.interval}秒)")
        
        import threading
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def _monitor_loop(self):
        """モニタリングループ"""
        while self.running:
            try:
                self.log_memory_usage()
                
                # ガベージコレクション実行（メモリ解放）
                collected = gc.collect()
                if collected > 0 and self.log_count % 10 == 0:
                    print(f"[MemoryMonitor] GC実行: {collected}個のオブジェクトを回収")
                
                time.sleep(self.interval)
            except Exception as e:
                print(f"[MemoryMonitor] モニタリングエラー: {e}")
                time.sleep(self.interval)
    
    def stop(self):
        """モニタリング停止"""
        if not self.running:
            return
        
        self.running = False
        
        # 最終ログ
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"モニタリング終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"実行時間: {time.time() - self.start_time:.0f}秒\n")
            f.write(f"初期メモリ: {self.initial_memory:.2f}MB\n")
            f.write(f"最終メモリ: {self.get_memory_info()['rss_mb']:.2f}MB\n")
            f.write(f"ピークメモリ: {self.peak_memory:.2f}MB\n")
            f.write(f"メモリ増加量: {self.get_memory_info()['rss_mb'] - self.initial_memory:.2f}MB\n")
            f.write("=" * 80 + "\n")
        
        if self.enable_tracemalloc:
            tracemalloc.stop()
        
        print(f"[MemoryMonitor] モニタリング停止 - ログ保存: {self.log_file}")


def test_memory_monitor():
    """テスト用"""
    print("メモリモニタリングテスト開始")
    
    # モニター作成（5秒間隔、tracemalloc有効）
    monitor = MemoryMonitor(log_file="test_memory.log", interval=5, enable_tracemalloc=True)
    monitor.start()
    
    # メモリを消費するダミー処理
    data_list = []
    try:
        for i in range(60):  # 5分間
            # 1MBずつデータを追加
            data_list.append(b'0' * (1024 * 1024))
            time.sleep(5)
            
            if i % 10 == 0:
                print(f"反復 {i}: {len(data_list)}MB のデータを保持")
    
    except KeyboardInterrupt:
        print("\nテスト中断")
    
    finally:
        monitor.stop()
        print("テスト完了")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_memory_monitor()
    else:
        print("使用方法:")
        print("  from memory_monitor import MemoryMonitor")
        print("  monitor = MemoryMonitor(log_file='memory_usage.log', interval=60)")
        print("  monitor.start()")
        print("  # ... アプリケーション実行 ...")
        print("  monitor.stop()")
        print("")
        print("テスト実行:")
        print("  python memory_monitor.py test")
