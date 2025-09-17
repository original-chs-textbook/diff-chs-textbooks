#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from pathlib import Path

# MDX 文件模板保持不变
MDX_TEMPLATE = """---
title: '{title}'
sidebar_label: '{title}'
---

export const MyComponent = () => (
    <div className="comparison-table">
{table_content}
    </div>
);

下面是《{article_title}》这篇文章在不同版本中的文字对比：

<MyComponent />
"""

def create_mdx_from_html(input_file: Path, output_file: Path, title: str):
    """
    通过正则表达式从 HTML 文件中提取表格，并创建 Docusaurus MDX 文件。
    此版本不使用任何外部库。
    """
    # --- 1. 读取 HTML 文件 ---
    try:
        html_content = input_file.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"错误：输入文件未找到 -> {input_file}")
        return
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return

    # --- 2. 使用正则表达式查找并提取整个 table 标签 ---
    # re.DOTALL 标志让 '.' 可以匹配包括换行符在内的任意字符
    # re.IGNORECASE 标志让匹配不区分大小写 (例如 <table> 或 <TABLE>)
    pattern = re.compile(r'(<table.*?>.*?</table>)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(html_content)

    if not match:
        print(f"错误：在文件 {input_file} 中未找到 <table>...</table> 块。")
        return

    # group(1) 获取第一个捕获组的内容，也就是整个 table 块
    table_html_string = match.group(1)

    # --- 3. 将 HTML 属性转换为 JSX 兼容的属性 ---
    table_jsx_string = table_html_string.replace('class=', 'className=')
    table_jsx_string = table_jsx_string.replace('cellspacing=', 'cellSpacing=')
    table_jsx_string = table_jsx_string.replace('cellpadding=', 'cellPadding=')
    # 添加适当的缩进
    table_jsx_string = "      " + table_jsx_string.replace("\n", "\n      ")

    # --- 4. 填充 MDX 模板 ---
    mdx_title = f"{title}：原文 VS 教材"
    final_mdx_content = MDX_TEMPLATE.format(
        title=mdx_title,
        article_title=title,
        table_content=table_jsx_string
    )

    # --- 5. 创建目录并写入 MDX 文件 ---
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        output_file.write_text(final_mdx_content, encoding='utf-8')
        print(f"✅ 成功生成 MDX 文件 -> {output_file}")
    except Exception as e:
        print(f"写入文件时发生错误：{e}")


def main():
    """
    主函数，用于处理命令行参数。
    """
    parser = argparse.ArgumentParser(
        description="从 Beyond Compare HTML 报告生成 Docusaurus MDX 文件 (无外部依赖)。"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="输入的 HTML 文件路径。"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="输出的 MDX 文件路径。"
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        required=True,
        help="文章的标题 (例如: '春')。"
    )

    args = parser.parse_args()

    create_mdx_from_html(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
    