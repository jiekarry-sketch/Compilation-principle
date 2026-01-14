# src/parser.py
from src.utils import TableRenderer
from src.grammar import Grammar


class LR0Parser:
    def __init__(self, grammar: Grammar):

        self.grammar = grammar
        self.states = []  # 状态列表（每个状态是一个项目集）
        self.transitions = {}  # 状态转移表: (state_id, symbol) -> next_state_id
        self.action_table = {}  # ACTION表
        self.goto_table = {}  # GOTO表
        self.is_lr0 = True  # 标志位
        self.conflicts = []  # 冲突记录
        self.conflict_state_ids = set()  # 冲突状态ID集合

    def _get_item_str(self, item):
        """辅助：将项目对象转为字符串，用于去重比较"""
        rhs = item['right']
        dot = item['dot']
        rhs_str = ""
        for i, sym in enumerate(rhs):
            if i == dot:
                rhs_str += "·"
            rhs_str += sym
        if dot == len(rhs):
            rhs_str += "·"
        return f"{item['left']}->{rhs_str}"

    def _items_equal(self, set1, set2):
        """判断两个项目集是否相同"""
        s1 = set([self._get_item_str(i) for i in set1])
        s2 = set([self._get_item_str(i) for i in set2])
        return s1 == s2

    def _closure(self, items):
        """计算闭包 Closure(I)"""
        closure_set = [item.copy() for item in items]
        while True:
            added_new = False
            for item in closure_set:
                rhs = item['right']
                dot = item['dot']
                if dot < len(rhs):
                    symbol = rhs[dot]
                    if symbol in self.grammar.non_terminals:
                        for prod in self.grammar.productions:
                            if prod['left'] == symbol:
                                new_item = {'left': prod['left'], 'right': prod['right'], 'dot': 0}
                                exists = False
                                for existing in closure_set:
                                    if existing == new_item:
                                        exists = True
                                        break
                                if not exists:
                                    closure_set.append(new_item)
                                    added_new = True
            if not added_new:
                break
        return closure_set

    def _goto(self, items, symbol):
        """计算 GoTo(I, X)"""
        next_items = []
        for item in items:
            rhs = item['right']
            dot = item['dot']
            if dot < len(rhs) and rhs[dot] == symbol:
                new_item = item.copy()
                new_item['dot'] += 1
                next_items.append(new_item)
        return self._closure(next_items)

    def build_canonical_collection(self):
        """构建识别活前缀的DFA"""
        print("正在构建项目集规范族 (DFA)...")
        start_prod = self.grammar.productions[0]
        initial_item = {'left': start_prod['left'], 'right': start_prod['right'], 'dot': 0}
        initial_state = self._closure([initial_item])

        self.states.append(initial_state)
        to_process = [0]

        while to_process:
            current_idx = to_process.pop(0)
            current_items = self.states[current_idx]

            symbols = set()
            for item in current_items:
                if item['dot'] < len(item['right']):
                    symbol = item['right'][item['dot']]
                    # 关键修改：跳过 ε 符号（@），不为其创建转移
                    if symbol != '@':
                        symbols.add(symbol)

            for sym in sorted(list(symbols)):
                next_state_items = self._goto(current_items, sym)
                if not next_state_items:
                    continue

                existing_idx = -1
                for idx, state in enumerate(self.states):
                    if self._items_equal(state, next_state_items):
                        existing_idx = idx
                        break

                if existing_idx == -1:
                    self.states.append(next_state_items)
                    new_idx = len(self.states) - 1
                    self.transitions[(current_idx, sym)] = new_idx
                    to_process.append(new_idx)
                else:
                    self.transitions[(current_idx, sym)] = existing_idx

    def build_parsing_table(self):
        """生成分析表并检测冲突"""
        n_states = len(self.states)
        for i in range(n_states):
            self.action_table[i] = {}
            self.goto_table[i] = {}

        for i, state_items in enumerate(self.states):
            # 1. 移进 (Shift)
            for (src, sym), dest in self.transitions.items():
                if src == i and sym in self.grammar.terminals:
                    # 关键修改：确保 $ 也添加移进动作
                    self._add_action(i, sym, f"s{dest}")

            # GOTO 表
            for (src, sym), dest in self.transitions.items():
                if src == i and sym in self.grammar.non_terminals:
                    self.goto_table[i][sym] = dest

            # 2. 规约 (Reduce) 和 接受 (Accept)
            for item in state_items:
                if item['dot'] == len(item['right']) or (item['right'] == ['@'] and item['dot'] == 0):
                    # 接受动作：当点在最右端且左部是拓广文法的开始符号
                    if item['left'] == self.grammar.start_symbol and item['dot'] == len(item['right']):
                        # 关键修改：确保 acc 动作添加到 $ 上
                        self._add_action(i, '$', "acc")
                    else:
                        # 规约动作
                        prod_idx = -1
                        for idx, p in enumerate(self.grammar.productions):
                            if p['left'] == item['left'] and p['right'] == item['right']:
                                prod_idx = idx
                                break

                        if prod_idx >= 0:
                            action_str = f"r{prod_idx}"
                            # LR(0) 核心：对所有终结符都进行规约（包括 $）
                            for term in self.grammar.terminals:
                                if term != '$':  # $ 可能有接受动作，避免覆盖
                                    self._add_action(i, term, action_str)
                            # 额外添加 $ 的规约动作（如果没有接受动作冲突的话）
                            if '$' not in self.action_table[i] or self.action_table[i]['$'] != 'acc':
                                self._add_action(i, '$', action_str)

    def _add_action(self, state, symbol, action):
        """
        添加动作，支持显式记录冲突
        """
        if symbol in self.action_table[state]:
            existing = self.action_table[state][symbol]
            # 如果动作不一样，说明冲突 (例如 s3 vs r2)
            if existing != action and action not in existing:
                self.is_lr0 = False

                # [核心修复] 记录冲突状态 ID
                self.conflict_state_ids.add(state)

                new_val = existing + "/" + action
                self.action_table[state][symbol] = new_val

                conflict_msg = f"State {state}, Symbol '{symbol}': Conflict [{new_val}]"
                if conflict_msg not in self.conflicts:
                    self.conflicts.append(conflict_msg)
        else:
            self.action_table[state][symbol] = action

    def print_dfa(self):
        print("\n[2.1] DFA 状态集信息")
        for i, items in enumerate(self.states):
            print(f"I{i}:")
            for item in items:
                print(f"  {self._get_item_str(item)}")
            print("-" * 15)

    def print_table(self):
        terminals = sorted(list(self.grammar.terminals))
        non_terminals = sorted(list(self.grammar.non_terminals))
        if self.grammar.start_symbol in non_terminals:
            non_terminals.remove(self.grammar.start_symbol)

        headers = ["State"] + terminals + non_terminals
        data = []
        for i in range(len(self.states)):
            row = [str(i)]
            for t in terminals:
                row.append(self.action_table[i].get(t, ""))
            for nt in non_terminals:
                val = self.goto_table[i].get(nt, "")
                row.append(str(val) if val != "" else "")
            data.append(row)

        print("\n[2.2] LR(0) 分析表 (Parsing Table)")
        TableRenderer.print_table(headers, data)

        if not self.is_lr0:
            print(f"\n[!!!] 严重警告: 检测到非 LR(0) 冲突！")
            print("该文法不是 LR(0) 文法，无法进行确定性分析。冲突详情如下：")
            for c in self.conflicts:
                print(f"  ❌ {c}")
        else:
            print("\n[✅] 这是一个合法的 LR(0) 文法，无冲突。")