# Triage V1 正式评测套件

`triage-suite-v1` 是 DevAgentOps 第一套正式冻结的故障诊断与报告评测套件（Formal Evaluation Suite）。

它包含 **20 个等权重、经过人工审核的真实历史故障 Case**，覆盖 V1 定义的 5 类失败类型，每类严格 4 个 Case。

- Suite Manifest：[`suite.json`](./suite.json)
- Suite ID / Version：`triage-suite-v1` / `1`
- Suite Fingerprint：`b61f2e3ff85ec77857625a323680b45344fc68523df7cdf70235fa8236c592ed`
- Case 数量：20
- 每个 Case 权重：`1`
- Failure Type：5 类，每类严格 4 个
- Canonicalization Profile v1：所有文本 Physical Artifact 从第 1 行开始，以连续、不重叠的 100 行窗口划分；最后一个窗口可以不足 100 行
- 完整策划与审核历史：[`BULK-DRAFT-REVIEW.md`](./BULK-DRAFT-REVIEW.md)
- 每个 Case 的 Human Review 记录：[`reviews/`](./reviews/)

正式 Suite 的成员由 `suite.json` 显式定义，而不是通过扫描目录自动发现。

仓库中可能仍保留被拒绝、reserve、research-only 或 taxonomy 不匹配的 Case Package，用于保存策划和审核历史，但它们不属于正式 Suite。

## 一个 Case 表示什么

每个 Case 都来自一个真实历史故障，并冻结了一个有边界的调查工作区。

这个工作区不会只保留“能直接回答问题的最小证据”，而是尽量接近故障发生时，一个工程师合理可能调查到的真实环境，包括：

- 原始失败日志或历史失败记录
- 对应版本的代码
- 配置文件
- 测试文件
- 构建文件
- 自然存在的干扰信息
- 合理的竞争假设

它的目标不是把答案喂给 Runtime，而是保留一个真实、有限、可复现的 investigation space。

每个 Case Package 主要包含：

- `physical-artifacts/`
  - 历史失败 observation
  - 有边界的历史代码快照
  - 是整个 Case 的 Source of Truth

- `canonical-evidence/`
  - 对 Physical Artifacts 建立确定性的引用坐标
  - Canonical Unit 用于引用和评分
  - **它不是 Retrieval chunk**

- `evaluator/required-evidence.json`
  - 支撑 Ground Truth 所需的 inclusion-minimal evidence set
  - 也就是：再删掉其中任意关键证据，都可能无法完整支持正确诊断

- `evaluator/expected-answer.json`
  - Diagnosis Ground Truth
  - 描述失败类型、summary、root cause 和 recommended action
  - 不包含 Evidence ID

- `case.json`
  - 记录 provenance、sanitization、review status 和不可变 Case identity

V1 评测的是：

> Runtime 能否从冻结的真实故障证据中完成正确的诊断和报告。

V1 不要求 Agent：

- 修改代码
- 重跑测试
- 创建 PR
- 部署修复
- 重建历史运行环境

## 为什么这样设计

这套 Suite 的主要用途，是在 **相同 Case、相同 Physical Evidence Universe、相同 Ground Truth** 下，对不同 Runtime 做 paired comparison。

例如可以比较：

- Fixed Pipeline
- Full-context model
- Retrieval
- 多阶段 workflow
- ReAct / Tool Use
- 后续 Planning / Verification / Memory Runtime

理想情况下，能力较弱的 Runtime 无法稳定获得完整 Ground Truth；而随着 evidence acquisition、Retrieval、tool use 和 Agent control 能力提升，正确诊断率和 Evidence Hit 应逐步提高。

因此：

> Physical Universe 必须大于 Required Evidence。

如果 Curator 直接把 Case 削成“答案附近的几段代码”，那么 Runtime 几乎不再需要调查，评测就无法测量 Retrieval 或 Agent 能力。

Required Evidence 是正确答案所需要的最小证据集合，而：

> Physical Universe - Required Evidence

所构成的空间，正是 Runtime 需要进行搜索、筛选、排除和推理的地方。

