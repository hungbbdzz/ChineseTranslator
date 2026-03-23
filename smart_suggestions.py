# smart_suggestions.py
import re

# Practical context database with 10 different categories
CORPUS = {
    "greeting": [
        "你好吗", "最近怎么样", "很高兴认识你", "好久不见", "早上好", "晚上好",
        "吃了吗", "你在干什么", "周末愉快", "你好"
    ],
    "shopping": [
        "多少钱", "太贵了", "可以便宜点吗", "我要这个", "有其他颜色吗", "能试穿吗",
        "给我发票", "可以刷卡吗", "怎么卖", "这个多少钱"
    ],
    "dining": [
        "服务员", "点菜", "买单", "结账", "有中文菜单吗", "这个很辣吗", "我吃素",
        "干杯", "再来一杯", "很好吃", "打包", "我要点菜"
    ],
    "transport": [
        "去机场", "去火车站", "请在这个地址停", "到这里要多久", "请打表", "迷路了",
        "怎么走", "车票多少钱", "在哪里下车", "去哪里"
    ],
    "hotel": [
        "我要退房", "含早餐吗", "能存行李吗", "请帮我叫辆车", "可以换房间吗", 
        "房间没有热水", "密码是多少", "有空房吗", "我要订房"
    ],
    "emergency": [
        "救命", "帮帮我", "我需要去医院", "我的护照丢了", "请报警", "哪里有药店",
        "我不舒服", "请叫救护车"
    ],
    "work": [
        "请发邮件给我", "我们开个会", "合同准备好了吗", "明天见", "很高兴和您合作", 
        "这份文件需要签字", "什么时候交", "辛苦了", "我发给你"
    ],
    "directions": [
        "洗手间在哪", "地铁站怎么走", "离这里远吗", "请在地图上指给我看", "附近有超市吗",
        "一直走", "往左拐", "往右拐", "在哪里"
    ],
    "time_weather": [
        "现在几点了", "今天星期几", "明天气温多少", "什么时候开始", "太晚了", "还要等多久",
        "今天天气真好", "会下雨吗", "明天见"
    ],
    "small_talk": [
        "你喜欢做什么", "我喜欢看电影", "听音乐", "打篮球", "看书", "去旅游",
        "我觉得很好", "你觉得呢", "我同意", "我也是"
    ]
}

def get_contextual_suggestions(text):
    text = text.strip()
    if not text:
        return []
        
    suggestions = []
    seen = set()
    
    def add_suggestion(display, append_txt):
        if append_txt not in seen:
            suggestions.append((display, append_txt))
            seen.add(append_txt)
            
    # 1. Exact prefix match (Highest priority)
    # Check if the entire input is the prefix of any sentence
    for ctx, sentences in CORPUS.items():
        for sentence in sentences:
            if sentence.startswith(text) and sentence != text:
                remainder = sentence[len(text):]
                add_suggestion("+" + remainder, remainder)
                
    if len(suggestions) >= 7:
        return suggestions[:7]
        
    # 2. Local context completion (Last N characters)
    # e.g., if user types "我觉得太贵", text[-2:] = "太贵", find "太贵了" -> append "了"
    max_suffix_len = min(len(text), 4)
    for length in range(max_suffix_len, 0, -1):
        suffix = text[-length:]
        for ctx, sentences in CORPUS.items():
            for sentence in sentences:
                idx = sentence.find(suffix)
                if idx != -1:
                    remainder = sentence[idx + length:]
                    if remainder:
                        add_suggestion("+" + remainder, remainder)
                        if len(suggestions) >= 7:
                            return suggestions[:7]
                            
    # 3. Fallback to dictionary for the last character if we still have room
    if len(suggestions) < 7:
        last_char = text[-1]
        if '\u4e00' <= last_char <= '\u9fff':
            try:
                from dict_data import get_common_words
                words = get_common_words(last_char)
                if words:
                    for w in words:
                        word = w[0]
                        # Only suggest if it actually starts with the char
                        if word.startswith(last_char) and len(word) > 1:
                            remainder = word[1:]
                            add_suggestion("+" + remainder, remainder)
                            if len(suggestions) >= 7:
                                break
            except ImportError:
                pass
                
    return suggestions[:7]
