import pytest
from src.graph import (
    parse_inline_foreign_keys,
    sql_to_graph,
    get_sub_graph,
    graph_to_sql,
    parse_not_null_constraints,
    parse_check_constraints,
    parse_unique_constraints,
    parse_primary_keys,
    parse_foreign_key_constraints
)

def test_parse_inline_foreign_keys():
    sql_statements = [
        "CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE enrollment (student_id INT NOT NULL REFERENCES student(id), course_id INT NOT NULL REFERENCES course(id));",
    ]

    expected_inline_foreign_keys = {
        "enrollment": [
            {
                "parent_column": "student_id",
                "parent_datatype": "INT",
                "ref_table": "student",
                "ref_column": "id",
            },
            {
                "parent_column": "course_id",
                "parent_datatype": "INT",
                "ref_table": "course",
                "ref_column": "id",
            },
        ]
    }

    result = parse_inline_foreign_keys(sql_statements)
    print(result)
    assert result == expected_inline_foreign_keys


def test_sql_to_graph():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE enrollment (student_id INT NOT NULL REFERENCES student(id), course_id INT NOT NULL REFERENCES course(id));
    """

    G = sql_to_graph(schema)

    assert len(G.nodes) == 9
    assert len(G.edges) == 8
    assert G.nodes["student"]["type"] == "table"
    assert G.nodes["student__id"]["type"] == "column"
    assert G.nodes["student__name"]["type"] == "column"


def test_get_sub_graph():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE enrollment (student_id INT NOT NULL REFERENCES student(id), course_id INT NOT NULL REFERENCES course(id));
    """

    G = sql_to_graph(schema)
    subgraph = get_sub_graph(G, "student", 2)

    assert len(subgraph.nodes) == 6
    assert len(subgraph.edges) == 5

def normalize_sql_string(sql_string):
    sql_string = sql_string.lower()
    sql_string = sql_string.replace(" ", "")
    sql_string = sql_string.replace(";", "")
    return sql_string


def test_graph_to_sql():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE enrollment (student_id INT NOT NULL REFERENCES student(id), course_id INT NOT NULL REFERENCES course(id));
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER PRIMARY KEY NOT NULL,\n"
        "  name VARCHAR(255) NOT NULL\n);"
        "\n"
        "CREATE TABLE course (\n"
        "  id INTEGER PRIMARY KEY NOT NULL,\n"
        "  name VARCHAR(255) NOT NULL\n);"
        "\n"
        "CREATE TABLE enrollment (\n"
        "  student_id INTEGER NOT NULL REFERENCES student(id),\n"
        "  course_id INTEGER NOT NULL REFERENCES course(id)\n);")

    sql_result = sql_result.strip().split(";")
    sql_result = [stmt.strip() for stmt in sql_result if stmt.strip()]
    sql_result = sorted(sql_result)

    expected_sql_result = expected_sql_result.strip().split(";")
    expected_sql_result = [stmt.strip() for stmt in expected_sql_result if stmt.strip()]
    expected_sql_result = sorted(expected_sql_result)

    print(sql_result, expected_sql_result)

    assert sql_result == expected_sql_result



def test_parse_inline_foreign_keys_no_references():
    sql_statements = [
        "CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
    ]

    expected_inline_foreign_keys = {}

    result = parse_inline_foreign_keys(sql_statements)
    assert result == expected_inline_foreign_keys


def test_parse_inline_foreign_keys_multiple_references():
    sql_statements = [
        "CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE enrollment (student_id INT NOT NULL REFERENCES student(id), course_id INT NOT NULL REFERENCES course(id), teacher_id INT NOT NULL REFERENCES teacher(id));",
    ]

    expected_inline_foreign_keys = {
        "enrollment": [
            {
                "parent_column": "student_id",
                "parent_datatype": "INT",
                "ref_table": "student",
                "ref_column": "id",
            },
            {
                "parent_column": "course_id",
                "parent_datatype": "INT",
                "ref_table": "course",
                "ref_column": "id",
            },
            {
                "parent_column": "teacher_id",
                "parent_datatype": "INT",
                "ref_table": "teacher",
                "ref_column": "id",
            },
        ]
    }

    result = parse_inline_foreign_keys(sql_statements)
    assert result == expected_inline_foreign_keys