Suite 的难度也不是完全一致的。

其中：

- `bugswarm-traccar-166900445` 被有意保留为一个低难度 anchor
- 一些 Case 属于 borderline / lower-end adequate
- 一些 Case 需要跨多个文件构建完整因果链
- 一些 Case 需要做 absence reasoning
- 一些 Case 需要排除多个真实竞争假设
- 一些 Case 需要理解语言 / Runtime / JVM 等领域语义

V1 并不追求“20 个 Case 全部都非常难”。

一个有合理难度梯度的 Suite，反而更容易区分：

> Runtime 是完全失效，还是只能解决简单 Case，还是已经具备更强的调查能力。

# 20 个正式 Case

## `test_assertion_failure`

### `bugswarm-traccar-170287308`

项目：Traccar

历史失败：

Upro 协议解码测试调用了 `verifyNothing`，认为输入不应该被解码。

但这段输入实际上符合当前支持的 Upro message pattern，并正常走过了解码和 `Position` 构造路径。

因此真正的问题不是产品错误，而是测试 Oracle 已经过时。

为什么有评测价值：

日志只暴露了一个 opaque 的 `Position` 对象，而没有直接告诉 Agent 这个对象是否应该出现。

Runtime 必须阅读 decoder 与 test，判断到底是：

- 产品错误地产生了 `Position`
- 还是测试错误地认为“不应该产生任何东西”

这要求进行 oracle-vs-product 的方向判断。

详细审核：

[`reviews/b01-review.md`](./reviews/b01-review.md)

---

### `bugswarm-apache-struts-190697114`

项目：Apache Struts

历史失败：

文件上传测试期望错误信息：

`The file is to large`

而产品实际返回：

`The file is too large`

本质上是测试 Oracle 中一个非常隐蔽的拼写错误。

为什么有评测价值：

CI 终端日志只给出了失败测试名，没有打印 assertion 的 expected / actual。

Runtime 必须从大量测试和资源文件中定位：

- 哪个 assertion 失败
- expected string 来自哪里
- actual string 来自哪里
- 两者真正差异是什么

详细审核：

[`reviews/b02-review.md`](./reviews/b02-review.md)

---

### `bugswarm-retrofit-113047638`

项目：Retrofit

历史失败：

测试认为：

`service.post(null)`

本身就应该立即抛出：

`IllegalStateException("Unable to serialize null message.")`

但 Retrofit 的请求构造是 lazy 的。

调用 service method 时只会创建并返回一个 `Call`，真正的 request construction 和 body conversion 只有在：

- `request()`
- `execute()`
- `enqueue()`

等路径中才发生。

Converter 本身的 null check 实际上完全正确。

真正错误的是测试假设了 eager request construction。

为什么有评测价值：

这是一个很典型的“局部代码看起来没问题，但行为时机错位”的 Case。

Runtime 需要先排除两个很自然的假设：

- converter 没有处理 null
- `ignoreNull = false` 没有正确传递

然后继续沿：

service proxy → MethodHandler → OkHttpCall → request construction

追踪，才能找到真正的 lazy execution mechanism。

详细审核：

[`reviews/a1-retrofit-review.md`](./reviews/a1-retrofit-review.md)

---

### `bugswarm-sonar-php-206164136`

项目：SonarPHP

历史失败：

测试期待 `Monkey.php` 存在 `CoreMetrics.TESTS` measure，但最终得到 null。

真正原因是：

配置的 PHPUnit JUnit report 中根本没有 `Monkey.php` 的记录。

因此：

report 中没有这个文件
→ importer 不会产生对应 per-file report
→ 不会写入 `TESTS` measure
→ assertion 得到 null

为什么有评测价值：

日志只告诉 Agent：

> 某个值是 null

它既不告诉：

- 哪个 metric
- 哪个文件
- 数据来自哪个 report
- 为什么 measure 没产生

Runtime 需要跨：

test → sensor → service → importer → fixture

完成一条多跳因果链，并最终通过“某个实体不存在于 fixture”完成 absence reasoning。

