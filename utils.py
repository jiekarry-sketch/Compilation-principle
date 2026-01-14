# src/utils.py
class TableRenderer:
    """
    工具类：用于在控制台输出格式化的ASCII表格。
    """

    @staticmethod
    def print_table(headers: list, data: list):
        """
        打印自适应宽度的表格。
        :param headers: 表头列表 ['列1', '列2']
        :param data: 数据二维列表 [['a', 'b'], ['c', 'd']]
        """
        if not data:
            print("（无数据）")
            return

        # 1. 初始化每一列的宽度为表头的长度
        widths = [len(str(h)) for h in headers]

        # 2. 遍历数据，更新每一列的最大宽度
        # 注意：为了让中文对齐更好，这里简单按照字符长度计算（更严谨可用wcwidth库，但为了不依赖第三方库，此处仅做基础处理）
        for row in data:
            for i, val in enumerate(row):
                # 转换为字符串并计算长度
                content_len = len(str(val))
                # 包含中文时适当加宽（这是一个简单的对齐技巧）
                for char in str(val):
                    if '\u4e00' <= char <= '\u9fff':
                        content_len += 1
                if i < len(widths):
                    widths[i] = max(widths[i], content_len)

        # 3. 增加一些Padding让表格不拥挤
        widths = [w + 2 for w in widths]

        # 4. 生成分割线
        separator = "+" + "+".join(["-" * w for w in widths]) + "+"

        # 5. 打印
        print(separator)
        # 打印表头
        header_row = "|"
        for h, w in zip(headers, widths):
            # 简单居中
            padding = w - len(str(h))
            # 同样处理中文表头的对齐补偿
            for char in str(h):
                if '\u4e00' <= char <= '\u9fff':
                    padding -= 1
            left_pad = padding // 2
            right_pad = padding - left_pad
            header_row += " " * left_pad + str(h) + " " * right_pad + "|"
        print(header_row)
        print(separator)

        # 打印数据行
        for row in data:
            row_str = "|"
            for i, (val, w) in enumerate(zip(row, widths)):
                val_str = str(val)
                padding = w - len(val_str)
                for char in val_str:
                    if '\u4e00' <= char <= '\u9fff':
                        padding -= 1
                # 数据默认左对齐
                row_str += " " + val_str + " " * (padding - 1) + "|"
            print(row_str)
        print(separator)