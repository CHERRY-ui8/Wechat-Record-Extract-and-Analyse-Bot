import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, List
import numpy as np
import matplotlib as mpl
import os

class ChatVisualizer:
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['PingFang HK', 'STHeiti', 'Hei', 'Heiti TC', 'LiHei Pro']  # 使用系统中可用的中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        # 使用 seaborn 的样式设置
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        # 设置 matplotlib 的默认字体
        mpl.rcParams['font.family'] = 'sans-serif'
        mpl.rcParams['font.sans-serif'] = ['PingFang HK', 'STHeiti', 'Hei', 'Heiti TC', 'LiHei Pro']
        
    def _ensure_directory_exists(self, file_path: str):
        """确保保存图片的目录存在"""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
    def _save_figure(self, save_path: str):
        """统一的图片保存方法"""
        if save_path:
            self._ensure_directory_exists(save_path)
            plt.savefig(save_path, 
                       format='png',
                       bbox_inches='tight', 
                       dpi=300, 
                       backend='agg',
                       facecolor='white',
                       edgecolor='none',
                       pad_inches=0.1)
        plt.close('all')
        
    def plot_engagement_scores(self, scores: Dict, save_path: str = None):
        """绘制参与度分数"""
        plt.figure(figsize=(10, 6))
        plt.bar(['用户', '对方'], [scores['user_score'], scores['partner_score']])
        plt.title('对话参与度对比')
        plt.ylabel('参与度分数')
        plt.ylim(0, 100)
        
        self._save_figure(save_path)
        
    def plot_response_time_distribution(self, df: pd.DataFrame, save_path: str = None):
        """绘制回复时间分布"""
        plt.figure(figsize=(12, 6))
        sns.histplot(data=df, x='response_time', hue='sender', bins=50)
        plt.title('回复时间分布')
        plt.xlabel('回复时间（秒）')
        plt.ylabel('频次')
        
        self._save_figure(save_path)
        
    def plot_message_length_distribution(self, df: pd.DataFrame, save_path: str = None):
        """绘制消息长度分布"""
        plt.figure(figsize=(12, 6))
        sns.histplot(data=df, x=df['content'].str.len(), hue='sender', bins=50)
        plt.title('消息长度分布')
        plt.xlabel('消息长度（字符）')
        plt.ylabel('频次')
        
        self._save_figure(save_path)
        
    def plot_daily_activity(self, daily_messages: Dict, save_path: str = None):
        """绘制每日活动趋势"""
        df = pd.DataFrame(daily_messages)
        plt.figure(figsize=(15, 6))
        df.plot(kind='line')
        plt.title('每日消息数量趋势')
        plt.xlabel('日期')
        plt.ylabel('消息数量')
        plt.xticks(rotation=45)
        
        self._save_figure(save_path)
        
    def plot_hourly_activity(self, hourly_messages: Dict, save_path: str = None):
        """绘制小时活动分布"""
        df = pd.DataFrame(hourly_messages)
        plt.figure(figsize=(12, 6))
        df.plot(kind='bar')
        plt.title('小时消息分布')
        plt.xlabel('小时')
        plt.ylabel('消息数量')
        
        self._save_figure(save_path)
        
    def generate_summary_report(self, analysis_results: Dict, save_path: str = None):
        """生成总结报告"""
        report = []
        report.append("聊天记录分析报告")
        report.append("=" * 50)
        
        # 参与度分析
        report.append("\n1. 参与度分析")
        report.append(f"用户平均回复时间: {analysis_results['response_patterns']['user_avg_response_time']:.2f}秒")
        report.append(f"对方平均回复时间: {analysis_results['response_patterns']['partner_avg_response_time']:.2f}秒")
        
        # 话题发起分析
        report.append("\n2. 话题发起分析")
        report.append(f"用户发起话题次数: {analysis_results['topic_initiation']['user']}")
        report.append(f"对方发起话题次数: {analysis_results['topic_initiation']['partner']}")
        
        # 关键讨论
        report.append("\n3. 关键讨论分析")
        for i, discussion in enumerate(analysis_results['key_discussions'], 1):
            report.append(f"\n关键讨论 {i}:")
            report.append(f"主题: {discussion['analysis']['topic']}")
            report.append(f"重要性: {discussion['analysis']['importance']}/10")
            report.append(f"对话深度: {discussion['analysis']['depth']}/10")
            report.append(f"双方态度: {discussion['analysis']['attitudes']}")
            report.append("\n对话内容:")
            for msg in discussion['messages']:
                report.append(f"{msg['timestamp']} - {msg['sender']}: {msg['content'][:100]}...")
        
        # 话题分析
        report.append("\n4. 话题分析")
        topics = {}
        for group in analysis_results['conversation_analysis']['analyzed_groups']:
            topic = group['analysis']['topic']
            if topic not in topics:
                topics[topic] = 0
            topics[topic] += 1
            
        report.append("\n主要话题统计:")
        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
            report.append(f"{topic}: {count}次讨论")
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report))
                
        return '\n'.join(report) 