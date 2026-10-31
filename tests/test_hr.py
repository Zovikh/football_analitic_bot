from automation.hr import check_python, check_sql, check_sql_join, evaluate


def test_sql_xg_ok():
    query = "SELECT p.name, SUM(s.xg) AS xg FROM players p JOIN shots s ON s.player_id = p.id GROUP BY p.name ORDER BY xg DESC LIMIT 5"
    result = check_sql(query)
    assert result.passed


def test_sql_xg_missing_limit():
    query = "SELECT p.name, SUM(s.xg) FROM players p JOIN shots s ON s.player_id=p.id GROUP BY p.name ORDER BY 2 DESC"
    result = check_sql(query)
    assert not result.passed


def test_sql_join_ok():
    query = "SELECT m.id FROM matches m JOIN leagues l ON l.id = m.league WHERE l.name='АПЛ' AND m.home_goals > 0 AND m.away_goals > 0"
    assert check_sql_join(query).passed


def test_python_ok():
    code = "def last_n_form(results, n):\n    return ''.join(results[-n:])\n"
    assert check_python(code).passed


def test_python_syntax_error():
    assert not check_python("def broken(:\n  pass").passed


def test_evaluate_routes():
    assert evaluate("py_form", "def last_n_form(results, n):\n    return ''.join(results[-n:])").passed
