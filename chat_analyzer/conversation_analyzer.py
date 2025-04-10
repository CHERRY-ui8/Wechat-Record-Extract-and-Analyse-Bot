import pandas as pd
from typing import List, Dict, Tuple
import numpy as np
from collections import Counter
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
import zhipuai
import re
import time

class ConversationAnalyzer:
    def __init__(self, user_name: str):
        self.user_name = user_name
        load_dotenv()
        self.client = zhipuai.ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))  # 创建 ZhipuAI 实例
        
    def group_messages_by_time(self, df: pd.DataFrame, time_threshold: int = 1800) -> List[List[Dict]]:
        """根据时间间隔将消息分组"""
        groups = []
        current_group = []
        
        for _, row in df.iterrows():
            if not current_group:
                current_group.append(row.to_dict())
            else:
                time_diff = (row['timestamp'] - current_group[-1]['timestamp']).total_seconds()
                if time_diff <= time_threshold:
                    current_group.append(row.to_dict())
                else:
                    groups.append(current_group)
                    current_group = [row.to_dict()]
                    
        if current_group:
            groups.append(current_group)
            
        return groups
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理和修复 JSON 字符串"""
        # 查找第一个 { 和最后一个 } 之间的内容
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start == -1 or end == 0:
            # 尝试查找 JSON 代码块
            if '```json' in json_str:
                json_block = json_str.split('```json')[-1].split('```')[0].strip()
                start = json_block.find('{')
                end = json_block.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = json_block[start:end]
            else:
                raise ValueError("No JSON content found")
        else:
            json_str = json_str[start:end]
        
        # 处理嵌套的大括号
        if json_str.count('{') > 1:
            # 找到最内层的大括号
            inner_start = json_str.rfind('{')
            inner_end = json_str.find('}', inner_start) + 1
            if inner_start != -1 and inner_end != 0:
                json_str = json_str[inner_start:inner_end]
        
        # 移除多余的逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        json_str = re.sub(r',(\s*,)', ',', json_str)
        
        return json_str
    
    def _filter_sensitive_content(self, text: str) -> str:
        """过滤可能的敏感内容"""
        # 替换可能的敏感词
        sensitive_words = ['自杀', '暴力', '色情', '赌博']
        filtered_text = text
        for word in sensitive_words:
            filtered_text = filtered_text.replace(word, '**')
        return filtered_text
    
    def analyze_topic_with_zhipu(self, messages: List[Dict], max_retries: int = 3, retry_delay: int = 5) -> Dict:
        """使用智谱 AI 分析对话主题和重要性"""
        # 构建对话文本并过滤敏感内容
        conversation_text = "\n".join([
            f"{msg['sender']} ({msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}): {self._filter_sensitive_content(msg['content'])}"
            for msg in messages
        ])
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="chatglm_turbo",
                    messages=[
                        {"role": "system", "content": """你是一个专业的对话分析师。请严格按照以下要求回复：
1. 只返回JSON格式的内容，不要添加任何其他文字
2. 使用客观、中性的语言
3. 避免任何敏感或不当的表述
4. 如果内容不合适，返回默认的中性分析结果"""},
                        {"role": "user", "content": f"""分析以下对话：

{conversation_text}

