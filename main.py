import os
from chat_analyzer.data_processor import ChatDataProcessor
from chat_analyzer.sentiment_analyzer import SentimentAnalyzer
from chat_analyzer.conversation_analyzer import ConversationAnalyzer
from chat_analyzer.visualizer import ChatVisualizer
from chat_analyzer.key_moments_analyzer import KeyMomentsAnalyzer
import json
import argparse

def analyze_chat(file_path: str, user_name: str, output_dir: str = "analysis_results"):
    """分析聊天记录的主函数"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化各个模块
    data_processor = ChatDataProcessor(file_path, user_name)
    sentiment_analyzer = SentimentAnalyzer()
    conversation_analyzer = ConversationAnalyzer(user_name)
    key_moments_analyzer = KeyMomentsAnalyzer(file_path, user_name)
    visualizer = ChatVisualizer()
    
    # 处理数据
    print("正在处理聊天记录...")
    df = data_processor.parse_chat_file()
    df = data_processor.calculate_response_time(df)
    
    # 对话分析
    print("正在进行对话分析...")
    conversation_analysis = conversation_analyzer.analyze_conversation(df)
    
    # 获取重要讨论
    key_discussions = conversation_analyzer.get_key_discussions(conversation_analysis['analyzed_groups'])
    
    # 计算参与度指标
    engagement_metrics = conversation_analyzer.calculate_engagement_metrics(df)
    
    # 分析关键时间节点和标志性话题
    print("分析关键时间节点和标志性话题...")
    # 将 analyzed_groups 转换为正确的消息格式
    messages = []
    for group in conversation_analysis['analyzed_groups']:
        for msg in group['messages']:
            messages.append({
                'timestamp': msg['timestamp'],
                'content': msg['content'],
                'sender': msg['sender'],
                'is_user': msg['sender'] == user_name
            })
    key_moments_analyzer.extract_landmark_topics(messages)
    key_moments_analyzer.save_results(output_dir)
    
    # 生成可视化
    print("正在生成可视化结果...")
    visualizer.plot_engagement_scores(
        {'user_score': sum(g['analysis']['depth'] for g in conversation_analysis['analyzed_groups'] 
                          if g['messages'][0]['sender'] == user_name),
         'partner_score': sum(g['analysis']['depth'] for g in conversation_analysis['analyzed_groups'] 
                            if g['messages'][0]['sender'] != user_name)},
        os.path.join(output_dir, 'engagement_scores.png')
    )
    
    visualizer.plot_response_time_distribution(
        df,
        os.path.join(output_dir, 'response_time_distribution.png')
    )
    
    visualizer.plot_daily_activity(
        engagement_metrics['daily_messages'],
        os.path.join(output_dir, 'daily_activity.png')
    )
    
    visualizer.plot_hourly_activity(
        engagement_metrics['hourly_messages'],
        os.path.join(output_dir, 'hourly_activity.png')
    )
    
    # 生成总结报告
    print("正在生成总结报告...")
    analysis_results = {
        'response_patterns': conversation_analysis['response_patterns'],
        'topic_initiation': conversation_analysis['topic_initiation'],
        'key_discussions': key_discussions,
        'engagement_metrics': engagement_metrics,
        'conversation_analysis': conversation_analysis
    }
    
    report = visualizer.generate_summary_report(
        analysis_results,
        os.path.join(output_dir, 'summary_report.txt')
    )
    
    print("\n分析完成！结果已保存到", output_dir)
    return report

def process_chat_records(file_path):
    """处理本地聊天记录文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None

def main():
    # 从本地文件读取聊天记录
    file_path = input("请输入聊天记录文件的路径: ")
    chat_content = process_chat_records(file_path)
    
    if chat_content is None:
        print("无法读取聊天记录文件")
        return
        
    parser = argparse.ArgumentParser(description='分析微信聊天记录')
    parser.add_argument('chat_file', help='聊天记录文件路径')
    parser.add_argument('partner_name', help='对话伙伴的微信昵称')
    parser.add_argument('--output-dir', default='analysis_results', help='输出目录')
    parser.add_argument('--key-dates', help='关键时间节点配置文件路径')
    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 初始化数据处理器
    data_processor = ChatDataProcessor(args.chat_file, args.partner_name)
    
    # 处理聊天记录
    print("正在处理聊天记录...")
    df = data_processor.parse_chat_file()
    df = data_processor.calculate_response_time(df)

    # 初始化分析器
    analyzer = ConversationAnalyzer(args.partner_name)
    key_moments_analyzer = KeyMomentsAnalyzer(args.chat_file, args.partner_name, args.partner_name)

    # 如果有提供关键时间节点配置文件，则加载
    if args.key_dates and os.path.exists(args.key_dates):
        with open(args.key_dates, 'r', encoding='utf-8') as f:
            key_dates_config = json.load(f)
            
            # 处理关系开始日期
            if 'relationship_start' in key_dates_config:
                key_moments_analyzer.set_key_date(
                    'relationship_start',
                    key_dates_config['relationship_start']['date'],
                    key_dates_config['relationship_start'].get('description', '')
                )
            
            # 处理冲突日期
            if 'conflicts' in key_dates_config:
                for conflict in key_dates_config['conflicts']:
                    key_moments_analyzer.set_key_date(
                        'conflict',
                        conflict['date'],
                        conflict.get('description', '')
                    )
            
            # 处理特殊日期
            if 'special_days' in key_dates_config:
                special_days = key_dates_config['special_days']
                # 处理纪念日
                if 'anniversary' in special_days:
                    key_moments_analyzer.set_key_date(
                        'anniversary',
                        special_days['anniversary']['date'],
                        special_days['anniversary'].get('description', '')
                    )
                # 处理情人节
                if 'valentine' in special_days:
                    for valentine in special_days['valentine']:
                        key_moments_analyzer.set_key_date(
                            'valentine',
                            valentine['date'],
                            valentine.get('description', '')
                        )
                # 处理七夕节
                if 'qixi' in special_days:
                    for qixi in special_days['qixi']:
                        key_moments_analyzer.set_key_date(
                            'qixi',
                            qixi['date'],
                            qixi.get('description', '')
                        )

    # 分析对话
    print("开始分析对话...")
    conversation_analysis = analyzer.analyze_conversation(df)

    # 分析关键时间节点和标志性话题
    print("分析关键时间节点和标志性话题...")
    # 将 analyzed_groups 转换为正确的消息格式
    messages = []
    for group in conversation_analysis['analyzed_groups']:
        for msg in group['messages']:
            messages.append({
                'timestamp': msg['timestamp'],
                'content': msg['content'],
                'sender': msg['sender'],
                'is_user': msg['sender'] == args.partner_name
            })
    key_moments_analyzer.extract_landmark_topics(messages)
    key_moments_analyzer.save_results(args.output_dir)

    print(f"分析完成！结果已保存到 {args.output_dir} 目录")

if __name__ == '__main__':
    main()