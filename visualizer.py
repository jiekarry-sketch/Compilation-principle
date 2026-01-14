# src/visualizer.py
import os
import html
from graphviz import Digraph
import pandas as pd


class Visualizer:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def render_dfa(self, states, transitions, terminals, conflict_states=None):
        """
        绘制 DFA 状态转换图 (优化版本)
        """
        if conflict_states is None:
            conflict_states = set()

        dot = Digraph(comment='LR(0) DFA', format='png')

        # === 关键优化：调整布局参数 ===
        dot.attr(rankdir='LR')  # 从左到右
        dot.attr('graph',
                 dpi='300',
                 fontname='Arial',
                 nodesep='2.0',  # 增大节点间距
                 ranksep='3.0',  # 增大层级间距
                 splines='ortho',  # 使用正交线（直线），更清晰
                 concentrate='false',  # 不合并平行边，每条边独立显示
                 overlap='false',  # 防止节点重叠
                 pack='false',  # 不打包节点
                 start='1',  # 随机种子，尝试不同布局
                 newrank='true')  # 使用新的排名算法

        dot.attr('node',
                 fontname='Arial',
                 shape='plaintext',
                 margin='0.2',
                 width='0.8',  # 限制节点宽度
                 height='0.5')  # 限制节点高度

        dot.attr('edge',
                 fontname='Arial',
                 fontsize='10',
                 arrowsize='0.8',  # 箭头大小
                 penwidth='1.2')

        # 1. 绘制节点 (状态)
        for i, items in enumerate(states):
            is_conflict = i in conflict_states
            title_bg = "#ffcccc" if is_conflict else "#E0E0E0"
            title_text = f"I{i} ⚠️" if is_conflict else f"I{i}"
            border_color = "red" if is_conflict else "black"

            # === 优化：限制每个状态显示的项目数量 ===
            display_items = items
            if len(items) > 8:  # 如果项目太多，只显示前8个
                display_items = items[:8]
                # 添加省略号提示
                title_text = f"I{i} ({len(items)}项)"

            # 构造 HTML 表格 - 简化显示
            label_html = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{border_color}">
                        <TR><TD BGCOLOR="{title_bg}" BORDER="1" COLSPAN="2"><B>{title_text}</B></TD></TR>'''

            for item in display_items:
                rhs = item['right'][:]
                rhs.insert(item['dot'], '•')
                lhs_esc = html.escape(item['left'])
                rhs_esc = html.escape("".join(rhs))

                # 简化显示：对于长产生式进行截断
                if len(rhs_esc) > 15:
                    rhs_esc = rhs_esc[:15] + "..."

                bg_color = "#ffffff"
                if item['dot'] == len(item['right']) or (item['right'] == ['@'] and item['dot'] == 0):
                    bg_color = "#e6fffa"

                label_html += f'<TR><TD ALIGN="LEFT" BGCOLOR="{bg_color}" COLSPAN="2">{lhs_esc} &rarr; {rhs_esc}</TD></TR>'

            # 如果项目太多被截断，显示提示
            if len(items) > len(display_items):
                label_html += f'<TR><TD ALIGN="CENTER" BGCOLOR="#f0f0f0" COLSPAN="2">... 还有 {len(items) - len(display_items)} 项</TD></TR>'

            label_html += "</TABLE>>"

            # 为节点设置固定大小，防止节点过大
            dot.node(str(i),
                     label=label_html,
                     _attributes={'width': '1.2', 'height': '0.8'} if len(items) > 5 else {})

        # 2. 绘制边 (转移) - 优化边的显示
        for (start_idx, sym), end_idx in transitions.items():
            if sym in terminals:
                color = "#0056b3"  # 蓝色
                style = "solid"
                penwidth = "1.5"
                # 为终结符添加特殊标签
                if sym == '#':  # 处理结束符
                    label = " # "
                else:
                    label = f" {sym} "
            else:
                color = "#d9534f"  # 红色
                style = "dashed"
                penwidth = "1.2"
                label = f" {sym} "

            # === 优化：调整边的位置，减少交叉 ===
            dot.edge(str(start_idx), str(end_idx),
                     label=label,
                     color=color,
                     style=style,
                     fontcolor=color,
                     penwidth=penwidth,
                     # 添加约束，减少不必要的弯曲
                     constraint='true',
                     # 边的标签位置调整
                     labeldistance='2.5',
                     labelangle='25')

        # 3. 保存并渲染
        output_path = os.path.join(self.output_dir, 'dfa_graph')
        try:
            # 尝试不同的布局引擎
            dot.engine = 'dot'  # 使用dot引擎，更适合层次结构

            dot.render(output_path, view=False, cleanup=True)
            print(f"   -> [Graphviz] DFA 高清图已生成: {output_path}.png")

            # 如果第一次效果不好，尝试不同的随机种子
            if len(states) > 15:  # 状态较多时才尝试
                for attempt in range(3):
                    dot.attr(start=str(attempt + 10))  # 改变随机种子
                    alt_path = os.path.join(self.output_dir, f'dfa_graph_alt{attempt}')
                    dot.render(alt_path, view=False, cleanup=True)
                    print(f"   -> [Graphviz] 备选布局 {attempt + 1} 已生成")

        except Exception as e:
            print(f"   -> [Error] Graphviz 渲染失败: {e}")
            # 尝试使用neato引擎作为备选
            try:
                dot.engine = 'neato'
                dot.attr(overlap='scalexy')  # 使用不同的重叠处理
                dot.render(output_path, view=False, cleanup=True)
                print(f"   -> [Graphviz] 使用neato引擎生成DFA图")
            except Exception as e2:
                print(f"   -> [Error] 备选渲染也失败: {e2}")

    def render_table_html(self, headers, data, filename="parsing_table.html"):
        """生成带有搜索、排序功能的现代化 HTML 表格"""
        formatted_data = []
        for row in data:
            new_row = [str(x) if str(x).strip() != "" else "-" for x in row]
            formatted_data.append(new_row)

        df = pd.DataFrame(formatted_data, columns=headers)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LR(0) 分析表</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
            <style>
                body {{ padding: 40px; background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; border-left: 5px solid #0d6efd; padding-left: 15px; margin-bottom: 25px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📊 LR(0) 分析表 (Interactive)</h2>
                {df.to_html(classes='table table-striped table-hover table-bordered', table_id='parsingTable', index=False)}
            </div>
            <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
            <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
            <script>
                $(document).ready(function() {{
                    $('#parsingTable').DataTable({{ "paging": false, "info": false }});
                }});
            </script>
        </body>
        </html>
        """

        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)



    def render_trace_html(self, trace_data, input_str, filename="trace_log.html"):
        """
        生成详细的分析过程 HTML 表格
        """
        # 构建表格行
        rows_html = ""
        for row in trace_data:
            # 兼容不同键名
            action = row.get('action', row.get('ACTION', ''))
            step = row.get('步骤', row.get('step', ''))
            state_stack = row.get('状态栈', row.get('state_stack', ''))
            symbol_stack = row.get('符号栈', row.get('symbol_stack', ''))
            input_str_val = row.get('输入串', row.get('input', ''))
            goto_value = row.get('goto', row.get('GOTO', ''))

            # 给不同动作加点颜色标记
            badge_class = "secondary"
            if "s" in action and "acc" not in action:
                badge_class = "primary"  # Shift 蓝
            elif "r" in action:
                badge_class = "warning text-dark"  # Reduce 黄
            elif "acc" in action:
                badge_class = "success"  # Accept 绿
            elif "ERROR" in action:
                badge_class = "danger"  # Error 红

            action_html = f'<span class="badge bg-{badge_class}">{action}</span>'

            rows_html += f"""
            <tr>
                <td>{step}</td>
                <td style="font-family: monospace;">{state_stack}</td>
                <td style="font-family: monospace;">{symbol_stack}</td>
                <td style="font-family: monospace; text-align: right;">{input_str_val}</td>
                <td>{action_html}</td>
                <td style="font-family: monospace; text-align: center;">{goto_value}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LR(0) 分析过程: {input_str}</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
            <style>
                body {{ padding: 20px; background-color: #f8f9fa; font-family: 'Microsoft YaHei', sans-serif; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }}
                h3 {{ border-left: 5px solid #198754; padding-left: 15px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3>📝 分析过程追踪 (输入: <code style="color:#d63384">{input_str}</code>)</h3>
                <table class="table table-striped table-hover table-bordered">
                    <thead class="table-dark">
                        <tr>
                            <th style="width: 80px;">步骤</th>
                            <th>状态栈</th>
                            <th>符号栈</th>
                            <th style="text-align: right;">输入串</th>
                            <th>ACTION</th>
                            <th style="width: 80px; text-align: center;">GOTO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                <div class="mt-3">
                    <a href="parsing_table.html" class="btn btn-outline-primary">查看分析表</a>
                    <a href="dfa_graph.png" class="btn btn-outline-secondary" target="_blank">查看DFA图</a>
                </div>
            </div>
        </body>
        </html>
        """


        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"[可视化] 分析过程已生成: {output_path}")

    def render_dashboard(self, info_dict, filename="index.html"):
        """
        生成综合仪表盘 index.html
        :param info_dict: 包含所有显示数据的字典
        """
        grammar_html = "<br>".join(info_dict['grammar'])

        # 1. 准备分析表 HTML
        headers = info_dict['table_headers']
        table_rows = ""
        for row in info_dict['table_data']:
            table_rows += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"

        # 2. 准备测试用例的折叠面板 HTML
        accordion_html = ""
        for idx, res in enumerate(info_dict['test_results']):
            # 状态颜色
            status_color = "success" if res['success'] else "danger"
            status_icon = "✅" if res['success'] else "❌"
            status_text = "成功" if res['success'] else "失败"

            # 判断是否为文法句子
            result_text = "是该文法的句子" if res['success'] else "不是该文法的句子"
            result_class = "success" if res['success'] else "danger"

            # 构建 Trace 表格
            trace_rows = ""
            for step in res['trace']:
                # 兼容不同键名
                action = step.get('action', step.get('ACTION', ''))
                step_num = step.get('step', step.get('步骤', ''))
                state_stack = step.get('state_stack', step.get('状态栈', ''))
                symbol_stack = step.get('symbol_stack', step.get('符号栈', ''))
                input_str_val = step.get('input', step.get('输入串', ''))
                goto_value = step.get('goto', step.get('GOTO', ''))

                # === 关键修改：确保输入串中的 $ 替换为 # ===
                input_str_val = input_str_val.replace('$', '#')  # 额外确保替换

                action_badge = "secondary"
                if "s" in action and "acc" not in action:
                    action_badge = "primary"
                elif "r" in action:
                    action_badge = "warning text-dark"
                elif "acc" in action:
                    action_badge = "success"
                elif "ERROR" in action:
                    action_badge = "danger"

                trace_rows += f"""
                <tr>
                    <td>{step_num}</td>
                    <td class="font-monospace">{state_stack}</td>
                    <td class="font-monospace">{symbol_stack}</td>
                    <td class="font-monospace text-end">{input_str_val}</td>
                    <td><span class="badge bg-{action_badge}">{action}</span></td>
                    <td class="font-monospace text-center">{goto_value}</td>
                </tr>
                """

            accordion_html += f"""
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading{idx}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{idx}">
                        <span class="badge bg-{status_color} me-2">{status_icon} {status_text}</span>
                        <strong>输入: <code class="text-dark">{res['input']}</code></strong>
                        <span class="ms-auto text-muted small">{res['note']}</span>
                    </button>
                </h2>
                <div id="collapse{idx}" class="accordion-collapse collapse" data-bs-parent="#testSuiteAccordion">
                    <div class="accordion-body">
                        <table class="table table-sm table-striped table-hover border">
                            <thead class="table-light">
                                <tr>
                                    <th>步骤</th>
                                    <th>状态栈</th>
                                    <th>符号栈</th>
                                    <th class="text-end">输入串</th>
                                    <th>Action</th>
                                    <th style="width: 80px; text-align: center;">GOTO</th>
                                </tr>
                            </thead>
                            <tbody>{trace_rows}</tbody>
                        </table>
                        <div class="alert alert-{result_class} mt-3" role="alert">
                            <strong>分析结果:</strong> 输入串 <code>{res['input']}</code> {result_text}。
                        </div>
                    </div>
                </div>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LR(0) 分析器仪表盘</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
            <style>
                body {{ background-color: #f4f6f9; padding-bottom: 50px; font-family: 'Microsoft YaHei', sans-serif; }}
                .card {{ border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }}
                .card-header {{ background-color: #fff; border-bottom: 1px solid #eee; font-weight: bold; color: #2c3e50; }}
                .font-monospace {{ font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9em; }}
                #dfa-img {{ max-height: 400px; object-fit: contain; cursor: zoom-in; }}
            </style>
        </head>
        <body>
            <nav class="navbar navbar-dark bg-dark mb-4">
                <div class="container-fluid">
                    <span class="navbar-brand mb-0 h1">📊 LR(0) 可视化分析器</span>
                    <span class="navbar-text text-light">{info_dict['desc']}</span>
                </div>
            </nav>

            <div class="container-fluid px-4">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card h-100">
                            <div class="card-header">📜 文法规则</div>
                            <div class="card-body font-monospace bg-light">
                                {grammar_html}
                            </div>
                        </div>
                    </div>

                    <div class="col-md-8">
                        <div class="card h-100">
                            <div class="card-header">🕸️ 识别文法活前缀的DFA（LR(0)项目集规范族）</div>
                            <div class="card-body text-center">
                                <a href="dfa_graph.png" target="_blank">
                                    <img src="dfa_graph.png" class="img-fluid" id="dfa-img" alt="DFA图">
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">🔢 LR(0) 分析表</div>
                            <div class="card-body">
                                <table id="parsingTable" class="table table-bordered table-hover table-sm text-center">
                                    <thead class="table-dark">
                                        <tr>{''.join([f'<th>{h}</th>' for h in headers])}</tr>
                                    </thead>
                                    <tbody>{table_rows}</tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">🧪 输入串分析过程</div>
                            <div class="card-body">
                                <div class="accordion" id="testSuiteAccordion">
                                    {accordion_html}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
            <script>
                $(document).ready(function() {{
                    $('#parsingTable').DataTable({{ "paging": false, "info": false, "searching": false }});
                }});
            </script>
        </body>
        </html>
        """

        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[可视化] 仪表盘已生成: {output_path}")


