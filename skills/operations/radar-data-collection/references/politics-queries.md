# 国际政治搜索 Query 参考

## 分区域链路

### 亚太
- `Asia Pacific political news today`
- `China Taiwan South China Sea military latest`
- `Japan Korea Southeast Asia diplomatic news`

### 中东·欧洲
- `Middle East Europe geopolitical news today`
- `Russia Ukraine war latest update`
- `NATO Middle East conflict latest`

### 美洲
- `Americas Latin America political news today`
- `US China trade tariffs latest`
- `Brazil Argentina South America policy`

## 采集规范
- 来源优先：Reuters / AP / AFP / Al Jazeera / BBC / FT / Bloomberg
- 每条必须有 URL，无 URL 丢弃
- 频道页/目录页必须下钻到具体事件稿
- 目标条数：10~12 条（亚太 4 / 中东·欧洲 4 / 美洲 3）

## 内容结构（入库 content 字段）
```
中文标题：xxx
English Headline: xxx
事件介绍：xxx
背景/影响：xxx
```
