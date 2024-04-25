# DBテーブル設計
## HumanResponses テーブル

このテーブルは、面接で想定される質問に対して、想定される人間(面接される人)の回答を保存します。

| フィールド名        | データ型 | 説明                             | 制約       |例|
|-------------------|---------|--------------------------------|-----------|---|
| response_id       | INT     | レスポンスの一意識別子             | 主キー     | 1|
| expected_response | TEXT    | 期待される回答                   |            | "業務効率化システムの開発リーダーを務めました"|

## AIFollowUpQuestions テーブル

このテーブルは、`HumanResponses` テーブルの各エントリに対する AI による深掘り質問を保存します。

| フィールド名         | データ型 | 説明                                 | 制約                   | 例　|
|--------------------|---------|------------------------------------|-----------------------|---|
| follow_up_id       | INT     | フォローアップ質問の一意識別子       | 主キー                 | 1
| response_id        | INT     | 対応するレスポンスの ID              | 外部キー (HumanResponses) | 1
| follow_up_question | TEXT    | AI が提案する追加の深掘り質問         |                     | "そのプロジェクトで直面した最大の課題は何でしたか？"|

## relationship
HumanResponses : AIFollowUpQuestions = 1 : 多

# DBへのデータ注入
http://0.0.0.0:8000/docs
↑にてtry it outでPOSTのAPIを叩いてデータを注入できる

サンプルリクエストボディ
```json
{
  "expected_response": "業務効率化システムの開発リーダーを務めました",
  "follow_up_questions": [
        {"follow_up_question": "そのプロジェクトで直面した最大の課題は何でしたか？"},
        {"follow_up_question": "何人規模の開発ですか"}
    ]
}
```


