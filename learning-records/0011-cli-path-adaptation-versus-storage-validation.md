# 理解 CLI 路径适配与 Storage 校验的边界

用户已经能够准确说明：CLI 将外部字符串输入转换为 Storage 所需的 `Path` 类型，而 Storage 继续负责路径规范化、合法性检查和数据库操作。这个边界使 Storage 不依赖 CLI，未来也能由测试、FastAPI 或 Agent Runtime 直接复用。

## Evidence

用户在纠正“CLI 直接生成完整绝对路径”的说法后，独立复述了两层的职责划分。
