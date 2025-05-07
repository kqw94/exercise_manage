# 题库后台管理系统

## TODO LIST

1. 后续功能开发
   
   1. 不同格式的导入导出，涉及到pdf，markdown，图片到json的转换  
   
   2. 用户行为日志 前端展示
   
   3. 快捷键
      
      1. 回车确认

2. 日志系统接入

3. 部署配置文件 

4. 代码清扫包括 接口函数合并，性能改进

5. 功能测试 和 性能测试（压力测试）     

## ISSUE

1. 长时间挂着，会refresh unauthorized， 导致其他请求失效![](C:\Users\qingwen\AppData\Roaming\marktext\images\2025-04-09-18-13-58-image.png)

2. chrome 页面内存不断增长问题

3. Exercise接口

|        | 单个                                     | 批量                                             |
|:------ |:--------------------------------------:|:----------------------------------------------:|
| GET    | ExerciseList -> ExerciseSerializer     | ExerciseList -> ExerciseSerializer             |
| POST   | ExerciseWrite->ExerciseWriteSerializer | BulkExerciseWrite->BulkExerciseWriteSerializer |
| PUT    | ExerciseWrite->ExerciseWriteSerializer | BulkExerciseWrite->BulkExerciseWriteSerializer |
| DELETE | ExerciseList                           | BulkExerciseWrite                              |

post/put 单个/批量 合并，都用ExerciseWriteSerializer和ExerciseWrite

4. 批量编辑页面 删除功能

5. 增加根据 题目答案对比 筛选题目功能

6. 用fasttext和faiss去一遍重

7. 所有void main 改成 int main 并在 最后加上 return 0;

8. 清理所有表格，代码，图片的格式问题

9. 有些问题中在编辑模式显示错误