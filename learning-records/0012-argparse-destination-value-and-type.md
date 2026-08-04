# 理解 argparse 的 dest、值与类型

用户已经能够区分 `args.command` 是解析结果上的属性、`"init"` 是该属性保存的值、`str` 是值的类型，并理解 `add_subparsers(dest="command")` 会把所选子命令名称写入 `args.command`。

## Evidence

用户在把属性名误认为类型后，根据反馈正确回答 `args.command` 的值为 `"init"`、类型为 `str`。
