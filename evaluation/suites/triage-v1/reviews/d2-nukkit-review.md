# D2 — bugswarm-nukkit-94403868 — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `BORDERLINE-ADEQUATE`** — **below the `ADEQUATE` estimate recorded at screening.** Constructed and reviewed in the targeted replacement round, awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.**

**Failure type:** `dependency_or_install_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `44605a3b8c30d05676f7b4ad2209e7d6337207d39abed396a5a266ccc8459348`.
**Slot:** one of two `dependency_or_install_failure` replacements.

## 1. The instruction that gated construction — the dependency established from the manifest

The discovery ledger justified D2 partly on an absence argument: the log downloads gson, jansi, snakeyaml and jline but not leveldb. That reasoning was explicitly not to be relied on, and it is not relied on here. The dependency is established from the build manifests and the source:

- **`build.gradle:22-28`** declares exactly `com.google.code.gson:gson:2.4`, `org.fusesource.jansi:jansi:1.11`, `org.yaml:snakeyaml:1.16`, `jline:jline:2.13`, plus `junit` at `testCompile`. **No leveldb dependency of any kind.**
- **`pom.xml:16-37`** declares the same four and no leveldb.
- **`LevelDB.java:19-21`** imports `org.iq80.leveldb.DB`, `org.iq80.leveldb.Options` and `org.iq80.leveldb.impl.Iq80DBFactory`.
- `LevelDB.java` is the **only** file in the repository that imports the leveldb API. `Chunk.java`, in the same package, does not — which is why all ten javac errors land in one file.

**`raw.log:521` shows `$ gradle assemble`**, so `build.gradle` is the operative manifest and `pom.xml` is present but unused by this job.

## 2. Authenticity and provenance

Source `https://www.bugswarm.org/artifact-logs/94403868/raw/`. **Exact executed revision** `5a893db8c78d3f4b05a9a6d34c7da782ed537611` (Nukkit/Nukkit), verified against the GitHub API; committer date `2015-12-02T14:06:47Z` matches the BugSwarm `committed_at` exactly, and `raw.log:358` records `git checkout -qf 5a893db8c78d3f4b05a9a6d34c7da782ed537611` — the executed revision is stated in the observation itself. Travis push job on `master`.

`raw.log` is 30,823 bytes / 719 lines and contains **all three Travis attempts** (`The command "eval gradle assemble" failed. Retrying, 2 of 3.`), each failing identically. Sanitization is ANSI/OSC removal plus CRLF/CR normalisation only. All **19 repository members are byte-identical** to the exact revision.

## 3. Independent causal chain

1. `raw.log:521-533` — `gradle assemble`; the four declared dependencies resolve and download.
2. `raw.log:534-573` — ten javac errors, all in `LevelDB.java`: `package org.iq80.leveldb does not exist` (`:19`, `:20`), `package org.iq80.leveldb.impl does not exist` (`:21`), then cascading `cannot find symbol` for `DB`, `Options` and `Iq80DBFactory` at `:38`, `:77`, `:135`, `:336`.
3. `raw.log:576-583` — `10 errors`, `:compileJava FAILED`, `Execution failed for task ':compileJava'`.
4. `build.gradle` declares no leveldb artifact, so the library is absent from the compile classpath.
5. The ten compile errors are a downstream symptom of one undeclared dependency, not of ten source defects. Three identical retries rule out a transient resolution failure.

## 4. Required Evidence — 2 units, and why it is only 2

| Required unit | What only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-0501-0600` | The observation, the operative build command `gradle assemble`, and all ten errors | Remove: no observation, and no way to know which manifest CI used |
| `repo:build-gradle:lines-0001-0029` | The operative dependency list, in which leveldb is absent | Remove: the omission cannot be established; "the artifact repository was unavailable" stays alive |

**`LevelDB.java` fails a strict removal test and is Optional.** The compiler quotes the offending import lines verbatim into the log (`import org.iq80.leveldb.DB;` and the rest), so the source usage is established without opening the file. This is the same property that made B16 log-alone sufficient, and it is recorded rather than argued away.

Five units are Optional, including `LevelDB.java:0001-0100`, `Server.java:0301-0400`, `pom.xml`, `settings.gradle` and `.travis.yml`.

## 5. Shortcut and leakage review

- `org.iq80.leveldb` occurs **18 times in the log**, `iq80` 42 times. The observation fully discloses the missing package name, the file and the line numbers. The repository's only necessary contribution is the *absence* in `build.gradle`.
- Answer-prose: **`Server.java:363` contains `//todo LevelDB provider`**, immediately after `addProvider(this, Anvil.class)` and `addProvider(this, McRegion.class)`. This is authentic contemporaneous code and is retained. It materially informs the reading: the LevelDB provider is unregistered work in progress.
- Two genuine discriminations survive:
  - **Which manifest is operative.** `pom.xml` and `build.gradle` both exist and both omit leveldb. An Agent that recommends editing `pom.xml` has not fixed the job. Only `raw.log:521` settles it, and only if the Agent knows Travis selects Gradle when `build.gradle` is present.
  - **Whether the code should compile at all.** With `//todo LevelDB provider` visible and the provider never registered, "this is unfinished code that should not be in the main source set" competes with "declare the dependency".
- `settings.gradle` declares `include 'nukkit'` for a subproject directory that does not exist — a further authentic red herring.

## 6. Runtime Discriminative Value — `BORDERLINE-ADEQUATE`, downgraded from the screening estimate

| Metric (diagnostic only) | Value |
|---|---:|
| `raw.log` | 719 lines / 30,823 bytes |
| Repository | 19 files / 104,568 bytes |
| Canonical units | 47 (8 log + 39 repo) |
| Required / Optional | 2 / 5 |

**Why it is below the `ADEQUATE` estimated at screening.** Screening credited an absence-based inference over the download list. Having done the manifest work the instruction required, the honest picture is thinner: one highly distinctive grep (`package org.iq80.leveldb does not exist`) plus one 29-line build file completes the root-cause statement, and the log quotes the imports so the source is not strictly needed. That is close to the "one distinctive grep and one small file" pattern the screening principle says to avoid.

**Why it is not `LOW`.** Unlike B16 and N10, the repository does contribute a necessary fact — the absence in the operative manifest — and two real discriminations remain: choosing between two competing manifests, and deciding whether unregistered work-in-progress should be made to compile. The recommended action is wrong if either is got wrong.

**The Expected Answer's direction, stated carefully.** `root_cause` is determined by the frozen evidence: source imports a library no manifest declares. `recommended_action` is the better-supported of two defensible remedies — the sources are in the main source set and are compiled unconditionally, so declaring the dependency is the direct fix. The alternative (exclude or remove the unfinished provider) is coherent and is recorded here rather than suppressed. This is a weaker form of the N22 hazard: the diagnosis is determined, the remedy is not uniquely determined.

## 7. Disposition

**Recommended `HUMAN REVIEW PASS`, at `BORDERLINE-ADEQUATE`**, as one `dependency_or_install_failure` replacement — with the explicit alternative that the Human may prefer to substitute the recorded reserve **D3 `orbit/orbit` job `126506070`**, which carries a stronger competing hypothesis in the form of an earlier `[ERROR] Invalid use of await` that does not fail the build.

This Case was not salvaged aggressively: nothing was pruned, no distractor was added, and the rating was lowered rather than the package adjusted to protect it. Not a Formal Freeze; Formal Suite membership is not frozen.
