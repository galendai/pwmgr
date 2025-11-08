# P2 - 中优先级任务 (计划在下一个冲刺)

## 📋 中优先级改进任务 (下一个冲刺周期)

### 1. 项目现代化迁移
**优先级**: 🟡 **MEDIUM**
**影响**: 项目配置过时，不符合现代Python标准
**预计工时**: 16小时

#### 任务描述
将项目从传统的setup.py迁移到现代的pyproject.toml配置，并集成现代开发工具。

#### 执行步骤
1. **创建pyproject.toml配置**
   ```toml
   # pyproject.toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"

   [project]
   name = "pwmgr"
   version = "0.2.0"
   description = "A secure local password manager"
   readme = "README.md"
   license = {file = "LICENSE"}
   authors = [
       {name = "Your Name", email = "your.email@example.com"},
   ]
   classifiers = [
       "Development Status :: 4 - Beta",
       "Intended Audience :: End Users/Desktop",
       "License :: OSI Approved :: MIT License",
       "Programming Language :: Python :: 3",
       "Programming Language :: Python :: 3.10",
       "Programming Language :: Python :: 3.11",
       "Programming Language :: Python :: 3.12",
       "Topic :: Security :: Cryptography",
       "Topic :: Utilities",
   ]
   requires-python = ">=3.10"
   dependencies = [
       "cryptography>=41.0.0",
       "click>=8.1.0",
   ]
   optional-dependencies = [
       "dev": [
           "pytest>=7.0.0",
           "pytest-cov>=4.0.0",
           "black>=23.0.0",
           "ruff>=0.1.0",
           "mypy>=1.0.0",
           "pre-commit>=3.0.0",
       ],
       "test": [
           "pytest>=7.0.0",
           "pytest-cov>=4.0.0",
           "pytest-mock>=3.10.0",
       ],
   ]

   [project.scripts]
   pwmgr = "pwmgr.cli:cli"

   [project.urls]
   Homepage = "https://github.com/yourusername/pwmgr"
   Documentation = "https://pwmgr.readthedocs.io/"
   Repository = "https://github.com/yourusername/pwmgr.git"
   "Bug Tracker" = "https://github.com/yourusername/pwmgr/issues"

   [tool.ruff]
   line-length = 88
   select = ["E", "F", "W", "S", "B", "C4", "UP"]
   ignore = ["E501"]  # 忽略行长度，由black处理

   [tool.ruff.per-file-ignores]
   "tests/*" = ["S101", "S311"]  # 测试文件中允许使用assert和随机

   [tool.mypy]
   python_version = "3.10"
   strict = true
   warn_return_any = true
   warn_unused_configs = true
   disallow_untyped_defs = true

   [tool.pytest.ini_options]
   minversion = "7.0"
   addopts = "-ra -q --strict-markers --strict-config"
   testpaths = ["tests"]
   python_files = ["test_*.py", "*_test.py"]
   python_classes = ["Test*"]
   python_functions = ["test_*"]

   [tool.coverage.run]
   source = ["pwmgr"]
   omit = ["*/tests/*", "*/test_*"]

   [tool.coverage.report]
   exclude_lines = [
       "pragma: no cover",
       "def __repr__",
       "raise AssertionError",
       "raise NotImplementedError",
       "if __name__ == .__main__.:",
   ]
   ```