请严格按照以下JSON格式回复：
{{
    "topic": "对话主题",
    "is_new_topic": true或false,
    "new_topic_reason": "判断理由",
    "importance": 分数(1-10),
    "attitudes": "双方态度的客观描述",
    "depth": 分数(1-10)
}}"""}
                    ],
                    temperature=0.7,
                    timeout=30
                )
                
                # 解析响应
                content = response.choices[0].message.content
                
                # 检查响应是否是异常模式（比如全是感叹号）
                if content.count('!') > len(content) * 0.5:
                    raise ValueError("API returned invalid response (exclamation marks)")
                
                try:
                    # 清理和修复 JSON 字符串
                    cleaned_content = self._clean_json_string(content)
                    
                    try:
                        analysis = json.loads(cleaned_content)
                    except json.JSONDecodeError as je:
                        print(f"JSON解析错误: {je}")
                        print(f"清理后的响应: {cleaned_content}")
                        raise
                    
                    # 验证和规范化结果
                    analysis = {
                        'topic': str(analysis.get('topic', '未知')),
                        'is_new_topic': bool(analysis.get('is_new_topic', False)),
                        'new_topic_reason': str(analysis.get('new_topic_reason', '无')),
                        'importance': min(max(int(analysis.get('importance', 5)), 1), 10),
                        'attitudes': str(analysis.get('attitudes', '中性')),
                        'depth': min(max(int(analysis.get('depth', 5)), 1), 10)
                    }
                    
                    return {
                        'messages': messages,
                        'analysis': analysis
                    }
                except Exception as e:
                    print(f"处理响应时出错: {str(e)}")
                    print(f"原始响应: {content}")
                    if attempt < max_retries - 1:
                        print(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次尝试失败: {str(e)}")
                    print(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"智谱 AI 分析出错: {str(e)}")
                    if len(messages) > 0:
                        print(f"消息数量: {len(messages)}")
                        print(f"第一条消息: {messages[0]['content'][:100]}...")
                    return {
                        'messages': messages,
                        'analysis': {
                            'topic': '未知',
                            'is_new_topic': False,
                            'new_topic_reason': f'分析失败: {str(e)}',
                            'importance': 5,
                            'attitudes': '中性',
                            'depth': 5
                        }
                    }
    
    def analyze_conversation(self, df: pd.DataFrame) -> Dict:
        """分析整个对话"""
        # 按时间分组
        print("正在按时间分组消息...")
        message_groups = self.group_messages_by_time(df)
        total_groups = len(message_groups)
        print(f"共找到 {total_groups} 组对话")
        
        # 尝试加载之前的分析结果
        analyzed_groups = self._load_intermediate_results()
        start_index = len(analyzed_groups)
        
        if start_index > 0:
            print(f"找到之前的分析结果，从第 {start_index + 1} 组继续分析...")
        
        # 分析每个对话组
        for i, group in enumerate(message_groups[start_index:], start_index + 1):
            print(f"\r正在分析第 {i}/{total_groups} 组对话... ({(i/total_groups*100):.1f}%)", end="", flush=True)
            try:
                analysis = self.analyze_topic_with_zhipu(group)
                analyzed_groups.append(analysis)
                
                # 每处理10组或处理完成时保存一次中间结果
                if i % 10 == 0 or i == total_groups:
                    print(f"\n已完成 {i} 组对话的分析，正在保存中间结果...")
                    self._save_intermediate_results(analyzed_groups)
            except KeyboardInterrupt:
                print("\n\n检测到中断信号，正在保存当前进度...")
                self._save_intermediate_results(analyzed_groups)
                print(f"已保存到第 {i} 组对话，下次运行时将从此处继续。")
                raise
            except Exception as e:
                print(f"\n处理第 {i} 组对话时出错: {str(e)}")
                print("继续处理下一组...")
                continue
        
        print("\n对话分析完成，正在计算统计数据...")
        
        # 统计话题发起
        topic_initiations = {
            'user': sum(1 for g in analyzed_groups 
                       if g['analysis']['is_new_topic'] and g['messages'][0]['sender'] == self.user_name),
            'partner': sum(1 for g in analyzed_groups 
                         if g['analysis']['is_new_topic'] and g['messages'][0]['sender'] != self.user_name)
        }
        
        # 计算平均回复时间
        response_times = df.groupby('sender')['response_time'].mean()
        
        return {
            'analyzed_groups': analyzed_groups,
            'topic_initiation': topic_initiations,
            'response_patterns': {
                'user_avg_response_time': response_times.get(self.user_name, 0),
                'partner_avg_response_time': response_times.mean() - response_times.get(self.user_name, 0)
            }
        }
    
    def _load_intermediate_results(self) -> List[Dict]:
        """加载中间分析结果"""
        try:
            filepath = os.path.join('analysis_results', 'intermediate_results.json')
            if not os.path.exists(filepath):
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 将字符串时间戳转换回 Timestamp 对象
            analyzed_groups = []
            for group in data['analyzed_groups']:
                messages = []
                for msg in group['messages']:
                    msg_copy = msg.copy()
                    msg_copy['timestamp'] = pd.Timestamp(msg['timestamp'])
                    messages.append(msg_copy)
                
                analyzed_groups.append({
                    'messages': messages,
                    'analysis': group['analysis']
                })
                
            return analyzed_groups
        except Exception as e:
            print(f"加载中间结果时出错: {str(e)}")
            return []
    
    def _save_intermediate_results(self, analyzed_groups: List[Dict], filename: str = 'intermediate_results.json'):
        """保存中间分析结果"""
        try:
            output_dir = 'analysis_results'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 转换 Timestamp 为字符串
            serializable_groups = []
            for group in analyzed_groups:
                serializable_group = {
                    'messages': [{
                        'sender': msg['sender'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'is_user': msg['is_user']
                    } for msg in group['messages']],
                    'analysis': group['analysis']
                }
                serializable_groups.append(serializable_group)
            
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'analyzed_groups': serializable_groups,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"\n警告：保存中间结果时出错: {str(e)}")
    
    def get_key_discussions(self, analyzed_groups: List[Dict], importance_threshold: float = 7) -> List[Dict]:
        """获取重要讨论"""
        return [group for group in analyzed_groups 
                if group['analysis']['importance'] >= importance_threshold]
    
    def calculate_engagement_metrics(self, df: pd.DataFrame) -> Dict:
        """计算参与度指标"""
        # 计算每日消息数量
        daily_messages = df.groupby([df['timestamp'].dt.date, 'sender']).size().unstack()
        
        # 计算活跃时间段
        hourly_messages = df.groupby([df['timestamp'].dt.hour, 'sender']).size().unstack()
        
        return {
            'daily_messages': daily_messages.to_dict(),
            'hourly_messages': hourly_messages.to_dict()
        } 