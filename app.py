# app.py
from flask import Flask, render_template, request, jsonify, send_file
import json
import tempfile

from io import BytesIO
import base64

import sys
import os

from src.grammar import Grammar
from src.parser import LR0Parser
from src.engine import AnalysisEngine


# 处理PyInstaller打包后的路径问题
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe，使用临时目录路径
    bundle_dir = sys._MEIPASS
    template_dir = os.path.join(bundle_dir, 'templates')
    static_dir = os.path.join(bundle_dir, 'static')
    src_dir = os.path.join(bundle_dir, 'src')
else:
    # 正常开发环境
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(bundle_dir, 'templates')
    static_dir = os.path.join(bundle_dir, 'static')
    src_dir = os.path.join(bundle_dir, 'src')

# 添加到Python路径
sys.path.insert(0, src_dir)

# 创建Flask应用时指定路径
app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir,
    static_url_path='/static'
)


app = Flask(__name__)


def analyze_grammar(grammar_text, input_strings=None):
    """
    核心分析函数，返回分析结果字典
    """
    if input_strings is None:
        input_strings = []

    results = {
        "grammar_info": {},
        "dfa_info": {},
        "table_data": {},
        "test_results": [],
        "is_lr0": False,
        "conflicts": [],
        "conflict_state_ids": []
    }

    try:
        # 1. 构建文法
        g = Grammar(grammar_text)
        results["grammar_info"]["productions"] = []
        for i, p in enumerate(g.productions):
            rhs = " ".join(p['right'])
            if not rhs or rhs == "@":
                rhs = "ε"
            results["grammar_info"]["productions"].append({
                "index": i,
                "left": p['left'],
                "right": rhs
            })

        results["grammar_info"]["terminals"] = sorted(list(g.terminals))
        results["grammar_info"]["non_terminals"] = sorted(list(g.non_terminals))

        # 2. 构建解析器
        parser = LR0Parser(g)
        parser.build_canonical_collection()
        parser.build_parsing_table()

        results["is_lr0"] = parser.is_lr0
        results["conflicts"] = parser.conflicts
        results["conflict_state_ids"] = list(parser.conflict_state_ids)

        # 3. DFA信息
        results["dfa_info"]["states"] = []
        for i, items in enumerate(parser.states):
            state_items = []
            for item in items:
                rhs = item['right'][:]
                rhs.insert(item['dot'], '•')
                state_items.append(f"{item['left']} → {''.join(rhs)}")
            results["dfa_info"]["states"].append({
                "id": i,
                "items": state_items,
                "is_conflict": i in parser.conflict_state_ids
            })

        results["dfa_info"]["transitions"] = []
        for (start, sym), end in parser.transitions.items():
            results["dfa_info"]["transitions"].append({
                "from": start,
                "to": end,
                "symbol": sym
            })

        # 4. 分析表数据 - 确保列顺序一致
        terminals = sorted(list(g.terminals))
        non_terminals = sorted(list(g.non_terminals))
        if g.start_symbol in non_terminals:
            non_terminals.remove(g.start_symbol)

        # 调整终结符显示顺序：将 $ 替换为 #，并确保 # 在最后
        display_terminals = []
        original_terminals_order = []  # 保存原始的终结符顺序，用于获取动作

        # 先处理小写字母
        lowercase_terms = sorted([t for t in terminals if t.islower() and t != '$'])
        for term in lowercase_terms:
            display_terminals.append(term)
            original_terminals_order.append(term)

        # 处理其他非小写字母终结符（除了 $）
        other_terms = sorted([t for t in terminals if not t.islower() and t != '$'])
        for term in other_terms:
            display_terminals.append(term)
            original_terminals_order.append(term)

        # 最后处理 $，显示为 #
        if '$' in terminals:
            display_terminals.append('#')
            original_terminals_order.append('$')

        # 构建表头
        headers = ["State"] + display_terminals + non_terminals

        # 构建表格数据 - 按照 original_terminals_order 顺序获取动作
        table_data = []
        for i in range(len(parser.states)):
            row = [str(i)]

            # ACTION部分 - 按照 original_terminals_order 顺序获取动作
            for t in original_terminals_order:
                action = parser.action_table[i].get(t, "")

                # 将动作中的 $ 替换为 #（如果存在）
                if isinstance(action, str):
                    action = action.replace('$', '#')
                row.append(action)

            # GOTO部分
            for nt in non_terminals:
                goto = parser.goto_table[i].get(nt, "")
                row.append(str(goto) if goto != "" else "")

            table_data.append(row)

        results["table_data"] = {
            "headers": headers,
            "rows": table_data
        }

        # 5. 测试输入串 - 只执行一次
        if parser.is_lr0 and input_strings:
            engine = AnalysisEngine(parser)
            for inp in input_strings:
                inp = inp.strip()
                if not inp:
                    continue

                success, trace_log = engine.parse(inp)

                # 确保有trace_log
                if not trace_log:
                    trace_log = []

                # 格式化trace - 确保格式统一
                formatted_trace = []
                for step in trace_log:
                    formatted_trace.append({
                        "step": step.get("step", ""),
                        "state_stack": step.get("state_stack", ""),
                        "symbol_stack": step.get("symbol_stack", ""),
                        "input": step.get("input", ""),
                        "action": step.get("action", ""),
                        "goto": step.get("goto", "")
                    })

                results["test_results"].append({
                    "input": inp,
                    "success": success,
                    "trace": formatted_trace
                })
        else:
            # 即使不能测试，也记录空的测试结果
            results["test_results"] = []

        # 6. 生成DFA图像
        from src.visualizer import Visualizer

        # 创建临时目录存储图像
        with tempfile.TemporaryDirectory() as temp_dir:
            viz = Visualizer(temp_dir)
            viz.render_dfa(
                parser.states,
                parser.transitions,
                terminals,
                parser.conflict_state_ids
            )

            # 读取生成的图像并转换为base64
            img_path = os.path.join(temp_dir, "dfa_graph.png")
            if os.path.exists(img_path):
                with open(img_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    results["dfa_image"] = f"data:image/png;base64,{img_data}"

        return results, None

    except Exception as e:
        return None, str(e)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()

    if not data or 'grammar' not in data:
        return jsonify({"error": "请输入文法"}), 400

    grammar_text = data['grammar']
    input_strings = data.get('inputs', [])

    # 清理输入：移除空行和注释
    grammar_lines = []
    for line in grammar_text.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):  # 支持注释行
            grammar_lines.append(line)
    grammar_text = '\n'.join(grammar_lines)

    # 清理测试输入
    clean_inputs = []
    for inp in input_strings:
        inp = inp.strip()
        if inp:
            clean_inputs.append(inp)

    try:
        # 1. 构建文法，检查是否有解析错误
        g = Grammar(grammar_text)

        # 检查文法解析错误
        if g.errors:
            # 返回文法错误信息
            return jsonify({
                "grammar_errors": g.errors,
                "has_grammar_errors": True
            }), 400

        # 2. 继续执行后续分析...
        results, error = analyze_grammar(grammar_text, clean_inputs)

        if error:
            return jsonify({"error": error}), 500

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # 生产环境使用waitress服务器
    from waitress import serve
    import webbrowser
    import threading

    port = 5000


    # 自动打开浏览器
    def open_browser():
        webbrowser.open(f'http://localhost:{port}')


    # 延迟3秒打开浏览器
    timer = threading.Timer(3, open_browser)
    timer.start()

    print(f"""
    ========================================
    LR(0) 文法分析器 已启动！

    访问地址: http://localhost:{port}
    按 Ctrl+C 停止程序

    注意：首次启动可能需要几秒钟生成资源文件
    ========================================
    """)

    try:
        serve(app, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n程序已停止")