import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os

class KeyMomentsAnalyzer:
    def __init__(self, chat_file: str, user_name: str, partner_name: str):
        self.chat_file = chat_file
        self.user_name = user_name
        self.partner_name = partner_name
        self.messages = []  # 添加 messages 属性
        self.key_dates = {
            'relationship_start': None,  # 正式确定关系的时间
            'conflicts': [],             # 吵架的时间点
            'special_days': {            # 特殊日子
                'anniversary': None,     # 纪念日
                'valentine': [],         # 情人节
                'qixi': [],             # 七夕节
            }
        }
        self.landmark_topics = {
            'terms_of_endearment': [],   # 亲昵称呼
            'literature': [],            # 文学作品讨论
            'movies': [],               # 电影讨论
            'tv_shows': [],             # 电视剧讨论
            'social_topics': [],        # 社会话题
            'intimate_topics': []       # 亲密话题
        }
        
    def set_key_date(self, date_type: str, date: str, description: str = ""):
        """设置关键时间节点"""
        if date_type == 'relationship_start':
            self.key_dates['relationship_start'] = {
                'date': datetime.strptime(date, '%Y-%m-%d'),
                'description': description
            }
        elif date_type == 'conflict':
            self.key_dates['conflicts'].append({
                'date': datetime.strptime(date, '%Y-%m-%d'),
                'description': description
            })
        elif date_type in ['anniversary', 'valentine', 'qixi']:
            if date_type == 'anniversary':
                self.key_dates['special_days']['anniversary'] = {
                    'date': datetime.strptime(date, '%Y-%m-%d'),
                    'description': description
                }
            else:
                self.key_dates['special_days'][date_type].append({
                    'date': datetime.strptime(date, '%Y-%m-%d'),
                    'description': description
                })

    def analyze_attitude_changes(self, messages: List[Dict[str, Any]], 
                               key_date: datetime, 
                               days_before: int = 7, 
                               days_after: int = 7) -> Dict[str, Any]:
        """分析关键时间点前后的态度变化"""
        start_date = key_date - timedelta(days=days_before)
        end_date = key_date + timedelta(days=days_after)
        
        before_messages = []
        after_messages = []
        
        for msg in messages:
            msg_date = msg['timestamp']  # 直接使用时间戳，不需要转换
            if start_date <= msg_date < key_date:
                before_messages.append(msg)
            elif key_date <= msg_date <= end_date:
                after_messages.append(msg)
        
        return {
            'before': self._analyze_attitude(before_messages),
            'after': self._analyze_attitude(after_messages),
            'change': self._compare_attitudes(
                self._analyze_attitude(before_messages),
                self._analyze_attitude(after_messages)
            )
        }

    def _analyze_attitude(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析消息中的态度"""
        user_messages = [msg for msg in messages if msg['is_user']]
        partner_messages = [msg for msg in messages if not msg['is_user']]
        
        # 分析情感词汇使用
        positive_words = ['喜欢', '爱', '开心', '高兴', '幸福', '好', '棒', '美', '赞', '可爱']
        negative_words = ['讨厌', '生气', '难过', '伤心', '不好', '烦', '累', '困', '忙', '烦']
        neutral_words = ['嗯', '哦', '好', '行', '可以', '知道', '明白', '了解']
        
        def analyze_word_usage(messages):
            content = ' '.join(msg['content'] for msg in messages)
            return {
                'positive_count': sum(1 for word in positive_words if word in content),
                'negative_count': sum(1 for word in negative_words if word in content),
                'neutral_count': sum(1 for word in neutral_words if word in content),
                'total_words': len(content)
            }
        
        # 分析消息长度分布
        def analyze_message_length(messages):
            lengths = [len(msg['content']) for msg in messages]
            return {
                'avg_length': sum(lengths) / len(lengths) if lengths else 0,
                'max_length': max(lengths) if lengths else 0,
                'min_length': min(lengths) if lengths else 0,
                'short_messages_ratio': sum(1 for l in lengths if l < 5) / len(lengths) if lengths else 0,
                'long_messages_ratio': sum(1 for l in lengths if l > 20) / len(lengths) if lengths else 0
            }
        
        # 分析回复时间模式
        def analyze_response_pattern(messages):
            if len(messages) < 2:
                return {'avg_response_time': 0, 'response_consistency': 0}
            
            response_times = []
            for i in range(1, len(messages)):
                time_diff = (messages[i]['timestamp'] - messages[i-1]['timestamp']).total_seconds()
                response_times.append(time_diff)
            
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            std_dev = (sum((t - avg_time) ** 2 for t in response_times) / len(response_times)) ** 0.5 if response_times else 0
            
            return {
                'avg_response_time': avg_time,
                'response_consistency': 1 - (std_dev / avg_time) if avg_time > 0 else 0,
                'quick_responses_ratio': sum(1 for t in response_times if t < 300) / len(response_times) if response_times else 0,
                'slow_responses_ratio': sum(1 for t in response_times if t > 3600) / len(response_times) if response_times else 0
            }
        
        # 分析话题多样性
        def analyze_topic_diversity(messages):
            topics = set()
            for msg in messages:
                content = msg['content'].lower()
                if any(keyword in content for keyword in ['电影', '电视剧', '书', '新闻']):
                    topics.add('entertainment')
                if any(keyword in content for keyword in ['工作', '学习', '项目']):
                    topics.add('work')
                if any(keyword in content for keyword in ['吃', '玩', '旅行']):
                    topics.add('life')
                if any(keyword in content for keyword in ['爱', '喜欢', '想']):
                    topics.add('relationship')
            return len(topics)
        
        return {
            'user': {
                'message_count': len(user_messages),
                'word_usage': analyze_word_usage(user_messages),
                'message_length': analyze_message_length(user_messages),
                'response_pattern': analyze_response_pattern(user_messages),
                'topic_diversity': analyze_topic_diversity(user_messages),
                'active_hours': self._analyze_active_hours(user_messages),
                'message_style': self._analyze_message_style(user_messages)
            },
            'partner': {
                'message_count': len(partner_messages),
                'word_usage': analyze_word_usage(partner_messages),
                'message_length': analyze_message_length(partner_messages),
                'response_pattern': analyze_response_pattern(partner_messages),
                'topic_diversity': analyze_topic_diversity(partner_messages),
                'active_hours': self._analyze_active_hours(partner_messages),
                'message_style': self._analyze_message_style(partner_messages)
            }
        }

    def _compare_attitudes(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """比较前后态度变化"""
        return {
            'user': {
                'message_count_change': after['user']['message_count'] - before['user']['message_count'],
                'avg_length_change': after['user']['message_length']['avg_length'] - before['user']['message_length']['avg_length'],
                'response_time_change': after['user']['response_pattern']['avg_response_time'] - before['user']['response_pattern']['avg_response_time'],
                'sentiment_change': after['user']['word_usage']['positive_count'] - before['user']['word_usage']['positive_count']
            },
            'partner': {
                'message_count_change': after['partner']['message_count'] - before['partner']['message_count'],
                'avg_length_change': after['partner']['message_length']['avg_length'] - before['partner']['message_length']['avg_length'],
                'response_time_change': after['partner']['response_pattern']['avg_response_time'] - before['partner']['response_pattern']['avg_response_time'],
                'sentiment_change': after['partner']['word_usage']['positive_count'] - before['partner']['word_usage']['positive_count']
            }
        }

    def extract_landmark_topics(self, messages: List[Dict[str, Any]]):
        """提取标志性话题"""
        print("\n开始提取标志性话题...")
        self.messages = messages  # 保存消息到实例属性
        terms_of_endearment = ['宝贝', '宝宝', '亲爱的', '老公', '老婆', '亲爱的']
        intimate_keywords = ['性', '爱', '亲密', '身体', '关系']
        
        total_messages = len(messages)
        for i, msg in enumerate(messages, 1):
            if i % 100 == 0:
                print(f"\r正在处理第 {i}/{total_messages} 条消息... ({(i/total_messages*100):.1f}%)", end="", flush=True)
            
            content = msg['content'].lower()
            sender = 'user' if msg['is_user'] else 'partner'
            
            # 检查亲昵称呼
            for term in terms_of_endearment:
                if term in content:
                    if not any(t['term'] == term for t in self.landmark_topics['terms_of_endearment']):
                        self.landmark_topics['terms_of_endearment'].append({
                            'term': term,
                            'first_occurrence': msg['timestamp'],
                            'sender': sender
                        })
                        print(f"\n发现新的亲昵称呼: {term} (时间: {msg['timestamp']})")
            
            # 检查亲密话题
            if any(keyword in content for keyword in intimate_keywords):
                if not any(t['timestamp'] == msg['timestamp'] for t in self.landmark_topics['intimate_topics']):
                    self.landmark_topics['intimate_topics'].append({
                        'timestamp': msg['timestamp'],
                        'content': content,
                        'sender': sender
                    })
                    print(f"\n发现亲密话题讨论 (时间: {msg['timestamp']})")
            
            # 检查文化相关话题
            if re.search(r'《.*》|作者|作家|导演|演员|电影|电视剧|新闻|社会|政治', content):
                category = 'literature' if re.search(r'《.*》|作者|作家', content) else \
                          'movies' if re.search(r'电影|导演|演员', content) else \
                          'tv_shows' if re.search(r'电视剧', content) else \
                          'social_topics'
                
                if not any(t['timestamp'] == msg['timestamp'] for t in self.landmark_topics[category]):
                    self.landmark_topics[category].append({
                        'timestamp': msg['timestamp'],
                        'content': content,
                        'sender': sender
                    })
                    print(f"\n发现{category}相关讨论 (时间: {msg['timestamp']})")
        
        print("\n标志性话题提取完成！")

    def _calculate_avg_response_time(self, messages: List[Dict[str, Any]]) -> float:
        """计算平均回复时间"""
        if len(messages) < 2:
            return 0
        
        total_time = 0
        for i in range(1, len(messages)):
            prev_time = messages[i-1]['timestamp']  # 直接使用时间戳
            curr_time = messages[i]['timestamp']    # 直接使用时间戳
            total_time += (curr_time - prev_time).total_seconds()
        
        return total_time / (len(messages) - 1)

    def _analyze_sentiment(self, messages: List[Dict[str, Any]]) -> float:
        """分析消息情感倾向"""
        positive_keywords = ['喜欢', '爱', '开心', '高兴', '幸福', '好']
        negative_keywords = ['讨厌', '生气', '难过', '伤心', '不好', '烦']
        
        sentiment_score = 0
        for msg in messages:
            content = msg['content']
            for keyword in positive_keywords:
                if keyword in content:
                    sentiment_score += 1
            for keyword in negative_keywords:
                if keyword in content:
                    sentiment_score -= 1
        
        return sentiment_score / len(messages) if messages else 0

    def save_results(self, output_dir: str):
        """保存分析结果"""
        print("\n正在保存分析结果...")
        
        # 自定义 JSON 序列化函数
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            return obj
        
        results = {
            'key_dates': self.key_dates,
            'landmark_topics': self.landmark_topics,
            'attitude_changes': {
                'relationship_start': self.analyze_attitude_changes(
                    self.messages, 
                    self.key_dates['relationship_start']['date']
                ) if self.key_dates['relationship_start'] else None,
                'conflicts': [
                    self.analyze_attitude_changes(
                        self.messages, 
                        conflict['date']
                    ) for conflict in self.key_dates['conflicts']
                ],
                'special_days': {
                    day_type: self.analyze_attitude_changes(
                        self.messages, 
                        day['date']
                    ) for day_type, days in self.key_dates['special_days'].items()
                    for day in (days if isinstance(days, list) else [days] if days else [])
                }
            }
        }
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'key_moments_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=datetime_handler)
        
        print(f"分析结果已保存到: {output_file}")
        
        # 打印关键发现
        print("\n关键发现总结:")
        if self.landmark_topics['terms_of_endearment']:
            print("\n亲昵称呼:")
            for term in self.landmark_topics['terms_of_endearment']:
                print(f"- 首次使用 '{term['term']}' 在 {term['first_occurrence']} (由 {term['sender']} 使用)")
        
        if self.landmark_topics['intimate_topics']:
            print("\n亲密话题讨论:")
            for topic in self.landmark_topics['intimate_topics']:
                print(f"- 在 {topic['timestamp']} 讨论 (由 {topic['sender']} 发起)")
        
        for category in ['literature', 'movies', 'tv_shows', 'social_topics']:
            if self.landmark_topics[category]:
                print(f"\n{category}相关讨论:")
                for topic in self.landmark_topics[category]:
                    print(f"- 在 {topic['timestamp']} 讨论 (由 {topic['sender']} 发起)")

    def analyze_key_moments(self):
        """深入分析关键时间点之间的关系和影响"""
        print("\n开始深入分析关键时间点...")
        
        # 1. 分析关系发展轨迹
        relationship_trajectory = self._analyze_relationship_trajectory()
        
        # 2. 分析冲突模式
        conflict_patterns = self._analyze_conflict_patterns()
        
        # 3. 分析特殊日子的影响
        special_days_impact = self._analyze_special_days_impact()
        
        # 4. 分析话题演变
        topic_evolution = self._analyze_topic_evolution()
        
        # 5. 生成综合分析报告
        analysis_report = {
            'relationship_trajectory': relationship_trajectory,
            'conflict_patterns': conflict_patterns,
            'special_days_impact': special_days_impact,
            'topic_evolution': topic_evolution
        }
        
        return analysis_report

    def _analyze_relationship_trajectory(self) -> Dict[str, Any]:
        """分析关系发展轨迹"""
        trajectory = {
            'stages': [],
            'milestones': [],
            'turning_points': []
        }
        
        # 分析关系发展阶段
        if self.key_dates['relationship_start']:
            start_date = self.key_dates['relationship_start']['date']
            trajectory['stages'].append({
                'stage': 'initial',
                'start_date': start_date,
                'duration': (datetime.now() - start_date).days,
                'characteristics': self._analyze_stage_characteristics(start_date, start_date + timedelta(days=30))
            })
        
        # 分析重要里程碑
        for conflict in self.key_dates['conflicts']:
            trajectory['milestones'].append({
                'type': 'conflict',
                'date': conflict['date'],
                'impact': self._analyze_conflict_impact(conflict['date'])
            })
        
        # 分析转折点
        for day_type, days in self.key_dates['special_days'].items():
            for day in (days if isinstance(days, list) else [days] if days else []):
                trajectory['turning_points'].append({
                    'type': day_type,
                    'date': day['date'],
                    'impact': self._analyze_special_day_impact(day['date'])
                })
        
        return trajectory

    def _analyze_conflict_patterns(self) -> Dict[str, Any]:
        """分析冲突模式"""
        patterns = {
            'frequency': len(self.key_dates['conflicts']),
            'interval_analysis': [],
            'resolution_patterns': [],
            'impact_analysis': []
        }
        
        # 分析冲突间隔
        conflicts = sorted(self.key_dates['conflicts'], key=lambda x: x['date'])
        for i in range(1, len(conflicts)):
            interval = (conflicts[i]['date'] - conflicts[i-1]['date']).days
            patterns['interval_analysis'].append({
                'interval': interval,
                'start_date': conflicts[i-1]['date'],
                'end_date': conflicts[i]['date']
            })
        
        # 分析冲突解决模式
        for conflict in conflicts:
            patterns['resolution_patterns'].append({
                'date': conflict['date'],
                'resolution_time': self._analyze_conflict_resolution(conflict['date']),
                'recovery_pattern': self._analyze_recovery_pattern(conflict['date'])
            })
        
        return patterns

    def _analyze_special_days_impact(self) -> Dict[str, Any]:
        """分析特殊日子的影响"""
        impact = {
            'anniversary': {},
            'valentine': [],
            'qixi': []
        }
        
        # 分析纪念日影响
        if self.key_dates['special_days']['anniversary']:
            anniversary = self.key_dates['special_days']['anniversary']
            impact['anniversary'] = {
                'date': anniversary['date'],
                'preparation_pattern': self._analyze_preparation_pattern(anniversary['date']),
                'celebration_pattern': self._analyze_celebration_pattern(anniversary['date']),
                'aftermath_impact': self._analyze_aftermath_impact(anniversary['date'])
            }
        
        # 分析情人节影响
        for valentine in self.key_dates['special_days']['valentine']:
            impact['valentine'].append({
                'date': valentine['date'],
                'celebration_pattern': self._analyze_celebration_pattern(valentine['date']),
                'gift_pattern': self._analyze_gift_pattern(valentine['date'])
            })
        
        # 分析七夕节影响
        for qixi in self.key_dates['special_days']['qixi']:
            impact['qixi'].append({
                'date': qixi['date'],
                'celebration_pattern': self._analyze_celebration_pattern(qixi['date']),
                'cultural_significance': self._analyze_cultural_significance(qixi['date'])
            })
        
        return impact

    def _analyze_topic_evolution(self) -> Dict[str, Any]:
        """分析话题演变"""
        evolution = {
            'terms_of_endearment': self._analyze_terms_evolution(),
            'intimate_topics': self._analyze_intimate_topics_evolution(),
            'shared_interests': self._analyze_shared_interests_evolution()
        }
        
        return evolution

    def _analyze_stage_characteristics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """分析特定阶段的特征"""
        stage_messages = [msg for msg in self.messages if start_date <= msg['timestamp'] <= end_date]
        return {
            'message_frequency': len(stage_messages) / (end_date - start_date).days if (end_date - start_date).days > 0 else 0,
            'topic_diversity': self._calculate_topic_diversity(stage_messages),
            'emotional_intensity': self._calculate_emotional_intensity(stage_messages),
            'interaction_pattern': self._analyze_interaction_pattern(stage_messages)
        }

    def _analyze_conflict_impact(self, conflict_date: datetime) -> Dict[str, Any]:
        """分析冲突的影响"""
        before = self.analyze_attitude_changes(self.messages, conflict_date, days_before=7, days_after=0)
        after = self.analyze_attitude_changes(self.messages, conflict_date, days_before=0, days_after=7)
        
        return {
            'immediate_impact': self._compare_attitudes(before['before'], after['after']),
            'recovery_time': self._calculate_recovery_time(conflict_date),
            'long_term_impact': self._analyze_long_term_impact(conflict_date)
        }

    def _analyze_special_day_impact(self, special_date: datetime) -> Dict[str, Any]:
        """分析特殊日子的影响"""
        return {
            'preparation_behavior': self._analyze_preparation_behavior(special_date),
            'celebration_quality': self._analyze_celebration_quality(special_date),
            'aftermath_effect': self._analyze_aftermath_effect(special_date)
        }

    def _analyze_terms_evolution(self) -> List[Dict[str, Any]]:
        """分析亲昵称呼的演变"""
        evolution = []
        terms = sorted(self.landmark_topics['terms_of_endearment'], key=lambda x: x['first_occurrence'])
        
        for i in range(len(terms)):
            evolution.append({
                'term': terms[i]['term'],
                'first_use': terms[i]['first_occurrence'],
                'usage_frequency': self._calculate_term_frequency(terms[i]['term']),
                'adoption_pattern': self._analyze_term_adoption(terms[i])
            })
        
        return evolution

    def _analyze_intimate_topics_evolution(self) -> List[Dict[str, Any]]:
        """分析亲密话题的演变"""
        evolution = []
        topics = sorted(self.landmark_topics['intimate_topics'], key=lambda x: x['timestamp'])
        
        for i in range(len(topics)):
            evolution.append({
                'timestamp': topics[i]['timestamp'],
                'topic_depth': self._analyze_topic_depth(topics[i]),
                'discussion_pattern': self._analyze_discussion_pattern(topics[i]),
                'follow_up_impact': self._analyze_follow_up_impact(topics[i])
            })
        
        return evolution

    def _analyze_shared_interests_evolution(self) -> Dict[str, Any]:
        """分析共同兴趣的演变"""
        evolution = {
            'literature': self._analyze_category_evolution('literature'),
            'movies': self._analyze_category_evolution('movies'),
            'tv_shows': self._analyze_category_evolution('tv_shows'),
            'social_topics': self._analyze_category_evolution('social_topics')
        }
        
        return evolution

    def _analyze_category_evolution(self, category: str) -> List[Dict[str, Any]]:
        """
        分析特定类别话题的演变过程
        
        Args:
            category: 要分析的话题类别
            
        Returns:
            包含话题演变信息的列表
        """
        evolution = []
        for date in self.key_dates:
            period_messages = self._get_messages_in_period(date)
            category_messages = [msg for msg in period_messages if category in msg.get('category', '')]
            
            if category_messages:
                evolution.append({
                    'date': date,
                    'message_count': len(category_messages),
                    'sentiment': self._calculate_sentiment(category_messages),
                    'key_messages': self._extract_key_messages(category_messages)
                })
        
        return evolution

    def _calculate_topic_diversity(self, messages: List[Dict[str, Any]]) -> float:
        """计算话题多样性"""
        topics = set()
        for msg in messages:
            content = msg['content'].lower()
            if any(keyword in content for keyword in ['电影', '电视剧', '书', '新闻']):
                topics.add('entertainment')
            if any(keyword in content for keyword in ['工作', '学习', '项目']):
                topics.add('work')
            if any(keyword in content for keyword in ['吃', '玩', '旅行']):
                topics.add('life')
        return len(topics) / len(messages) if messages else 0

    def _calculate_emotional_intensity(self, messages: List[Dict[str, Any]]) -> float:
        """计算情感强度"""
        intensity = 0
        for msg in messages:
            content = msg['content']
            # 计算情感词密度
            emotional_words = sum(1 for word in ['喜欢', '爱', '开心', '难过', '生气'] if word in content)
            intensity += emotional_words / len(content) if content else 0
        return intensity / len(messages) if messages else 0

    def _analyze_interaction_pattern(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析互动模式"""
        user_messages = [msg for msg in messages if msg['is_user']]
        partner_messages = [msg for msg in messages if not msg['is_user']]
        
        return {
            'message_ratio': len(user_messages) / len(partner_messages) if partner_messages else 0,
            'response_time': self._calculate_avg_response_time(messages),
            'conversation_depth': self._calculate_conversation_depth(messages)
        }

    def _calculate_conversation_depth(self, messages: List[Dict[str, Any]]) -> float:
        """计算对话深度"""
        depth = 0
        current_depth = 0
        for msg in messages:
            if msg['is_user']:
                current_depth += 1
                depth = max(depth, current_depth)
            else:
                current_depth = max(0, current_depth - 1)
        return depth

    def _calculate_term_frequency(self, term: str) -> float:
        """计算称呼使用频率"""
        total_messages = len(self.messages)
        term_count = sum(1 for msg in self.messages if term in msg['content'])
        return term_count / total_messages if total_messages > 0 else 0

    def _analyze_term_adoption(self, term: Dict[str, Any]) -> Dict[str, Any]:
        """分析称呼采用模式"""
        return {
            'initial_usage': self._analyze_initial_usage(term),
            'adoption_speed': self._analyze_adoption_speed(term),
            'usage_consistency': self._analyze_usage_consistency(term)
        }

    def _analyze_topic_depth(self, topic: Dict[str, Any]) -> int:
        """分析话题深度"""
        related_messages = [msg for msg in self.messages 
                          if abs((msg['timestamp'] - topic['timestamp']).total_seconds()) < 3600]
        return len(related_messages)

    def _analyze_discussion_pattern(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析讨论模式"""
        return {
            'initiation': self._analyze_topic_initiation(topic),
            'development': self._analyze_topic_development(topic),
            'conclusion': self._analyze_topic_conclusion(topic)
        }

    def _analyze_follow_up_impact(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析后续影响"""
        return {
            'immediate_impact': self._analyze_immediate_impact(topic),
            'long_term_impact': self._analyze_long_term_impact(topic['timestamp'])
        }

    def _analyze_initial_usage(self, term: Dict[str, Any]) -> Dict[str, Any]:
        """分析称呼初始使用"""
        return {
            'first_use': term['first_occurrence'],
            'usage_frequency': self._calculate_term_frequency(term['term'])
        }

    def _analyze_adoption_speed(self, term: Dict[str, Any]) -> Dict[str, Any]:
        """分析称呼采用速度"""
        return {
            'adoption_speed': self._calculate_term_frequency(term['term'])
        }

    def _analyze_usage_consistency(self, term: Dict[str, Any]) -> Dict[str, Any]:
        """分析称呼使用一致性"""
        return {
            'usage_consistency': self._calculate_term_frequency(term['term'])
        }

    def _analyze_topic_initiation(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析话题发起"""
        return {
            'initiation_pattern': self._analyze_discussion_pattern(topic)
        }

    def _analyze_topic_development(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析话题发展"""
        return {
            'topic_development': self._calculate_topic_diversity(
                [msg for msg in self.messages if abs((msg['timestamp'] - topic['timestamp']).total_seconds()) < 3600]
            )
        }

    def _analyze_topic_conclusion(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析话题结论"""
        return {
            'conclusion_pattern': self._calculate_emotional_intensity(
                [msg for msg in self.messages if abs((msg['timestamp'] - topic['timestamp']).total_seconds()) < 3600]
            )
        }

    def _analyze_immediate_impact(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """分析直接影响"""
        return {
            'immediate_impact': self._calculate_emotional_intensity(
                [msg for msg in self.messages if abs((msg['timestamp'] - topic['timestamp']).total_seconds()) < 3600]
            )
        }

    def _analyze_long_term_impact(self, date: datetime) -> Dict[str, Any]:
        """分析长期影响"""
        return {
            'long_term_impact': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_preparation_pattern(self, date: datetime) -> Dict[str, Any]:
        """分析准备模式"""
        return {
            'preparation_pattern': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_celebration_pattern(self, date: datetime) -> Dict[str, Any]:
        """分析庆祝模式"""
        return {
            'celebration_pattern': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_aftermath_impact(self, date: datetime) -> Dict[str, Any]:
        """分析后续影响"""
        return {
            'aftermath_impact': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] > date]
            )
        }

    def _analyze_gift_pattern(self, date: datetime) -> Dict[str, Any]:
        """分析礼物模式"""
        return {
            'gift_pattern': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_cultural_significance(self, date: datetime) -> Dict[str, Any]:
        """分析文化意义"""
        return {
            'cultural_significance': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_preparation_behavior(self, date: datetime) -> Dict[str, Any]:
        """分析准备行为"""
        return {
            'preparation_behavior': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_celebration_quality(self, date: datetime) -> Dict[str, Any]:
        """分析庆祝质量"""
        return {
            'celebration_quality': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_aftermath_effect(self, date: datetime) -> Dict[str, Any]:
        """分析后续效果"""
        return {
            'aftermath_effect': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] > date]
            )
        }

    def _analyze_conflict_resolution(self, date: datetime) -> Dict[str, Any]:
        """分析冲突解决"""
        return {
            'resolution_time': self._calculate_avg_response_time(
                [msg for msg in self.messages if msg['timestamp'] <= date]
            )
        }

    def _analyze_recovery_pattern(self, date: datetime) -> Dict[str, Any]:
        """分析恢复模式"""
        return {
            'recovery_pattern': self._calculate_emotional_intensity(
                [msg for msg in self.messages if msg['timestamp'] > date]
            )
        }

    def _calculate_recovery_time(self, date: datetime) -> Dict[str, Any]:
        """计算恢复时间"""
        return {
            'recovery_time': self._calculate_avg_response_time(
                [msg for msg in self.messages if msg['timestamp'] > date]
            )
        }

    def _get_messages_in_period(self, date):
        return [msg for msg in self.messages if date <= msg['timestamp'] <= date + timedelta(days=1)]

    def _calculate_sentiment(self, messages):
        positive_keywords = ['喜欢', '爱', '开心', '高兴', '幸福', '好']
        negative_keywords = ['讨厌', '生气', '难过', '伤心', '不好', '烦']
        
        sentiment_score = 0
        for msg in messages:
            content = msg['content']
            for keyword in positive_keywords:
                if keyword in content:
                    sentiment_score += 1
            for keyword in negative_keywords:
                if keyword in content:
                    sentiment_score -= 1
        
        return sentiment_score / len(messages) if messages else 0

    def _extract_key_messages(self, messages):
        return [msg['content'] for msg in messages if msg['is_user']]

    def _analyze_active_hours(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析活跃时间段"""
        hour_counts = [0] * 24
        for msg in messages:
            hour = msg['timestamp'].hour
            hour_counts[hour] += 1
        
        # 计算最活跃的时段
        max_hour = hour_counts.index(max(hour_counts))
        active_hours = [i for i, count in enumerate(hour_counts) if count > sum(hour_counts) / 24]
        
        return {
            'most_active_hour': max_hour,
            'active_hours': active_hours,
            'morning_activity': sum(hour_counts[6:12]) / sum(hour_counts) if sum(hour_counts) > 0 else 0,
            'afternoon_activity': sum(hour_counts[12:18]) / sum(hour_counts) if sum(hour_counts) > 0 else 0,
            'evening_activity': sum(hour_counts[18:24]) / sum(hour_counts) if sum(hour_counts) > 0 else 0,
            'night_activity': sum(hour_counts[0:6]) / sum(hour_counts) if sum(hour_counts) > 0 else 0
        }

    def _analyze_message_style(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析消息风格"""
        # 表情符号分析
        emoji_patterns = {
            'happy': ['😊', '😄', '😂', '😍', '😘'],
            'sad': ['😢', '😭', '😔', '😞'],
            'angry': ['😠', '😡', '😤'],
            'neutral': ['😐', '🙂', '😶']
        }
        
        # 标点符号分析
        punctuation_patterns = {
            'exclamation': ['!', '！'],
            'question': ['?', '？'],
            'ellipsis': ['...', '…'],
            'period': ['.', '。']
        }
        
        def count_patterns(text, patterns):
            return {key: sum(1 for p in patterns[key] if p in text) for key in patterns}
        
        # 消息类型分析
        def analyze_message_types(messages):
            types = {
                'text_only': 0,
                'with_emoji': 0,
                'with_image': 0,
                'with_link': 0,
                'with_voice': 0
            }
            
            for msg in messages:
                content = msg['content']
                if 'http' in content:
                    types['with_link'] += 1
                elif '[图片]' in content:
                    types['with_image'] += 1
                elif '[语音]' in content:
                    types['with_voice'] += 1
                elif any(emoji in content for emoji_list in emoji_patterns.values() for emoji in emoji_list):
                    types['with_emoji'] += 1
                else:
                    types['text_only'] += 1
            
            total = sum(types.values())
            return {k: v/total if total > 0 else 0 for k, v in types.items()}
        
        # 分析所有消息
        all_content = ' '.join(msg['content'] for msg in messages)
        
        return {
            'emoji_usage': count_patterns(all_content, emoji_patterns),
            'punctuation_usage': count_patterns(all_content, punctuation_patterns),
            'message_types': analyze_message_types(messages),
            'avg_words_per_message': len(all_content.split()) / len(messages) if messages else 0,
            'unique_words_ratio': len(set(all_content.split())) / len(all_content.split()) if all_content else 0
        }