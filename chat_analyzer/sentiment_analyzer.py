from typing import Dict, List, Tuple
import re
import jieba
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
        # 简单的情感词典
        self.positive_words = set(['喜欢', '开心', '好', '棒', '爱', '感谢', '谢谢', '希望', '期待', '加油',
                                 '赞', '优秀', '完美', '快乐', '温暖', '支持', '同意', '可以', '好的'])
        self.negative_words = set(['不', '没', '难过', '讨厌', '烦', '累', '怕', '担心', '生气', '失望',
                                 '抱歉', '对不起', '不好', '不行', '不可以', '不要'])
        
    def analyze_message(self, message: str) -> Dict:
        """分析单条消息的情感"""
        # 分词
        words = jieba.lcut(message)
        
        # 计算情感得分
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_words = len(words)
        if total_words == 0:
            sentiment_score = 0.5
        else:
            # 计算情感得分 (0-1之间)
            sentiment_score = (positive_count - negative_count + total_words) / (total_words * 2)
            sentiment_score = max(0, min(1, sentiment_score))  # 确保在0-1之间
        
        # 确定情感标签
        if sentiment_score > 0.6:
            sentiment = 'positive'
        elif sentiment_score < 0.4:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        return {
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'emotion': sentiment,  # 简化版本中情感和情绪相同
            'emotion_score': sentiment_score
        }
    
    def analyze_conversation_pair(self, pair: Dict) -> Dict:
        """分析对话对的情感特征"""
        first_message_analysis = self.analyze_message(pair['first_message'])
        second_message_analysis = self.analyze_message(pair['second_message'])
        
        return {
            'first_sender': pair['first_sender'],
            'second_sender': pair['second_sender'],
            'first_sentiment': first_message_analysis['sentiment'],
            'second_sentiment': second_message_analysis['sentiment'],
            'first_emotion': first_message_analysis['emotion'],
            'second_emotion': second_message_analysis['emotion'],
            'response_time': pair['response_time'],
            'message_length_ratio': len(pair['second_message']) / len(pair['first_message']) if pair['first_message'] else 1
        }
    
    def calculate_engagement_score(self, analysis: Dict) -> float:
        """计算对话参与度分数"""
        # 基于回复时间、消息长度比例和情感强度计算参与度
        time_score = 1 / (1 + analysis['response_time'] / 3600)  # 时间越短分数越高
        length_score = min(analysis['message_length_ratio'], 1)  # 消息长度比例
        sentiment_score = analysis.get('second_sentiment_score', 0.5)  # 情感强度
        
        return (time_score * 0.4 + length_score * 0.3 + sentiment_score * 0.3) * 100 