def test_sql_to_graph_empty_schema():
    schema = ""

    G = sql_to_graph(schema)

    assert len(G.nodes) == 0
    assert len(G.edges) == 0


def test_sql_to_graph_self_referencing_table():
    schema = """
    CREATE TABLE employee (
        id INT NOT NULL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        manager_id INT REFERENCES employee(id)
    );
    """

    G = sql_to_graph(schema)

    assert len(G.nodes) == 4
    assert len(G.edges) == 3
    assert G.nodes["employee"]["type"] == "table"
    assert G.nodes["employee__id"]["type"] == "column"
    assert G.nodes["employee__name"]["type"] == "column"
    assert G.nodes["employee__manager_id"]["type"] == "column"


def test_get_sub_graph_empty():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    """

    G = sql_to_graph(schema)
    subgraph = get_sub_graph(G, "student", 0)

    assert len(subgraph.nodes) == 3
    assert len(subgraph.edges) == 2


def test_graph_to_sql_self_referencing_table():
    schema = """
    CREATE TABLE employee (
        id INT NOT NULL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        manager_id INT REFERENCES employee(id)
    );
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE employee (\n"
        "  id INTEGER PRIMARY KEY NOT NULL,\n"
        "  name VARCHAR(255) NOT NULL,\n"
        "  manager_id INTEGER REFERENCES employee(id)\n);"
    )

    assert sql_result == expected_sql_result

def test_parse_not_null_constraints():
    sql_statements = [
        "CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "CREATE TABLE enrollment (student_id INT NOT NULL REFERENCES student(id), course_id INT NOT NULL REFERENCES course(id));",
    ]

    expected_not_null_constraints = {
        "student": ["id", "name"],
        "course": ["id", "name"],
        "enrollment": ["student_id", "course_id"],
    }

    result = parse_not_null_constraints(sql_statements)
    assert result == expected_not_null_constraints


def test_sql_to_graph_unique_constraints():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL UNIQUE);
    """

    G = sql_to_graph(schema)

    assert "unique" in G.nodes["student__name"]["constraints"]


def test_sql_to_graph_primary_key_constraints():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    """

    G = sql_to_graph(schema)

    assert G.nodes["student"]["primary_key"] == ["id"]


def test_get_sub_graph_no_neighbors():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    CREATE TABLE course (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL);
    """

    G = sql_to_graph(schema)
    subgraph = get_sub_graph(G, "student", 1)

    assert len(subgraph.nodes) == 3
    assert len(subgraph.edges) == 2


def test_graph_to_sql_unique_constraints():
    schema = """
    CREATE TABLE student (id INT NOT NULL PRIMARY KEY, name VARCHAR(255) NOT NULL UNIQUE);
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER PRIMARY KEY NOT NULL,\n"
        "  name VARCHAR(255) NOT NULL UNIQUE\n);"
    )

    sql_result = normalize_sql_string(sql_result)
    expected_sql_result = normalize_sql_string(expected_sql_result)

    assert sql_result == expected_sql_result

def test_parse_check_constraints():
    sql_statements = [
        "CREATE TABLE student (id INT PRIMARY KEY, age INT NOT NULL, CHECK (age >= 18));"
    ]

    expected_check_constraints = {
        "student": ["CHECK (age >= 18)"]
    }

    result = parse_check_constraints(sql_statements)
    assert result == expected_check_constraints


