# src/grammar.py

class Grammar:
    def __init__(self, raw_productions: str):
        self.productions = []  # 列表，存储字典 {'left': 'S', 'right': ['a', 'A']}
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = ""
        self.errors = []  # 新增：存储解析错误信息

        # 初始化处理
        self._parse_grammar(raw_productions)
        if not self.errors:  # 只有在没有解析错误时才进行拓广
            self._augment_grammar()

    def _parse_grammar(self, raw_text: str):
        """解析用户输入的文法字符串"""
        lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]

        for i, line in enumerate(lines):
            # 兼容 -> 和 = 写法
            if '->' in line:
                sep = '->'
            else:
                sep = '='  # 容错处理

            if sep not in line:
                continue

            lhs, rhs_str = line.split(sep)
            lhs = lhs.strip()
            self.non_terminals.add(lhs)

            if i == 0 and not self.start_symbol:
                self.start_symbol = lhs

            # 处理 'A -> a | b' 形式
            alternatives = rhs_str.split('|')
            for alt in alternatives:
                # 假设符号之间用空格分隔，如果没有空格则按字符分割
                alt = alt.strip()
                if ' ' in alt:
                    rhs = [x for x in alt.split(' ') if x]
                else:
                    rhs = list(alt)

                # 检查右部是否为空（没有使用@表示空串）
                if not rhs:
                    # 记录错误：文法右部为空但未使用@
                    self.errors.append(f"产生式 '{lhs} -> ' 的右部为空，请使用 '@' 表示空串")
                    continue  # 跳过这个产生式，不添加到productions中
                elif len(rhs) == 1 and rhs[0] == '@':
                    # 这是合法的空串表示
                    pass

                self.productions.append({'left': lhs, 'right': rhs})

                # 识别终结符：非大写字母且不是@（关键修改）
                for sym in rhs:
                    if not sym.isupper() and sym != '@':  # 排除 @
                        self.terminals.add(sym)

    def _augment_grammar(self):
        """构造拓广文法: 添加 S' -> S"""
        new_start = self.start_symbol + "'"
        # 插入到第一个位置，作为第0号产生式
        self.productions.insert(0, {'left': new_start, 'right': [self.start_symbol]})
        self.start_symbol = new_start
        self.non_terminals.add(new_start)
        self.terminals.add('$')  # 添加输入结束符

    def get_production_str(self, index):
        """根据索引获取产生式的字符串形式 (用于打印)"""
        p = self.productions[index]
        return f"{p['left']}->{''.join(p['right'])}"