详细审核：

[`reviews/a2-sonar-php-review.md`](./reviews/a2-sonar-php-review.md)

# `lint_or_type_failure`

### `bugswarm-checkstyle-77722324`

项目：Checkstyle

历史失败：

Checkstyle 在 `EqualsAvoidNullCheck.java` 中报告 `RedundantModifier`。

一个 `private static` nested class `FieldFrame` 的 constructor 被声明成了 `public`。

由于 enclosing class 本身是 private，这个 constructor 不可能真正拥有更高的外部可访问性，因此 `public` 是冗余 modifier。

最终 Checkstyle verification 阶段失败。

为什么有评测价值：

Runtime 需要把：

Maven verify
→ ant-phase-verify
→ Checkstyle
→ RedundantModifier
→ 具体 nested class visibility

连成完整诊断，而不是只报告“Checkstyle failed”。

这个 Case 也是 Schema V2 的 calibration reference。

---

### `bugswarm-mypy-237548392`

项目：mypy

历史失败：

一个 generic helper：

`retry_on_error`

使用 `_T` 表示 callback 返回类型。

失败调用传入的是一个只执行副作用、返回 `None` 的 lambda。

因此 mypy 无法为该 generic call 推断出预期的 type argument。

为什么有评测价值：

日志只给出了：

> Cannot infer type argument 1 of retry_on_error

真正解释需要跨两个位置理解：

- generic helper 的类型声明
- 实际 callback 的返回行为

错误机制不会直接出现在日志里。

详细审核：

[`reviews/n07-review.md`](./reviews/n07-review.md)

---

### `bugswarm-byte-buddy-149441998`

项目：Byte Buddy

历史失败：

静态分析器报告一个 broad：

`catch (Exception)`

问题。

但这段代码实际上是一个通过 reflection 探测 Java 9 module capability 的兼容性 shim。

因此问题并不是普通业务代码“随便 catch Exception”，而是一个跨 Java 版本兼容路径中的 analyzer violation。

为什么有评测价值：

Analyzer 已经明确告诉 Runtime：

- 文件
- 方法
- violation type

所以定位并不困难。

真正需要判断的是：

> 这是应该简单缩窄 exception type，还是应该理解为 deliberate compatibility shim 并选择更合理的处理方式？

详细审核：

[`reviews/n09-review.md`](./reviews/n09-review.md)

---

### `bugswarm-pygithub-36442425251`

项目：PyGithub

历史失败：

代码中有：

`isinstance(output, RequestsResponse) or hasattr(output, "iter_content")`

随后调用：

`output.raise_for_status()`

以及：

`output.iter_content(...)`

问题在于：

- `isinstance` branch 能证明 `output` 是 `RequestsResponse`
- `hasattr(..., "iter_content")` branch 只证明 `iter_content` 存在
- 它并不能证明 `raise_for_status` 存在

而函数更上游的返回类型仍然允许 `object`。

因此 mypy 接受 `iter_content`，却拒绝 `raise_for_status`。

为什么有评测价值：

这是一个典型的 type narrowing / control-flow join 问题。

Runtime 不能只读报错行，还必须追踪：

- `output` 的原始类型来自哪里
- `or` 两个 branch 分别提供了什么 type guarantee
- 为什么两个相邻 method call 的 type-check 结果不同

详细审核：

[`reviews/l1-pygithub-review.md`](./reviews/l1-pygithub-review.md)

# `dependency_or_install_failure`

### `bugswarm-traccar-221926468`

项目：Traccar

历史失败：

CI 使用 Java 7，但依赖中的 `async-http-client` 是用 Java 8 编译的。

日志出现：

`Unsupported major.minor version 52`

其中 class-file version 52 对应 Java 8。

该类又通过 `Context` 的 static initialization 路径被加载，最终导致大量彼此看起来无关的测试失败。

为什么有评测价值：

最终表现是：

> 大量测试同时出错

但真正根因只是：

> JVM runtime 与某个 dependency bytecode version 不兼容

Runtime 需要：

