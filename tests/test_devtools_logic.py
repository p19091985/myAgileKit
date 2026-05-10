from __future__ import annotations

import ast
import unittest

from tests.helpers import load_module_from_path

limpar_citacoes = load_module_from_path(
    "limpar_citacoes_for_tests",
    "DevTools/tools/limpar_citacoes.py",
    extra_paths=("DevTools/tools",),
)
removedor_docstrings = load_module_from_path(
    "removedor_docstrings_for_tests",
    "DevTools/tools/removedor_docstrings.py",
    extra_paths=("DevTools/tools",),
)
file_modifier = load_module_from_path(
    "file_modifier_for_tests",
    "DevTools/tools/file_modifier.py",
    extra_paths=("DevTools/tools",),
)
corretor_streamlit = load_module_from_path(
    "corretor_streamlit_for_tests",
    "DevTools/tools/corretor_streamlit.py",
    extra_paths=("DevTools/tools",),
)


class DevToolsLogicTests(unittest.TestCase):
    def test_limpar_citacoes_removes_supported_markers(self) -> None:
        text = "Antes [cite: 12] meio [cite_start] conteudo [cite_end] depois"

        cleaned, count = limpar_citacoes.remover_citacoes(text)

        self.assertEqual(count, 3)
        self.assertEqual(cleaned, "Antes  meio  conteudo  depois")

    def test_docstring_remover_removes_docs_and_preserves_sql_string(self) -> None:
        source = '''
"""module docs"""
QUERY = """SELECT id FROM users WHERE id = 1"""

def run():
    """function docs"""
    return QUERY
'''
        tree = ast.parse(source)
        transformed = removedor_docstrings.DocstringRemover().visit(tree)
        ast.fix_missing_locations(transformed)
        output = ast.unparse(transformed)

        self.assertNotIn("module docs", output)
        self.assertNotIn("function docs", output)
        self.assertIn("SELECT id FROM users", output)

    def test_file_modifier_cleans_python_and_c_style_comments(self) -> None:
        app = file_modifier.CommentRemoverApp.__new__(file_modifier.CommentRemoverApp)

        python_output = app.clean_content("x = 1  # remove\ntext = '# keep'\n", "python")
        c_output = app.clean_content("int x; // remove\n/* block */\nint y;\n", "c_style")

        self.assertIn("x = 1", python_output)
        self.assertIn("'# keep'", python_output)
        self.assertNotIn("# remove", python_output)
        self.assertNotIn("// remove", c_output)
        self.assertNotIn("block", c_output)
        self.assertIn("int y;", c_output)

    def test_streamlit_replacements_are_consistent(self) -> None:
        source = "st.image(img, use_container_width=True)\nst.dataframe(df, use_container_width=False)\n"

        updated = corretor_streamlit.pattern_true.sub(
            corretor_streamlit.replacement_true,
            source,
        )
        updated = corretor_streamlit.pattern_false.sub(
            corretor_streamlit.replacement_false,
            updated,
        )

        self.assertIn("width='stretch'", updated)
        self.assertIn("width='content'", updated)
        self.assertNotIn("use_container_width", updated)


if __name__ == "__main__":
    unittest.main()
