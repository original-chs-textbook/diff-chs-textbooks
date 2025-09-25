#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import json
from pathlib import Path

# --- 模板定义 ---

CATEGORY_JSON_TPL_SEM = {
    "label": "{sem}",
    "position": "{semester}",
    "link": {
        "type": "generated-index",
        "description": "〔{grade}年级〕语文（{sem}）"
    }
}

CATEGORY_JSON_TPL = {
    "label": "{padded_number}.《{title}》",
    "position": "{number}",
    "link": {
        "type": "generated-index",
        "description": "〔{grade}年级〕语文（{sem}）［第{number}课］：【原文】和【课文】对比"
    }
}

ORIGINAL_MD_TPL = """---
title: '原文'
sidebar_label: '原文'
sidebar_position: 1
---

:::tip
这是〔{grade}年级〕语文（{sem}）［第{number}课］《{title}》的【原文】相关信息。
:::

:::warning
本项目（`山高水落`）中使用的`原文`和`课文`的截图、图片或文字内容，**其著作权归原作者及出版社所有**。

当你使用这些资源时，意味着你已经阅读《👉[访问者须知与免责声明](/#访问者须知与免责声明)》，并接受其中条款。

再次提醒：你需自行承担*可能的侵犯著作权的风险和全部法律责任*，而**本项目发起人和开发者不承担任何连带责任**。
:::

## 教材页脚备注

![教材页脚备注截图](./assets/textbook-remark.png)

## 原文来源

我们找到了**相应**版本（或是**最可能**一致的版本），相关信息如下：

### 封面

![原文出处封面](./assets/original-cover.jpg)

### 目录

![原文书籍目录](./assets/original-contents.jpg)

### 出版社

![原文出版社](./assets/original-publisher.jpg)

## 原文截图

### 第〔1〕页
![原文截图01](./assets/original-01.jpg)

### 第〔2〕页

![原文截图02](./assets/original-02.jpg)

"""

TEXTBOOK_MD_TPL = """---
title: '课文'
sidebar_label: '课文'
sidebar_position: 2
---

:::tip
这是〔{grade}年级〕语文（{sem}）［第{number}课］的【课文】：《{title}》
:::

:::warning
本项目（`山高水落`）中使用的`原文`和`课文`的截图、图片或文字内容，**其著作权归原作者及出版社所有**。

当你使用这些资源时，意味着你已经阅读《👉[访问者须知与免责声明](/#访问者须知与免责声明)》，并接受其中条款。

再次提醒：你需自行承担*可能的侵犯著作权的风险和全部法律责任*，而**本项目发起人和开发者不承担任何连带责任**。
:::

## 课文

### 第〔1〕页

![教材课文截图01](./assets/textbook-01.png)

### 第〔2〕页

![教材课文截图02](./assets/textbook-02.png)

### 第〔3〕页

![教材课文截图03](./assets/textbook-03.png)

"""

DIFF_MDX_TPL = """---
title: '原文vs课文'
sidebar_label: '原文vs课文'
sidebar_position: 3
---

:::tip
这是〔{grade}年级〕语文（{sem}）［第{number}课］《{title}》原文和课文的【对比】。
:::

:::warning
本项目（`山高水落`）中使用的`原文`和`课文`的截图、图片或文字内容，**其著作权归原作者及出版社所有**。

当你使用这些资源时，意味着你已经阅读《👉[访问者须知与免责声明](/#访问者须知与免责声明)》，并接受其中条款。

再次提醒：你需自行承担*可能的侵犯著作权的风险和全部法律责任*，而**本项目发起人和开发者不承担任何连带责任**。
:::

export const MyComponent = () => (
    <div className="comparison-table">
{table_content}
    </div>
);

<MyComponent />
"""

ASSET_FILES = [
    "original-cover.jpg",
    "original-contents.jpg",
    "original-publisher.jpg",
    "original-01.jpg",
    "original-02.jpg",
    "textbook-remark.png",
    "textbook-01.png",
    "textbook-02.png",
    "textbook-03.png",
]