- 理解 major.minor version
- 找到实际 Java runtime
- 找到 dependency
- 理解 static initialization 如何把一个错误扩散成大规模 test fan-out

详细审核：

[`reviews/b06-review.md`](./reviews/b06-review.md)

---

### `github-tan-cli-30459137058`

项目：tan-cli

历史失败：

bootstrap host dependency 列表遗漏了 `hidapi` 所需要的 `libudev` development headers。

bootstrap 阶段已经出现 warning，但脚本选择继续执行。

真正的根因随后被埋在两千多行之后，最终日志尾部反而出现了容易误导调查方向的 `elftools` / Python 相关错误。

为什么有评测价值：

这是典型的：

> earlier tolerated failure → later misleading terminal failure

如果 Runtime 只看日志尾部，很容易诊断错。

它必须回溯更早阶段，识别哪个 warning 实际具有 causal significance。

详细审核：

[`reviews/n20-review.md`](./reviews/n20-review.md)

---

### `bugswarm-nukkit-94403868`

项目：Nukkit

历史失败：

`LevelDB.java` import：

`org.iq80.leveldb`

但实际执行的 `build.gradle` 并没有声明任何 LevelDB dependency。

因此 javac 产生：

- package does not exist
- cannot find symbol

等十个 cascading compile error。

为什么有评测价值：

missing package 本身很明显，但 Runtime 仍然必须判断：

- 当前 CI 实际使用 Gradle 还是 Maven
- 哪个 manifest 才是 operative manifest
- dependency 是真的漏声明
- 还是这段尚未完成的 LevelDB provider 根本不应该进入 main source set

这是一个诊断确定、remedy 存在一定选择空间的 Case。

详细审核：

[`reviews/d2-nukkit-review.md`](./reviews/d2-nukkit-review.md)

---

### `bugswarm-spring-hateoas-232784946`

项目：Spring HATEOAS

历史失败：

`spring5-next` profile 把 Spring 升级到了 Spring 5，但 Jackson 仍固定在 `2.8.5`。

Spring 5 路径中引用：

`com.fasterxml.jackson.databind.exc.InvalidDefinitionException`

而该 class 不存在于 Jackson 2.8.5。

最终导致 32 个彼此无关的 Spring context test 全部失败。

为什么有评测价值：

Jackson dependency 实际上成功 resolve 了。

所以不能简单诊断为：

> dependency missing / repository resolution failed

真正问题是：

> profile 只升级了 Spring，而没有同步升级与其兼容的 Jackson。

Runtime 必须区分：

- dependency missing
- dependency resolved but incompatible

详细审核：

[`reviews/d1-spring-hateoas-review.md`](./reviews/d1-spring-hateoas-review.md)

# `config_or_environment_failure`

### `bugswarm-testng-64757057`

项目：TestNG

历史失败：

构建过程广泛 apply 了 publishing script。

该脚本无条件对 archives configuration 执行 signing。

因此即使只是普通 CI assemble 路径，也会进入：

`signArchives`

但 CI 环境中并没有 signing identity。

最终构建失败。

为什么有评测价值：

失败 task 名并没有直接写在源码中。

日志中还有大量无关的 javadoc `error:`，容易让简单 grep / tail-based pipeline 偏离真正原因。

Runtime 必须理解 Gradle configuration 如何把 signing task 引入普通 task graph。

详细审核：

[`reviews/n11-review.md`](./reviews/n11-review.md)

---

### `bugswarm-traccar-166900445`

项目：Traccar

历史失败：

一个依赖外部环境的邮件测试被直接放进普通测试套件。

测试使用源码中的 placeholder credential 连接公开 AWS SES SMTP endpoint。

服务器随后返回 SMTP 535 authentication failure。

为什么有评测价值：

这个 Case **故意比较简单**。

失败日志、测试文件和凭据关系非常直接。

它在 Suite 中承担 low-difficulty anchor 的角色，用来判断：

> 一个 Runtime 是真的完全坏掉了，还是只是无法解决更复杂的 Case。

详细审核：

