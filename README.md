# SQLAlchemy Learning

## 概要

SQLAlchemy のラーニング用リポジトリです。
([SQLAlchemy](https://docs.sqlalchemy.org/en/20/index.html))

VSCode + pytest により画面ポチポチで動かしながら動作を確認していく仕組みです。

## 検証環境

- **検証環境**: Ubuntu 23.04
- **Python**: Python 3.11
- **SQLAlchemy**: SQLAlchemy 2.0
- **パッケージ管理**: Poetry
- **データベース**: MySQL 8.0
- **データベース動作環境**: Docker
- **環境変数管理**: direnv
- **プログラム実行環境**: VSCode + pytest

## 使い方

### 事前準備

- 検証環境に書かれているツール類を用意する
- データベースを起動する

#### データベースに docker を使う場合

データベースに docker を使う場合の起動用サンプルコマンド。

```bash
docker run --name db-sqlalchemy-learning    \
    -e MYSQL_ROOT_PASSWORD=rootpassword     \
    -e MYSQL_PASSWORD=testpassword          \
    -e MYSQL_USER=testuser                  \
    -e MYSQL_DATABASE=testdb                \
    -p 3306:3306                            \
    -d mysql:8.0
```

### 環境変数の読み込み

`.envrc.sample` をベースに `.envrc` を作成してデータベースへの接続情報を記載します。
保存後にターミナルを操作し direnv により環境変数が読み込まれたことを確認します。

### 仮想環境の作成とパッケージインストール

パッケージをインストールし仮想環境を作成します。

```bash
poetry install
```

仮想環境を作成したことを確認します。

```bash
poetry env info
```

### VSCode の起動

ターミナルから **環境変数が読み込まれた状態** で VSCode を起動します。
この方法で VSCode に環境変数が読み込まれます。

### データベースとの疎通確認

- `src/db.py` を開きます
- `test_db_connecting()` を実行します

pytest によるテストコードの実行方法については VSCode のマニュアルを参照してください。
([Python testing in Visual Studio Code](https://code.visualstudio.com/docs/python/testing))

#### サイドバーに テスト が出てこない場合

仮想環境が設定されていない可能性がありますので VSCode のマニュアルを参考に Interpreter を設定してください。
([Working with Python interpreters](https://code.visualstudio.com/docs/python/environments#_working-with-python-interpreters))

### Seeder による検証用データのインサート

- `src/seeder.py` を開きます
- `test_seeder()` を実行します

#### 注意事項

- テーブルを drop / create するためデータはリセットします
- インサートするデータは faker にて生成するためランダムになります

### テストコードの実行

任意のファイルから疎通確認と同じ方法でテストコードを実行します。

#### 注意事項

setup/teardown によるデータのリセットなどは実装していません。
このため update や delete の動作検証後は他のテストケースがエラーとなる場合があります。
このような場合には seeder を再実行してデータをリセットしてください。

## データベースのテーブル設計

<img width="800" src="https://raw.githubusercontent.com/yoshik159753/sqlalchemy-learning/main/docs/database-table-design/er-diagram.png" alt="テーブル定義"> 

## ディレクトリ構成

```txt
./sqlalchemy-learning
|-- LICENSE
|-- README.md
|-- poetry.lock
|-- pyproject.toml
`-- src
    |-- 01_base_crud.py
    |-- 02_where_tips.py
    |-- 03_select_tips.py
    |-- 04_relationships_tips.py
    |-- 05_other_tips.py
    |-- db.py
    |-- models.py
    `-- seeder.py
```

- `src/01_base_crud.py`: CRUD の基本ケースです
- `src/02_where_tips.py`: where で使用する and, or, not, exists などについてです
- `src/03_select_tips.py`: select で使用する one, all, scalars, orderby, groupby, join, case などについてです
- `src/04_relationships_tips.py`: SQLAlchemy のリレーション(リレーションによる join, 各種 eager load など)についてです
- `src/05_other_tips.py`: その他の upsert, session について, 悲観/楽観的ロック などについてです
- `src/db.py`: データベースへの接続です
- `src/models.py`: 検証用のモデル群です
- `src/seeder.py`: 検証用のデータをインサートする seeder です