HEADER_ROW = """
    <tr className="AlignCenter">
      <td className="HeaderItem"><span className="TextSegSigDiff">左</span>侧为<span className="TextSegSigDiff">原</span>文</td>
      <td className="AlignCenter">&lt;&gt;</td>
      <td className="HeaderItem"><span className="TextSegSigDiff">右</span>侧为<span className="TextSegSigDiff">课</span>文</td>
    </tr>"""

def extract_and_format_table(html_content: str) -> str | None:
    """从HTML内容中提取、格式化并添加表头的表格为JSX字符串。"""
    
    # 定义要插入的表头行
    header_row = HEADER_ROW

    # 1. 使用正则表达式查找并提取整个 table 标签
    pattern = re.compile(r'(<table.*?>.*?</table>)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(html_content)
    if not match:
        return None
    
    table_html = match.group(1)

    # 2. 将 HTML 属性转换为 JSX 兼容的属性
    table_jsx = table_html.replace('class=', 'className=')
    table_jsx = table_jsx.replace('cellspacing=', 'cellSpacing=')
    table_jsx = table_jsx.replace('cellpadding=', 'cellPadding=')
    
    # --- 3. 核心修改：插入表头 ---
    # 找到第一个 ">" 符号，它标志着 <table> 开标签的结束位置
    first_tag_end = table_jsx.find('>')
    if first_tag_end != -1:
        # 将表头插入到开标签之后
        # table_jsx[:first_tag_end + 1] 是 <table ...> 部分
        # table_jsx[first_tag_end + 1:] 是表格的剩余部分
        final_table_jsx = (
            table_jsx[:first_tag_end + 1] 
            + header_row 
            + table_jsx[first_tag_end + 1:]
        )
    else:
        # 如果找不到 ">"，则作为备用方案，不插入表头
        final_table_jsx = table_jsx

    # 4. 添加适当的缩进并返回
    return "      " + final_table_jsx.replace("\n", "\n      ")

def process_lesson_files(args):
    """根据项目结构，生成一套完整的课程文件。"""
    # 1. 确定项目根目录和目标目录
    try:
        # __file__ 是当前脚本的路径
        script_path = Path(__file__).resolve()
        # project_root 是 utils 目录的上级目录
        project_root = script_path.parent.parent
    except NameError:
        # 在某些交互式环境中 __file__ 可能未定义
        project_root = Path.cwd()
        print("警告：无法通过 __file__ 确定项目根目录，将使用当前工作目录。")

    semester_dir = project_root / 'docs' / str(args.grade) / str(args.semester)
    target_dir = semester_dir / str(args.number)
    print(f"项目根目录已确定: {project_root}")
    print(f"将在以下目录生成文件: {target_dir}")

    # 2. 创建目标目录
    target_dir.mkdir(parents=True, exist_ok=True)

    # 3. 准备模板替换所需的数据
    sem = "上册" if args.semester < 2 else "下册"
    template_data = {
        "grade": args.grade,
        "semester": args.semester,
        "sem": sem,
        "number": args.number,
        "title": args.title,
        "padded_number": f"{args.number:02d}"
    }

    # 4. 生成 _category_.json
    category_data = CATEGORY_JSON_TPL_SEM.copy()
    category_data['label'] = category_data['label'].format(**template_data)
    category_data['position'] = int(category_data['position'].format(**template_data))
    category_data['link']['description'] = category_data['link']['description'].format(**template_data)
    category_path = semester_dir / '_category_.json'
    with open(category_path, 'w', encoding='utf-8') as f:
        # 使用 indent=2 美化JSON输出
        json.dump(category_data, f, ensure_ascii=False, indent=2)
    print(f"  -> 已生成: {category_path.relative_to(project_root)}")

    category_data = CATEGORY_JSON_TPL.copy()
    category_data['label'] = category_data['label'].format(**template_data)
    category_data['position'] = int(category_data['position'].format(**template_data))
    category_data['link']['description'] = category_data['link']['description'].format(**template_data)
    category_path = target_dir / '_category_.json'
    with open(category_path, 'w', encoding='utf-8') as f:
        # 使用 indent=2 美化JSON输出
        json.dump(category_data, f, ensure_ascii=False, indent=2)
    print(f"  -> 已生成: {category_path.relative_to(project_root)}")

    # 5. 生成 original.md 和 textbook.md
    original_md_path = target_dir / 'original.md'
    original_md_path.write_text(ORIGINAL_MD_TPL.format(**template_data), encoding='utf-8')
    print(f"  -> 已生成: {original_md_path.relative_to(project_root)}")
    
    textbook_md_path = target_dir / 'textbook.md'
    textbook_md_path.write_text(TEXTBOOK_MD_TPL.format(**template_data), encoding='utf-8')
    print(f"  -> 已生成: {textbook_md_path.relative_to(project_root)}")

    # 6. 生成 diff.mdx (核心逻辑)
    try:
        html_content = args.input.read_text(encoding='utf-8')
        table_content = extract_and_format_table(html_content)
        if table_content is None:
            print(f"错误: 在输入文件 {args.input} 中未找到 <table> 块。diff.mdx 未生成。")
            return

        template_data["table_content"] = table_content
        diff_mdx_content = DIFF_MDX_TPL.format(**template_data)
        diff_mdx_path = target_dir / 'diff.mdx'
        diff_mdx_path.write_text(diff_mdx_content, encoding='utf-8')
        print(f"  -> 已生成: {diff_mdx_path.relative_to(project_root)}")

    except FileNotFoundError:
        print(f"错误：输入文件未找到 -> {args.input}")
        return
    except Exception as e:
        print(f"处理 diff.mdx 时发生错误: {e}")
        return
        
    # 7. 创建 assets 目录和占位文件
    assets_dir = target_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)
    for filename in ASSET_FILES:
        (assets_dir / filename).touch()
    print(f"  -> 已创建 assets 目录及占位文件于: {assets_dir.relative_to(project_root)}")
    
    print("\n✅ 所有文件生成完毕！")

