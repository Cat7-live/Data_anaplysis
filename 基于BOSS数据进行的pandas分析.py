import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, WordCloud, Boxplot, Map
import re
from collections import Counter

# r_df = pd.read_excel(r"D:\excel_sample\BOSS直聘数据分析师职位.xlsx")
pd.set_option('display.width', 300)  # 设置字符显示宽度
pd.set_option('display.max_rows', None)  # 设置显示最大行
pd.set_option('display.max_columns', None)


# df.dropna(axis=0,how='any',inplace=True)
# print(df.head(5))
# print(df.info())
# print(r_df.shape)


class DataCleaning:
    def __init__(self, df_file):
        self.df = pd.read_excel(df_file)

    def salary_process(self, salary):
        if isinstance(salary, str):
            if "元/时" in salary:
                hour_str_list = re.findall(r'(\d+\.?\d*)', salary.split('-')[0].split('~')[0])
                hour = float(hour_str_list[0]) * 8 * 30 / 1000  # 转换为千元单位
                return round(hour, 2)
            elif "元/天" in salary:
                day_str_list = re.findall(r'(\d+\.?\d*)', salary.split('-')[0].split('~')[0])
                day = float(day_str_list[0]) * 30 / 1000
                return round(day, 2)
            elif "K" in salary or "k" in salary:
                month_str_list = re.findall(r'(\d+\.?\d*)', salary.split('-')[0].split('~')[0])
                month = float(month_str_list[0])
                if "薪" in salary:
                    months = float(re.findall(r'(\d+)薪', salary)[0])
                    return round(month * months / 12, 2)
                return round(month, 2)
        else:
            try:
                return float(re.findall(r'(\d+\.?\d*)', salary)[0] / 1000)
            except TypeError:
                return 0

    def extract_distinct(self, location):
        if isinstance(location, str):
            if '上海' in location:
                distinct = location.split('·')
                if len(distinct) > 1:
                    return distinct[1]
            else:
                part = location.split("·")
                if len(part) > 1:
                    return part[1] + "(其他)"
        else:
            return '类型错误'

    def firm_type_process(self, types):  # 简化分类行业
        self.df['公司类型'] = self.df['公司类型'].fillna('其他')
        category_map = {
            '互联网': ['互联网', 'IT', '科技', '大数据'],
            '电子商务': ['电子商务', '电商', '跨境'],
            '游戏': ['游戏', '手游', '网游', '页游'],
            '金融': ['金融', '银行', '证券', '保险', '基金', '股票'],
            '咨询': ['咨询', '顾问', '管理咨询'],
            '医疗': ['医疗', '医药', '健康', '医院'],
            '食品': ['食品', '饮料', '餐饮']}
        # low_type = type.str().lower()  # 统一小写，避免大小写问题
        for category, keywords in category_map.items():
            if any(keyword in types for keyword in keywords):
                return category  # 返回公司类型对应分类行业
        return types  # 未匹配任何关键词的返回"其他"

    def exp_process(self, exp):
        # 对要求经验进行分类
        if isinstance(exp, str):
            if exp in ['经验不限', '在校/应届', '1天/周', '5天/周', '3天/周', '4天/周']:
                return '经验不限/应届/在校'
            else:
                return exp
        else:
            print("非str类型")

    def deal(self):
        self.df['薪资月薪(K)'] = self.df['薪资范围'].apply(self.salary_process)
        self.df['经验要求分类'] = self.df['经验要求'].apply(self.exp_process)
        self.df['公司类型'] = self.df['公司类型'].apply(self.firm_type_process)
        self.df['区域'] = self.df['地区'].apply(self.extract_distinct)
        print(f'数据清洗后的结果:{self.df.head(3)}')
        # return self.df