def test_parse_foreign_key_constraints():
    sql_statements = [
        "CREATE TABLE student (id INT PRIMARY KEY, age INT NOT NULL);",
        "CREATE TABLE enrollment (id INT PRIMARY KEY, student_id INT, FOREIGN KEY (student_id) REFERENCES student(id));",
    ]

    expected_foreign_key_constraints = {
        "enrollment": [("student_id", "student", "id")]
    }

    result = parse_foreign_key_constraints(sql_statements)
    assert result == expected_foreign_key_constraints


def test_sql_to_graph_check_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, age INT NOT NULL, CHECK (age >= 18));
    """

    G = sql_to_graph(schema)

    assert "CHECK (age >= 18)" in G.nodes["student__age"]["constraints"]


def test_sql_to_graph_foreign_key_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, age INT NOT NULL);
    CREATE TABLE enrollment (id INT PRIMARY KEY, student_id INT, FOREIGN KEY (student_id) REFERENCES student(id));
    """

    G = sql_to_graph(schema)

    assert ("enrollment__student_id", "student__id") in G.edges


def test_graph_to_sql_check_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, age INT NOT NULL, CHECK (age >= 18));
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  age INTEGER NOT NULL,\n"
        "  CHECK (age >= 18)\n);"
    )

    sql_result = normalize_sql_string(sql_result)
    expected_sql_result = normalize_sql_string(expected_sql_result)

    assert sql_result == expected_sql_result


def test_graph_to_sql_foreign_key_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, age INT NOT NULL);
    CREATE TABLE enrollment (id INT PRIMARY KEY, student_id INT, FOREIGN KEY (student_id) REFERENCES student(id));
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  age INTEGER NOT NULL\n);\n\n"
        "CREATE TABLE enrollment (\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  student_id INTEGER,\n"
        "  FOREIGN KEY (student_id) REFERENCES student(id)\n);"
    )

    sql_result = normalize_sql_string(sql_result)
    expected_sql_result = normalize_sql_string(expected_sql_result)

    assert sql_result == expected_sql_result

def test_parse_unique_constraints():
    sql_statements = [
        "CREATE TABLE student (id INT PRIMARY KEY, email VARCHAR(255) UNIQUE);"
    ]

    expected_unique_constraints = {
        "student": ["email"]
    }

    result = parse_unique_constraints(sql_statements)
    assert result == expected_unique_constraints


def test_parse_multiple_constraints():
    sql_statements = [
        "CREATE TABLE student (id INT PRIMARY KEY, email VARCHAR(255) UNIQUE, age INT NOT NULL, CHECK (age >= 18));"
    ]

    expected_primary_keys = {"student": "id"}
    expected_unique_constraints = {"student": ["email"]}
    expected_not_null_constraints = {"student": ["age"]}
    expected_check_constraints = {"student": ["CHECK (age >= 18)"]}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_sql_to_graph_unique_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, email VARCHAR(255) UNIQUE);
    """

    G = sql_to_graph(schema)

    assert "UNIQUE" in G.nodes["student__email"]["constraints"]


def test_graph_to_sql_unique_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, email VARCHAR(255) UNIQUE);
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  email VARCHAR(255) UNIQUE\n);"
    )

    sql_result = normalize_sql_string(sql_result)
    expected_sql_result = normalize_sql_string(expected_sql_result)

    assert sql_result == expected_sql_result


def test_graph_to_sql_multiple_constraints():
    schema = """
    CREATE TABLE student (id INT PRIMARY KEY, email VARCHAR(255) UNIQUE, age INT NOT NULL, CHECK (age >= 18));
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  email VARCHAR(255) UNIQUE,\n"
        "  age INTEGER NOT NULL,\n"
        "  CHECK (age >= 18)\n);"
    )

    sql_result = normalize_sql_string(sql_result)
    expected_sql_result = normalize_sql_string(expected_sql_result)

    assert sql_result == expected_sql_result