[`reviews/b08-review.md`](./reviews/b08-review.md)

---

### `bugswarm-blueflood-80881330`

项目：Blueflood

历史失败：

integration test 创建 Elasticsearch `events` index 时，把：

`events_mapping.json`

注册到了 type：

`metrics`

但 mapping 文件本身，以及 production code 中定义的事件类型，实际上都是：

`graphite_event`

因此 mapping parse 失败。

随后由于 setup 尚未完成，teardown 又访问未初始化对象，产生第二个 NPE。

为什么有评测价值：

日志只告诉 Agent：

> create index failed

它不告诉：

- mapping 文件是什么
- 注册 type 是什么
- production type 是什么
- 第二个 NPE 是否是根因

Runtime 需要组合：

test
→ mapping resource
→ production constant

并排除：

- Elasticsearch 没启动
- cluster 不 ready
- 加载了错误 resource

等竞争假设。

详细审核：

[`reviews/c2-blueflood-review.md`](./reviews/c2-blueflood-review.md)

---

### `bugswarm-cola-12505170926`

项目：Alibaba COLA

历史失败：

integration tests 启动完整 Spring context。

Datasource 默认连接：

`localhost:3306/chargeDB`

但 GitHub Actions CI：

- 没有 MySQL `services`
- 没有提供 `MYSQL_*` override

因此 datasource initialization 时连接被拒绝，最终整个 Spring context 无法启动。

为什么有评测价值：

日志中没有直接出现：

- JDBC URL
- `chargeDB`
- `localhost:3306`
- `MYSQL_SERVER`

等关键配置。

Runtime 必须离开日志，进入 repository 才能找到真实环境假设。

同时仓库中还存在一个看起来很像解决方案的 `application-test.yml`，但它实际上也连接同一个 localhost MySQL，因此是一个真实 red herring。

详细审核：

[`reviews/c1-cola-review.md`](./reviews/c1-cola-review.md)

# `timeout_or_flaky_failure`

### `idflakies-cukes-http-b483e1a8`

项目：CukesHTTP

历史失败：

前一个测试向 JVM-wide singleton-backed `GlobalWorld` 写入：

`ASSERTS_STATUS_CODE_MAX_SIZE = 5`

并且没有清理。

后续 victim test 启用了 body display，却没有重新设置或清空这个 key。

因此 victim 继承了前一个 test 泄漏的状态，原本应该看到的完整 body 被截断。

为什么有评测价值：

iDFlakies record 提供了 victim / order 信息，却没有 exception stack 或具体 assertion。

而且 Physical Universe 中存在多个真实可能 polluter。

Runtime 必须进行 candidate elimination，最终找到：

test state
→ singleton object factory
→ GlobalWorld
→ leaked map entry

这一整条共享状态路径。

详细审核：

[`reviews/n01-review.md`](./reviews/n01-review.md)

---

### `github-osquery-issue-7718`

项目：osquery

历史失败：

测试自己提前创建了 pidfile。

之后测试又把：

> pidfile 是否存在

作为 daemon 已经 ready 的同步信号。

结果 wait 可能立刻返回，而此时 daemon 甚至还没有安装 SIGINT handler。

于是测试发送 SIGINT 时存在 race：

- 有时 handler 已安装
- 有时还没有

最终产生 intermittent behavior。

为什么有评测价值：

这是一个典型的 synchronization contract 被测试自身破坏的问题。

Runtime 需要跨：

- Python test control flow
- daemon startup semantics
- pidfile readiness
- signal handler installation

理解为什么一个看似合理的 readiness signal 实际已经失效。

详细审核：

[`reviews/n18-review.md`](./reviews/n18-review.md)

---

### `odrepair-dubbo-737f7a7e`

项目：Apache Dubbo

历史失败：

polluter test 启动了一个 async `RpcContext`，并把相关状态留在线程级 `InternalThreadLocal` 中，没有清理。

victim 随后在同一个线程执行。

由于 `RpcContext.isAsyncStarted()` 仍然为 true，victim 的调用走入：

`AsyncRpcResult`