2. **配置开发工具**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.4.0
       hooks:
         - id: trailing-whitespace
         - id: end-of-file-fixer
         - id: check-yaml
         - id: check-added-large-files
         - id: check-merge-conflict

     - repo: https://github.com/psf/black
       rev: 23.7.0
       hooks:
         - id: black
           language_version: python3

     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.0.287
       hooks:
         - id: ruff
           args: [--fix]

     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.5.1
       hooks:
         - id: mypy
           additional_dependencies: [types-all]
   ```

3. **迁移构建脚本**
   - 更新安装说明
   - 更新CI/CD配置
   - 测试新配置

#### 验证标准
- [ ] pyproject.toml配置完成
- [ ] 所有开发工具配置正确
- [ ] pre-commit hooks正常工作
- [ ] CI/CD管道适配
- [ ] 打包和安装测试通过

#### 负责人
- [ ] DevOps工程师
- [ ] 开发团队

---

### 2. 测试框架升级和扩展
**优先级**: 🟡 **MEDIUM**
**影响**: 测试覆盖不足，测试质量需要提升
**预计工时**: 24小时

#### 任务描述
升级测试框架到pytest，实现全面的测试覆盖，包括性能测试和安全测试。

#### 执行步骤
1. **创建测试基础设施**
   ```python
   # tests/conftest.py
   import pytest
   import tempfile
   import os
   from pwmgr.core import PasswordStorage, PasswordEntry

   @pytest.fixture
   def temp_storage():
       """临时存储fixture"""
       with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as f:
           temp_file = f.name

       storage = PasswordStorage(temp_file)
       yield storage

       # 清理
       if os.path.exists(temp_file):
           os.unlink(temp_file)

   @pytest.fixture
   def sample_entries():
       """示例密码条目fixture"""
       return [
           PasswordEntry(
               name="GitHub",
               username="user@example.com",
               password="gh_password123",
               notes="Main GitHub account"
           ),
           PasswordEntry(
               name="Google",
               username="user@gmail.com",
               password="google_password456",
               notes="Personal Google account"
           ),
       ]

   @pytest.fixture
   def master_password():
       """主密码fixture"""
       return "test_master_password_123"
   ```

2. **扩展单元测试**
   ```python
   # tests/test_services.py
   import pytest
   from pwmgr.core.services import PasswordService
   from pwmgr.core.exceptions import AuthenticationError, EntryNotFoundError

   class TestPasswordService:
       def test_authenticate_success(self, temp_storage, master_password, sample_entries):
           """测试认证成功"""
           temp_storage.save(sample_entries, master_password)
           service = PasswordService(temp_storage)

           assert service.authenticate(master_password) == True

       def test_authenticate_failure(self, temp_storage):
           """测试认证失败"""
           service = PasswordService(temp_storage)

           with pytest.raises(AuthenticationError):
               service.authenticate("wrong_password")

       def test_add_entry_duplicate(self, temp_storage, master_password, sample_entries):
           """测试添加重复条目"""
           temp_storage.save(sample_entries, master_password)
           service = PasswordService(temp_storage)

           with pytest.raises(ValueError, match="Entry with name .* already exists"):
               service.add_entry(sample_entries[0], master_password)
   ```

3. **添加集成测试**
   ```python
   # tests/test_integration.py
   import pytest
   from click.testing import CliRunner
   from pwmgr.cli import cli

   class TestCLIIntegration:
       def test_complete_workflow(self, temp_dir):
           """测试完整工作流程"""
           runner = CliRunner()

           # 初始化
           result = runner.invoke(cli, ['init'], input="test_password\ntest_password\n")
           assert result.exit_code == 0

           # 添加密码
           result = runner.invoke(cli, [
               'add',
               '--name', 'TestSite',
               '--username', 'test@example.com',
               '--password', 'test123'
           ], input="test_password\n")
           assert result.exit_code == 0

           # 列出密码
           result = runner.invoke(cli, ['list'], input="test_password\n")
           assert result.exit_code == 0
           assert 'TestSite' in result.output

           # 显示密码
           result = runner.invoke(cli, ['show', '--name', 'TestSite'], input="test_password\n")
           assert result.exit_code == 0
           assert 'test@example.com' in result.output
   ```

4. **性能测试**
   ```python
   # tests/test_performance.py
   import pytest
   import time
   from pwmgr.core import PasswordEntry, PasswordStorage, PasswordGenerator

   class TestPerformance:
       def test_password_generation_performance(self):
           """测试密码生成性能"""
           start_time = time.time()

           for _ in range(1000):
               PasswordGenerator.generate(length=16)

           end_time = time.time()
           duration = end_time - start_time

           # 应该在1秒内完成1000次生成
           assert duration < 1.0, f"密码生成性能不达标: {duration:.2f}秒"

       def test_encryption_performance(self, temp_storage, master_password):
           """测试加密性能"""
           entries = [
               PasswordEntry(
                   name=f"Site_{i}",
                   username=f"user_{i}@example.com",
                   password=f"password_{i}" * 10  # 长密码
               )
               for i in range(100)
           ]

           start_time = time.time()
           temp_storage.save(entries, master_password)
           save_time = time.time() - start_time

           start_time = time.time()
           loaded_entries = temp_storage.load(master_password)
           load_time = time.time() - start_time

           # 性能基准
           assert save_time < 2.0, f"保存性能不达标: {save_time:.2f}秒"
           assert load_time < 1.0, f"加载性能不达标: {load_time:.2f}秒"
           assert len(loaded_entries) == 100
   ```

5. **安全测试**
   ```python
   # tests/test_security.py
   import pytest
   from pwmgr.crypto import EncryptionService
   from pwmgr.core import PasswordStorage

   class TestSecurity:
       def test_encryption_integrity(self):
           """测试加密完整性"""
           data = "sensitive_password_data"
           password = "master_password"

           encrypted = EncryptionService.encrypt_password_data(data, password)
           decrypted = EncryptionService.decrypt_password_data(encrypted, password)

           assert decrypted == data

       def test_wrong_password_fails(self):
           """测试错误密码失败"""
           data = "sensitive_password_data"
           password = "master_password"
           wrong_password = "wrong_password"

           encrypted = EncryptionService.encrypt_password_data(data, password)
           decrypted = EncryptionService.decrypt_password_data(encrypted, wrong_password)

           assert decrypted is None

       def test_file_permissions(self, temp_storage, master_password):
           """测试文件权限设置"""
           temp_storage.save([], master_password)

           import stat
           file_stat = os.stat(temp_storage.file_path)
           permissions = stat.S_IMODE(file_stat.st_mode)

           # 检查文件权限（应该是600，只有所有者可读写）
           assert permissions == 0o600, f"文件权限不安全: {oct(permissions)}"
   ```

#### 验证标准
- [ ] 测试覆盖率达到 80%+
- [ ] 所有测试通过CI/CD
- [ ] 性能基准测试通过
- [ ] 安全测试全部通过
- [ ] 集成测试覆盖主要场景

#### 负责人
- [ ] 测试工程师
- [ ] 开发团队

---

### 3. API文档生成
**优先级**: 🟡 **MEDIUM**
**影响**: 缺少开发者级文档，影响可维护性
**预计工时**: 12小时

#### 任务描述
创建完整的API文档，包括模块文档、使用示例和架构说明。

#### 执行步骤
1. **配置Sphinx文档**
   ```python
   # docs/conf.py
   import os
   import sys
   sys.path.insert(0, os.path.abspath('..'))

   project = 'PassMgr'
   copyright = '2024, PassMgr Team'
   author = 'PassMgr Team'

   extensions = [
       'sphinx.ext.autodoc',
       'sphinx.ext.viewcode',
       'sphinx.ext.napoleon',  # 支持Google/NumPy风格docstring
       'sphinx.ext.intersphinx',
   ]

   html_theme = 'sphinx_rtd_theme'
   html_static_path = ['_static']

   # 自动文档配置
   autodoc_default_options = {
       'members': True,
       'member-order': 'bysource',
       'special-members': '__init__',
       'undoc-members': True,
       'exclude-members': '__weakref__'
   }
   ```

2. **创建模块文档**
   ```rst
   # docs/api/crypto.rst
   Cryptography Module
   ===================

   .. automodule:: pwmgr.crypto
      :members:
      :undoc-members:
      :show-inheritance:

   EncryptionService
   -----------------

   .. autoclass:: pwmgr.crypto.encryption.EncryptionService
      :members:
      :undoc-members:
      :show-inheritance:
   ```

3. **创建使用示例**
   ```python
   # docs/examples/basic_usage.py
   """
   PassMgr基本使用示例
   """
   from pwmgr.core import PasswordEntry, PasswordStorage, PasswordGenerator

   # 创建密码条目
   entry = PasswordEntry(
       name="GitHub",
       username="user@example.com",
       password="generated_password_123",
       notes="Main GitHub account"
   )

   # 初始化存储
   storage = PasswordStorage()
   master_password = "your_master_password"

   # 保存条目
   storage.save([entry], master_password)

   # 加载条目
   entries = storage.load(master_password)
   print(f"Loaded {len(entries)} entries")

   # 生成密码
   new_password = PasswordGenerator.generate(
       length=20,
       include_symbols=True
   )
   print(f"Generated password: {new_password}")
   ```

4. **创建架构文档**
   ```rst
   # docs/architecture.rst
   Architecture Overview
   =====================

   PassMgr采用三层架构设计：

   Core Layer
   -----------
   核心业务逻辑层，包含：
   - PasswordEntry: 密码条目数据模型
   - PasswordStorage: 存储管理
   - PasswordGenerator: 密码生成

   Crypto Layer
   ------------
   加密服务层，负责：
   - AES-256-CBC加密
   - PBKDF2密钥派生
   - 安全的随机数生成

   CLI Layer
   ---------
   命令行界面层，提供：
   - Click命令接口
   - 交互式Shell
   - 用户交互逻辑
   ```

#### 验证标准
- [ ] Sphinx文档配置完成
- [ ] 所有模块都有API文档
- [ ] 使用示例可正常运行
- [ ] 文档网站可正常构建
- [ ] 文档部署到ReadTheDocs

#### 负责人
- [ ] 技术文档工程师
- [ ] 开发团队

---

### 4. 错误处理改进
**优先级**: 🟡 **MEDIUM**
**影响**: 错误处理不一致，用户体验差
**预计工时**: 8小时

#### 任务描述
统一错误处理机制，提供更好的错误信息和恢复选项。

#### 执行步骤
1. **扩展异常体系**
   ```python
   # pwmgr/core/exceptions.py
   class PasswordManagerException(Exception):
       """基础异常类"""
       def __init__(self, message: str, error_code: str = None):
           super().__init__(message)
           self.error_code = error_code
           self.message = message

   class AuthenticationError(PasswordManagerException):
       """认证失败"""
       pass

   class StorageError(PasswordManagerException):
       """存储操作失败"""
       pass

   class EntryNotFoundError(PasswordManagerException):
       """条目未找到"""
       pass

   class ConfigurationError(PasswordManagerException):
       """配置错误"""
       pass

   class ValidationError(PasswordManagerException):
       """数据验证失败"""
       pass
   ```

2. **创建错误处理装饰器**
   ```python
   # pwmgr/core/error_handlers.py
   import functools
   import logging
   from typing import Callable, Any
   from .exceptions import PasswordManagerException

   logger = logging.getLogger(__name__)

   def handle_errors(func: Callable) -> Callable:
       """统一错误处理装饰器"""
       @functools.wraps(func)
       def wrapper(*args, **kwargs) -> Any:
           try:
               return func(*args, **kwargs)
           except PasswordManagerException as e:
               logger.error(f"Password manager error in {func.__name__}: {e}")
               raise  # 重新抛出已知异常
           except Exception as e:
               logger.error(f"Unexpected error in {func.__name__}: {e}")
               raise PasswordManagerException(f"An unexpected error occurred: {str(e)}")
       return wrapper

   def cli_error_handler(func: Callable) -> Callable:
       """CLI错误处理装饰器"""
       @functools.wraps(func)
       def wrapper(*args, **kwargs) -> Any:
           try:
               return func(*args, **kwargs)
           except AuthenticationError as e:
               click.secho(f"Authentication failed: {e}", fg="red", bold=True)
               sys.exit(1)
           except EntryNotFoundError as e:
               click.secho(f"Entry not found: {e}", fg="yellow")
               sys.exit(1)
           except StorageError as e:
               click.secho(f"Storage error: {e}", fg="red", bold=True)
               sys.exit(1)
           except PasswordManagerException as e:
               click.secho(f"Error: {e}", fg="red")
               sys.exit(1)
           except KeyboardInterrupt:
               click.secho("\nOperation cancelled by user.", fg="yellow")
               sys.exit(130)
           except Exception as e:
               click.secho(f"Unexpected error: {e}", fg="red", bold=True)
               logger.exception("Unexpected CLI error")
               sys.exit(1)
       return wrapper
   ```

3. **改进用户错误信息**
   ```python
   # 在各个服务中添加更好的错误处理
   class PasswordService:
       @handle_errors
       def add_entry(self, entry: PasswordEntry, master_password: str) -> None:
           # 验证条目
           if not entry.name.strip():
               raise ValidationError("Entry name cannot be empty")

           if not entry.username.strip():
               raise ValidationError("Username cannot be empty")

           # 检查重复
           existing_entries = self.get_entries(master_password)
           if any(e.name.lower() == entry.name.lower() for e in existing_entries):
               raise ValidationError(f"Entry with name '{entry.name}' already exists")

           # 保存条目
           try:
               all_entries = existing_entries + [entry]
               self.storage.save(all_entries, master_password)
           except Exception as e:
               raise StorageError(f"Failed to save entry: {str(e)}")
   ```

#### 验证标准
- [ ] 异常体系完整
- [ ] 错误处理装饰器实现
- [ ] 所有已知异常都有友好提示
- [ ] 错误日志记录完整
- [ ] 异常恢复机制合理

#### 负责人
- [ ] 开发工程师
- [ ] UX设计师

---

## 📊 P2 任务总览

| 任务 | 状态 | 预计工时 | 负责人 | 优先级 | 截止日期 |
|------|------|----------|--------|--------|----------|
| 项目现代化迁移 | ⏳ 待开始 | 16小时 | DevOps团队 | MEDIUM | 4周内 |
| 测试框架升级 | ⏳ 待开始 | 24小时 | 测试团队 | MEDIUM | 4周内 |
| API文档生成 | ⏳ 待开始 | 12小时 | 文档团队 | MEDIUM | 3周内 |
| 错误处理改进 | ⏳ 待开始 | 8小时 | 开发团队 | MEDIUM | 3周内 |

**总预计工时**: 60小时
**目标完成日期**: 4周内

---

## 🎯 P2 阶段成功标准

P2 阶段成功完成的标准：
- [ ] 项目配置完全现代化（pyproject.toml）
- [ ] 测试覆盖率达到 80%+
- [ ] 完整的API文档可用
- [ ] 统一的错误处理机制
- [ ] 开发工具链集成完成
- [ ] 代码质量评分提升至 8.5+
- [ ] 开发者体验显著改善

---

## 🔄 依赖关系

1. **项目现代化** → **测试框架升级** (使用新的配置)
2. **错误处理改进** → **测试框架升级** (更好的异常测试)
3. **API文档** → **项目现代化** (文档配置在新系统中)

---

## 📈 质量指标目标

| 指标 | 当前值 | 目标值 | 测量方法 |
|------|--------|--------|----------|
| 测试覆盖率 | 30% | 80%+ | pytest-cov |
| 代码质量评分 | 7.2 | 8.5+ | SonarQube |
| 文档覆盖率 | 40% | 85%+ | Sphinx文档统计 |
| 开发工具集成 | 低 | 完整 | pre-commit检查 |
| 错误处理一致性 | 60% | 95%+ | 异常处理分析 |

*最后更新: 2025-11-08*