import re
from datetime import datetime
import pandas as pd
from typing import List, Dict, Tuple

class ChatDataProcessor:
    def __init__(self, file_path: str, user_name: str):
        self.file_path = file_path
        self.user_name = user_name
        self.messages = []
        
    def parse_chat_file(self) -> pd.DataFrame:
        """解析聊天记录文件，返回结构化的DataFrame"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 使用正则表达式匹配消息
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+([^\n]+)\n(.*?)(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        messages = []
        for match in matches:
            timestamp, sender, content = match
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            messages.append({
                'timestamp': timestamp,
                'sender': sender.strip(),
                'content': content.strip(),
                'is_user': sender.strip() == self.user_name
            })
            
        return pd.DataFrame(messages)
    
    def calculate_response_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算每条消息的回复时间"""
        df = df.sort_values('timestamp')
        df['response_time'] = df['timestamp'].diff()
        df['response_time'] = df['response_time'].apply(lambda x: x.total_seconds() if pd.notnull(x) else None)
        return df
    
    def get_conversation_pairs(self, df: pd.DataFrame) -> List[Dict]:
        """将对话组织成对话对的形式"""
        pairs = []
        current_pair = None
        
        for _, row in df.iterrows():
            if current_pair is None:
                current_pair = {
                    'first_sender': row['sender'],
                    'first_message': row['content'],
                    'first_timestamp': row['timestamp'],
                    'response_time': None,
                    'second_sender': None,
                    'second_message': None,
                    'second_timestamp': None
                }
            else:
                current_pair['second_sender'] = row['sender']
                current_pair['second_message'] = row['content']
                current_pair['second_timestamp'] = row['timestamp']
                current_pair['response_time'] = (row['timestamp'] - current_pair['first_timestamp']).total_seconds()
                pairs.append(current_pair)
                current_pair = None
                
        return pairs 