def generate_single_mdx(args):
    """仅生成一个独立的 mdx 文件，用于兼容旧的 -o 参数行为。"""
    print(f"检测到 -o 参数，将仅生成独立的 MDX 文件到: {args.output}")
    try:
        html_content = args.input.read_text(encoding='utf-8')
        table_content = extract_and_format_table(html_content)
        if table_content is None:
            print(f"错误: 在输入文件 {args.input} 中未找到 <table> 块。")
            return

        # 为模板准备数据，grade 和 number 变为可选信息
        if args.semester is not None:
            sem = "上册" if args.semester < 2 else "下册"
        else:
            sem = '?'
        template_data = {
            "grade": args.grade or '?',
            "number": args.number or '?',
            "sem": sem,
            "title": args.title,
            "table_content": table_content
        }

        mdx_content = DIFF_MDX_TPL.format(**template_data)
        
        # 创建父目录并写入文件
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(mdx_content, encoding='utf-8')
        print(f"✅ 成功生成 MDX 文件 -> {args.output}")

    except FileNotFoundError:
        print(f"错误：输入文件未找到 -> {args.input}")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="从 Beyond Compare HTML 报告生成 Docusaurus 课程文件结构。"
    )
    parser.add_argument(
        "-i", "--input", type=Path, required=True,
        help="输入的 HTML 文件路径。"
    )
    parser.add_argument(
        "-t", "--title", type=str, required=True,
        help="文章的标题 (例如: '春')。"
    )
    # --- 新增和修改的参数 ---
    parser.add_argument(
        "-g", "--grade", type=int, choices=range(1, 10),
        help="指定年级 (1-9)。当不使用 -o 时为必需。"
    )
    parser.add_argument(
        "-s", "--semester", type=int, choices=range(1, 2),
        help="指定学期 (1或2)。当不使用 -o 时为必需。"
    )
    parser.add_argument(
        "-n", "--number", type=int,
        help="指定课程序号 (例如: 1)。当不使用 -o 时为必需。"
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="[可选] 指定单个 MDX 文件的输出路径。若指定此项，则忽略 -g 和 -n 的目录生成逻辑。"
    )

    args = parser.parse_args()

    if args.output:
        # 如果用户指定了 -o，则执行旧的、生成单个文件的逻辑
        generate_single_mdx(args)
    else:
        # 如果没有指定 -o，则执行新的、生成完整目录结构的逻辑
        if args.grade is None or args.number is None:
            parser.error("当不使用 -o/--output 时, -g/--grade 和 -n/--number 参数是必需的。")
        process_lesson_files(args)

if __name__ == "__main__":
    main()
