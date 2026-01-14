# src/engine.py
from src.utils import TableRenderer


class AnalysisEngine:
    def __init__(self, parser):
        self.parser = parser

    def parse(self, input_string: str):
        if not self.parser.is_lr0:
            return False, []

        stack = [0]
        symbol_stack = ['$']  # 内部保持 $

        trace_log = []

        input_tokens = list(input_string) + ['$']  # 内部保持 $
        ptr = 0
        step = 1

        while True:
            top_state = stack[-1]
            current_char = input_tokens[ptr]
            action = self.parser.action_table[top_state].get(current_char)

            # === 关键修改：将 $ 替换为 # 进行显示 ===
            state_stack_str = " ".join(map(str, stack))
            symbol_stack_str = "".join(symbol_stack).replace('$', '#')  # $ 替换为 #
            remaining_input = "".join(input_tokens[ptr:]).replace('$', '#')  # $ 替换为 #

            # 初始化GOTO列
            goto_value = ""

            step_info = {
                "step": step,
                "state_stack": state_stack_str,
                "symbol_stack": symbol_stack_str,  # 这里已经是替换后的值
                "input": remaining_input,  # 这里已经是替换后的值
                "action": str(action) if action else "ERROR",
                "goto": goto_value
            }
            trace_log.append(step_info)

            if action is None:
                return False, trace_log

            # === SHIFT ===
            if action.startswith('s'):
                next_state = int(action[1:])
                stack.append(next_state)
                symbol_stack.append(current_char)
                ptr += 1

            # === REDUCE ===
            elif action.startswith('r'):
                prod_idx = int(action[1:])
                production = self.parser.grammar.productions[prod_idx]
                lhs = production['left']
                rhs = production['right']

                pop_len = len(rhs)
                if pop_len == 1 and rhs[0] == '@':
                    pop_len = 0


                if pop_len > 0:
                    stack = stack[:-pop_len]
                    symbol_stack = symbol_stack[:-pop_len]

                current_top = stack[-1]
                if lhs in self.parser.goto_table[current_top]:
                    goto_state = self.parser.goto_table[current_top][lhs]
                    stack.append(goto_state)
                    symbol_stack.append(lhs)


                    # === 更新GOTO列 ===
                    trace_log[-1]['goto'] = str(goto_state)  # 英文小写
                else:
                    return False, trace_log

            # === ACCEPT ===
            elif action == 'acc':

                return True, trace_log

            step += 1