def test_empty_input():
    sql_statements = []

    expected_primary_keys = {}
    expected_unique_constraints = {}
    expected_not_null_constraints = {}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_no_constraints():
    sql_statements = [
        "CREATE TABLE student (id INT, name VARCHAR(255));"
    ]

    expected_primary_keys = {}
    expected_unique_constraints = {}
    expected_not_null_constraints = {}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_sql_to_graph_no_constraints():
    schema = """
    CREATE TABLE student (id INT, name VARCHAR(255));
    """

    G = sql_to_graph(schema)

    assert "constraints" not in G.nodes["student__id"]
    assert "constraints" not in G.nodes["student__name"]


def test_graph_to_sql_no_constraints():
    schema = """
    CREATE TABLE student (id INT, name VARCHAR(255));
    """

    G = sql_to_graph(schema)
    sql_result = graph_to_sql(G)

    expected_sql_result = (
        "CREATE TABLE student (\n"
        "  id INTEGER,\n"
        "  name VARCHAR(255)\n);"
    )

    sql_result = normalize_sql_string(sql_result)
    expected_sql_result = normalize_sql_string(expected_sql_result)

    assert sql_result == expected_sql_result


def test_invalid_sql_input():
    sql_statements = [
        "INVALID SQL STATEMENT"
    ]

    with pytest.raises(Exception) as exc_info:
        parse_primary_keys(sql_statements)

    assert "Invalid SQL statement" in str(exc_info.value)

def test_single_column_table():
    sql_statements = [
        "CREATE TABLE single_column (id INT PRIMARY KEY);"
    ]

    expected_primary_keys = {"single_column": ["id"]}
    expected_unique_constraints = {}
    expected_not_null_constraints = {}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_all_constraints_no_columns():
    sql_statements = [
        "CREATE TABLE no_columns ();",
        "ALTER TABLE no_columns ADD PRIMARY KEY ();",
        "ALTER TABLE no_columns ADD UNIQUE ();",
        "ALTER TABLE no_columns ADD CHECK ();",
    ]

    expected_primary_keys = {}
    expected_unique_constraints = {}
    expected_not_null_constraints = {}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_only_whitespace_input():
    sql_statements = [
        "   \t \n  "
    ]

    expected_primary_keys = {}
    expected_unique_constraints = {}
    expected_not_null_constraints = {}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_missing_semicolon():
    sql_statements = [
        "CREATE TABLE student (id INT, name VARCHAR(255))"
    ]

    with pytest.raises(Exception) as exc_info:
        parse_primary_keys(sql_statements)

    assert "Missing semicolon" in str(exc_info.value)

def test_invalid_sql_statement():
    sql_statements = [
        "CREATE TABL students (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL);"
    ]

    with pytest.raises(Exception) as exc_info:
        parse_primary_keys(sql_statements)

    assert "Invalid SQL statement" in str(exc_info.value)


def test_commented_lines():
    sql_statements = [
        "-- This is a commented line",
        "CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL);",
        "/* This is a multiline",
        "comment block */"
    ]

    expected_primary_keys = {"students": ["id"]}
    expected_unique_constraints = {}
    expected_not_null_constraints = {"students": ["name"]}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_empty_input():
    sql_statements = []

    expected_primary_keys = {}
    expected_unique_constraints = {}
    expected_not_null_constraints = {}
    expected_check_constraints = {}

    result_primary_keys = parse_primary_keys(sql_statements)
    result_unique_constraints = parse_unique_constraints(sql_statements)
    result_not_null_constraints = parse_not_null_constraints(sql_statements)
    result_check_constraints = parse_check_constraints(sql_statements)

    assert result_primary_keys == expected_primary_keys
    assert result_unique_constraints == expected_unique_constraints
    assert result_not_null_constraints == expected_not_null_constraints
    assert result_check_constraints == expected_check_constraints


def test_non_string_input():
    sql_statements = [1, 2, 3]

    with pytest.raises(Exception) as exc_info:
        parse_primary_keys(sql_statements)

    assert "Invalid input: expected a list of strings" in str(exc_info.value)