class DataAnalysis(DataCleaning):

    def edu_salary(self):
        edu_df = self.df[self.df['学历要求'].isin(['本科', '硕士', '大专'])]
        edu_exp_salary = edu_df.groupby(['学历要求', '经验要求分类'])['薪资月薪(K)'].mean().unstack()
        bar1 = (
            Bar()
            .add_xaxis(edu_exp_salary.index.tolist())
            # .add_yaxis("1年以内经验", edu_exp_salary['1年以内'].round(1).tolist())
            .add_yaxis("1-3年经验", edu_exp_salary['1-3年'].round(1).tolist())
            .add_yaxis("3-5年经验", edu_exp_salary['3-5年'].round(1).tolist())
            .add_yaxis("5-10年经验", edu_exp_salary['5-10年'].round(1).tolist())
            # .add_yaxis('10年以上经验', edu_exp_salary['10年以上'].round(1).tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="不同学历和经验组合的平均薪资"),
                yaxis_opts=opts.AxisOpts(name="薪资(千元)")
            ))
        output_path = "edu_salary.html"  # 定义输出路径
        bar1.render(output_path)  # 生成 HTML 文件
        print(f"图表已生成，文件路径：{output_path}")
        master_avg = edu_df[edu_df['学历要求'] == '硕士']['薪资月薪(K)'].mean()
        bachelor_avg = edu_df[edu_df['学历要求'] == '本科']['薪资月薪(K)'].mean()
        junior_avg = edu_df[edu_df['学历要求'] == '大专']['薪资月薪(K)'].mean()
        print(f"不同学历平均薪资对比:")
        print(f"硕士平均薪资: {master_avg:.1f}k, 本科平均薪资: {bachelor_avg:.1f}k,大专平均薪资: {junior_avg:.1f}k")
        print(f"硕士比本科高: {(master_avg - bachelor_avg):.1f}k ({(master_avg / bachelor_avg - 1) * 100:.1f}%)")
        print(f"本科比大专高: {(bachelor_avg - junior_avg):.1f}k ({(bachelor_avg / junior_avg - 1) * 100:.1f}%)")

    def industry_salary(self):
        indu_salary = (self.df.groupby('公司类型')['薪资月薪(K)'].agg(['mean', 'median', 'count'])
                       .sort_values('mean', ascending=False))
        indu_salary = indu_salary[indu_salary['count'] >= 5]
        bar2 = (
            Bar().add_xaxis(indu_salary.index.tolist())
            .add_yaxis('薪资月薪(K)', indu_salary['mean'].round(1).tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="不同行业数据分析师平均薪资"),
                yaxis_opts=opts.AxisOpts(name="薪资(千元)"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45))))
        output_path = "industry_salary.html"  # 定义输出路径
        bar2.render(output_path)  # 生成 HTML 文件
        print(f"图表已生成，文件路径：{output_path}")

    def exp_salary(self):
        # exp_levels = ['经验不限/应届/在校','1年以内', '1-3年', '3-5年', '5-10年']
        exp_levels = self.df['经验要求分类'].unique().tolist()[0:5]
        iqr_list = []
        for level in exp_levels:
            salary_data = self.df[self.df['经验要求分类'] == level]['薪资月薪(K)']
            q1 = salary_data.quantile(0.25)
            q3 = salary_data.quantile(0.75)
            IQR = q1 - q3
            iqr_list.append({'经验要求': level, 'Q1': round(q1, 2), 'Q3': round(q3, 2), 'IQR': round(IQR, 2)})
        iqr_results = pd.DataFrame(iqr_list)
        print("不同经验要求的薪资四分位距分析:")
        print(iqr_results)
        data = [self.df[self.df['经验要求分类'] == level]['薪资月薪(K)'].tolist() for level in exp_levels]
        boxplot = (Boxplot()
        .add_xaxis(exp_levels)
        .add_yaxis('薪资分布', Boxplot.prepare_data(data))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="不同经验要求的薪资分布"),
            yaxis_opts=opts.AxisOpts(name="薪资(千元)"))
        )
        output_path = "experience_salary.html"  # 定义输出路径
        boxplot.render(output_path)  # 生成 HTML 文件
        print(f"图表已生成，文件路径：{output_path}")

    def word_cloud(self):
        tags = self.df[[f'标签{i}' for i in range(1, 6)]].stack().dropna().tolist()  # stack 列明变为二级索引
        tag_count = Counter(tags)
        wordcloud_data = [(word, count) for word, count in tag_count.most_common(50) if len(word) > 1]
        wordcloud = (WordCloud()
                     .add(series_name='技能需求'
                          , data_pair=wordcloud_data
                          , word_size_range=[12, 55]
                          , textstyle_opts=opts.TextStyleOpts(font_family="SimHei"))
                     .set_global_opts(title_opts=opts.TitleOpts(title='数据分析师技能需求词云')
                                      , tooltip_opts=opts.TooltipOpts(is_show=True)
                                      , visualmap_opts=opts.VisualMapOpts(
                min_=min(count for _, count in wordcloud_data),
                max_=max(count for _, count in wordcloud_data),
                orient="horizontal",  # 水平显示
                pos_bottom="10%")))
        output_path = "wordcloud.html"  # 定义输出路径
        wordcloud.render(output_path)  # 生成 HTML 文件
        print(f"图表已生成，文件路径：{output_path}")
        print("Top 10 技能需求:")
        for word, count in tag_count.most_common(10):
            print(f"{word}: {count}次")

    def map(self):
        distinct_states = self.df.groupby("区域")['薪资月薪(K)'].agg(['mean', 'count']).sort_values('count',
                                                                                                    ascending=False)
        # main_distinct = distinct_states[distinct_states["count"]>=5]
        main_distinct_dict = distinct_states['mean'].round(2).to_dict()
        map_data = [(k, v) for k, v in main_distinct_dict.items()]
        district_map = (
            Map(init_opts=opts.InitOpts(width="1200px", height="800px"))
            .add("平均薪资(千元)", map_data, "上海", is_roam=True)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="上海各区数据分析师平均薪资"),
                visualmap_opts=opts.VisualMapOpts(max_=30),
            )
        )
        output_path = "map.html"  # 输出路径
        district_map.render(output_path)  # 生成 HTML 文件
        print(f"图表已生成，文件路径：{output_path}")

    def pie(self):

        position_count = self.df.groupby('区域')['职位'].count().sort_values(ascending=False)
        position_count_dict = position_count.to_dict()
        pie_data = [(k, v) for k, v in position_count_dict.items()]
        position_pie = (Pie(init_opts=opts.InitOpts(width="1600px", height="800px", theme="white"))
        .add(series_name='职务数量'
             , data_pair=pie_data
             , radius=['30%', '50%']
             , is_clockwise=True
             , label_opts=opts.LabelOpts(position='outside')
             , itemstyle_opts=opts.ItemStyleOpts(border_width=1, border_color="#fff"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title='上海各区域职务分布', subtitle='数据来源：BOSS直聘')
            , legend_opts=opts.LegendOpts(pos_bottom='3%', orient='horizontal')))
        output_path = "pie.html"  # 定义输出路径
        position_pie.render(output_path)  # 生成 HTML 文件
        print(f"图表已生成，文件路径：{output_path}")


if __name__ == '__main__':
    item = DataAnalysis(r"D:\excel_sample\BOSS直聘数据分析师职位.xlsx")
    item.deal()
    item.edu_salary()
    item.exp_salary()
    item.industry_salary()
    item.word_cloud()
    item.map()
    item.pie()
