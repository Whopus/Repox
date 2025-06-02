"""Tests for repository analysis."""

import pytest

from repox.repository import RepositoryAnalyzer


def test_repository_analyzer_init(temp_repo, test_config):
    """Test repository analyzer initialization."""
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    assert analyzer.repo_path == temp_repo.resolve()
    assert analyzer.config == test_config


def test_get_repository_structure(temp_repo, test_config):
    """Test getting repository structure."""
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    structure = analyzer.get_repository_structure()
    
    assert isinstance(structure, str)
    assert temp_repo.name in structure
    assert "main.py" in structure
    assert "utils.py" in structure


def test_get_file_sizes(temp_repo, test_config):
    """Test getting file sizes."""
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    file_sizes = analyzer.get_file_sizes()
    
    assert isinstance(file_sizes, dict)
    assert "main.py" in file_sizes
    assert "utils.py" in file_sizes
    assert "config.json" in file_sizes
    assert "subdir/module.py" in file_sizes
    
    # Large file should be excluded due to size limit
    assert "large_file.py" not in file_sizes
    
    # Binary file should be excluded by patterns
    assert "binary.bin" not in file_sizes


def test_get_processable_files(temp_repo, test_config):
    """Test getting processable files."""
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    files = analyzer.get_processable_files()
    
    assert isinstance(files, list)
    assert "main.py" in files
    assert "utils.py" in files
    assert "config.json" in files
    assert "subdir/module.py" in files
    
    # Large file should be excluded
    assert "large_file.py" not in files


def test_validate_file_selection(temp_repo, test_config):
    """Test validating file selection."""
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    selected_files = [
        "main.py",           # Valid
        "utils.py",          # Valid
        "nonexistent.py",    # Invalid - doesn't exist
        "large_file.py",     # Invalid - too large
        "binary.bin",        # Invalid - excluded pattern
    ]
    
    valid_files, invalid_files = analyzer.validate_file_selection(selected_files)
    
    assert "main.py" in valid_files
    assert "utils.py" in valid_files
    assert len(valid_files) == 2
    
    assert len(invalid_files) == 3
    assert any("nonexistent.py" in item for item in invalid_files)
    assert any("large_file.py" in item for item in invalid_files)
    assert any("binary.bin" in item for item in invalid_files)


def test_get_repository_summary(temp_repo, test_config):
    """Test getting repository summary."""
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    summary = analyzer.get_repository_summary()
    
    assert isinstance(summary, dict)
    assert "total_files" in summary
    assert "total_size" in summary
    assert "file_types" in summary
    assert "largest_files" in summary
    assert "repository_path" in summary
    
    assert summary["total_files"] > 0
    assert summary["total_size"] > 0
    assert str(temp_repo) == summary["repository_path"]


def test_exclude_patterns(temp_repo, test_config):
    """Test that exclude patterns work correctly."""
    # Add custom exclude pattern
    test_config.exclude_patterns.append("*.json")
    
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    file_sizes = analyzer.get_file_sizes()
    
    # JSON file should be excluded
    assert "config.json" not in file_sizes
    
    # Python files should still be included
    assert "main.py" in file_sizes
    assert "utils.py" in file_sizes


def test_large_directory_detection(temp_repo, test_config):
    """Test detection of large directories."""
    # Create a directory with many files
    large_dir = temp_repo / "large_dir"
    large_dir.mkdir()
    
    # Create more files than the threshold
    for i in range(test_config.large_dir_threshold + 10):
        (large_dir / f"file_{i}.py").write_text(f"# File {i}")
    
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    # The large directory should be detected as large
    assert analyzer._is_large_directory(large_dir)
    
    # Regular directories should not be detected as large
    assert not analyzer._is_large_directory(temp_repo / "subdir")


def test_skip_large_dirs_config(temp_repo, test_config):
    """Test that configured large directory names are skipped."""
    # Create a directory with a name in skip_large_dirs
    node_modules = temp_repo / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.js").write_text("// Package file")
    
    analyzer = RepositoryAnalyzer(temp_repo, test_config)
    
    # node_modules should be detected as large directory
    assert analyzer._is_large_directory(node_modules)
    
    # Files in node_modules should not appear in processable files
    files = analyzer.get_processable_files()
    assert not any("node_modules" in f for f in files)