而不是正常同步 `RpcResult`。

最终读取到的是 polluter 之前已经完成的 future，而不是 victim 自己调用的返回值。

为什么有评测价值：

ODRepair observation 只提供：

- victim
- polluter
- order dependency

没有 exception 或 stack trace。

Runtime 必须追踪：

polluter test
→ RpcContext lifecycle
→ InternalThreadLocal
→ AsyncContextImpl
→ AbstractProxyInvoker
→ AsyncRpcResult

才能完整解释为什么 victim 本身没 bug，却会因为执行顺序而失败。

详细审核：

[`reviews/f5-dubbo-review.md`](./reviews/f5-dubbo-review.md)

---

### `odrepair-remoting-abf0455a`

项目：Jenkins Remoting

历史失败：

polluter 在 `ClassFilter` 第一次初始化前，把一个非法 regex 配置给它。

`ClassFilter` 的 static initializer 调用：

`createDefaultInstance()`

随后在：

`Pattern.compile(...)`

处抛出 `Error`。

Java/JVM 语义规定：

> 如果 class initialization 失败，该 class 会在当前 classloader 生命周期中保持 erroneous state，static initializer 不会重新执行。

虽然 polluter 的 `@After` 清除了 system property，但这并不能重置失败过的 class initialization。

victim 随后实例化继承自 `ClassFilter` 的 `TestFilter` 时，仍然触发错误。

为什么有评测价值：

observation 已经告诉 Runtime：

> 某 polluter 在前 → victim ERROR

但完全没有告诉：

> 为什么状态能跨 test 永久保留

正确诊断要求同时理解：

- invalid regex
- static initialization
- JVM erroneous class state
- cleanup 的局限
- victim 对该 superclass 的依赖

这是一个典型“代码状态 + JVM runtime semantics”结合的 Case。

详细审核：

[`reviews/f6-remoting-review.md`](./reviews/f6-remoting-review.md)

# Suite Portfolio 说明

这套 Suite 是 V1，不应被理解为“软件工程生态总体分布”的统计样本。

目前 20 个 Formal Case 中：

> **15 个来自 BugSwarm。**

同时 Java / JVM 项目占比也比较高。

这是 V1 已知的 source / language concentration。

之所以接受这一点，是因为 V1 当前主要目标不是：

> 估计所有语言、所有工程生态中 Agent 的平均能力。

而是：

> 在一组稳定、真实、经过严格人工审核的固定历史故障上，对不同 Runtime 做 paired capability comparison。

因此，对 V1 来说：

- Ground Truth 可信
- provenance 可信
- evidence universe 可信
- Runtime treatment 公平
- Case 有足够 investigation value

比追求语言分布均匀更重要。

未来 V2 可以增加：

- Python
- Go
- C/C++
- JavaScript / TypeScript
- 更多 GitHub Actions / issue / research benchmark source
- 更少依赖 BugSwarm 的 Case

但不应该为了增加 diversity 而 retroactively 修改已经冻结的 V1 Suite identity。

# 如何阅读这套 Suite

如果只是想快速理解 benchmark：

1. 先读本 README
2. 再看 [`suite.json`](./suite.json)

如果想了解某一个 Case 的正式 Ground Truth：

```text
cases/<case-id>/evaluator/expected-answer.json

如果想看支撑 Ground Truth 的最小证据集合：

```text
cases/<case-id>/evaluator/required-evidence.json
```

如果想看：

- provenance
- 原始失败来源
- Physical Universe 为什么这样划定
- Required Evidence removal test
- shortcut / leakage analysis
- competing hypotheses
- Runtime Discriminative Value
- Human admission decision

则阅读：

```text
reviews/
```

中对应的 Human Review 文件。

[`BULK-DRAFT-REVIEW.md`](./BULK-DRAFT-REVIEW.md) 是完整的策划、构造、拒绝、替换、校准和冻结过程记录。

其中会保留一些已经被后续决策 supersede 的 pre-freeze 状态。这是有意保留的审计历史，不代表当前 Formal Suite 状态。
