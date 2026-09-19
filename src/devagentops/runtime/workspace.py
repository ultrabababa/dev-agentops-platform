from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devagentops.evaluation.suite import OfflineCasePackage, PublicCaseView


class RuntimeWorkspaceError(RuntimeError):
    """Raised when a frozen Case artifact cannot be exposed safely."""


@dataclass(frozen=True)
class RuntimeCanonicalCoordinate:
    evidence_id: str
    source: str
    start_line: int
    end_line: int
    content_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "span": {
                "type": "line_range",
                "start_line": self.start_line,
                "end_line": self.end_line,
            },
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True)
class RuntimeCaseWorkspace:
    """把可信 Case Package 投影成 Runtime 可用的只读调查视图。

    Harness 持有含 Ground Truth 的完整 package；本对象只保存公开 Case 信息、
    package root、manifest 已声明的仓库成员和答案无关的 Canonical coordinates。
    对外读取 API 仅允许 raw log 与成员白名单中的 repo 文件。该限制是应用层
    capability boundary，不会收紧运行 Python 进程本身的 OS 文件权限。
    """
    case: PublicCaseView
    package_root: Path
    repository_members: tuple[str, ...]
    canonical_coordinates: tuple[RuntimeCanonicalCoordinate, ...]

    @classmethod
    def from_package(cls, package: OfflineCasePackage) -> RuntimeCaseWorkspace:
        """从已通过指纹校验的 package 构造视图，不复制物理文件正文。

        坐标按物理位置排序供模型稳定查看；Required/Optional 标签和 Expected Answer
        不进入对象。文件在工具读取时才从冻结 package 路径读取。
        """
        return cls(
            case=package.public_view(),
            package_root=package.manifest_path.parent,
            repository_members=tuple(
                sorted(item.path for item in package.repository_snapshot.files)
            ),
            canonical_coordinates=tuple(
                sorted(
                    (
                        RuntimeCanonicalCoordinate(
                            evidence_id=unit.evidence_id,
                            source=unit.source,
                            start_line=unit.start_line,
                            end_line=unit.end_line,
                            content_sha256=unit.content_sha256,
                        )
                        for unit in package.canonical_evidence_units
                    ),
                    key=lambda coordinate: (
                        coordinate.source,
                        coordinate.start_line,
                        coordinate.end_line,
                        coordinate.evidence_id,
                    ),
                )
            ),
        )

    def read_raw_log(self) -> str:
        return self._read_controlled_file(self.case.raw_log_path)

    def read_raw_log_exact(self) -> str:
        """Read the frozen log without universal-newline translation."""
        return self._read_controlled_file_exact(self.case.raw_log_path)

    def list_repository_files(self) -> tuple[str, ...]:
        return self.repository_members

    def read_repository_file(self, relative_path: str) -> str:
        """读取 manifest 声明的 repo 成员；未知路径在接触磁盘前即被拒绝。"""
        if relative_path not in self.repository_members:
            raise RuntimeWorkspaceError(
                f"repository file is outside the frozen workspace: {relative_path}"
            )
        return self._read_controlled_file(
            f"{self.case.repository_root}/{relative_path}"
        )

    def read_repository_file_exact(self, relative_path: str) -> str:
        """Read one frozen repository member without newline translation."""
        if relative_path not in self.repository_members:
            raise RuntimeWorkspaceError(
                f"repository file is outside the frozen workspace: {relative_path}"
            )
        return self._read_controlled_file_exact(
            f"{self.case.repository_root}/{relative_path}"
        )

    def evidence_ids_for_sources(self, sources: set[str]) -> tuple[str, ...]:
        """按 source identity 返回答案无关坐标 ID，不判断这些 ID 是否为 Ground Truth。"""
        return tuple(
            sorted(
                coordinate.evidence_id
                for coordinate in self.canonical_coordinates
                if coordinate.source in sources
            )
        )

    def _read_controlled_file(self, relative_path: str) -> str:
        # resolve + containment 防止受控相对路径经 symlink/遍历逃离 package root；
        # Case loader 已先冻结成员与 hash，但此处没有文件锁，不能抵御同进程外部篡改。
        path = (self.package_root / relative_path).resolve()
        if not path.is_relative_to(self.package_root.resolve()) or not path.is_file():
            raise RuntimeWorkspaceError(
                f"workspace file is unavailable: {relative_path}"
            )
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RuntimeWorkspaceError(
                f"workspace file cannot be read as UTF-8: {relative_path}"
            ) from exc

    def _read_controlled_file_exact(self, relative_path: str) -> str:
        path = (self.package_root / relative_path).resolve()
        if not path.is_relative_to(self.package_root.resolve()) or not path.is_file():
            raise RuntimeWorkspaceError(
                f"workspace file is unavailable: {relative_path}"
            )
        try:
            return path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RuntimeWorkspaceError(
                f"workspace file cannot be read as UTF-8: {relative_path}"
            ) from exc
