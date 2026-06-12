from unittest.mock import patch

def test_main_imports():
    import src.db.__main__  # noqa
    assert True

def test_main_has_main_function():
    from src.db.__main__ import main
    assert callable(main)

def test_main_module_execution():
    import runpy
    with patch('src.db.tui.main') as mock_main:
        runpy.run_path('src/db/__main__.py', run_name='__main__')
        mock_main.assert_called_once()




