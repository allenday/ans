"""Test cases for command handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from chronicler.exceptions import CommandStorageError, CommandValidationError
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.handlers.command import StartCommandHandler, ConfigCommandHandler, StatusCommandHandler
from tests.mocks.commands import command_frame_factory, coordinator_mock, TEST_METADATA

class TestStartCommandHandler:
    """Test cases for StartCommandHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self, coordinator_mock, command_frame_factory):
        """Test successful start command handling."""
        handler = StartCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = False
        frame = command_frame_factory(command="/start")

        result = await handler.handle(frame)
        assert isinstance(result, TextFrame)
        assert "Storage initialized successfully" in result.content
        coordinator_mock.init_storage.assert_awaited_once()
        coordinator_mock.create_topic.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_init_error(self, coordinator_mock, command_frame_factory):
        """Test error handling when initialization fails."""
        handler = StartCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = False
        coordinator_mock.init_storage.side_effect = RuntimeError("Init failed")
        frame = command_frame_factory(command="/start")

        with pytest.raises(CommandStorageError, match="Failed to initialize storage: Init failed"):
            await handler.handle(frame)

    @pytest.mark.asyncio
    async def test_handle_create_topic_error(self, coordinator_mock, command_frame_factory):
        """Test error handling when topic creation fails."""
        handler = StartCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = False
        coordinator_mock.create_topic.side_effect = RuntimeError("Topic creation failed")
        frame = command_frame_factory(command="/start")

        with pytest.raises(CommandStorageError, match="Failed to create topic: Topic creation failed"):
            await handler.handle(frame)

class TestConfigCommandHandler:
    """Test cases for ConfigCommandHandler."""

    @pytest.mark.asyncio
    async def test_handle_missing_args(self, coordinator_mock, command_frame_factory):
        """Test handling when arguments are missing."""
        handler = ConfigCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = True
        frame = command_frame_factory(command="/config")

        with pytest.raises(CommandValidationError, match="Missing required arguments"):
            await handler.handle(frame)

    @pytest.mark.asyncio
    async def test_handle_success(self, coordinator_mock, command_frame_factory):
        """Test successful config command handling."""
        handler = ConfigCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = True
        frame = command_frame_factory(
            command="/config",
            args=["user/repo", "ghp_token123"]
        )

        result = await handler.handle(frame)
        assert isinstance(result, TextFrame)
        assert "GitHub configuration" in result.content
        coordinator_mock.set_github_config.assert_awaited_once_with(
            token="ghp_token123",
            repo="user/repo"
        )

    @pytest.mark.asyncio
    async def test_handle_config_error(self, coordinator_mock, command_frame_factory):
        """Test error handling when configuration fails."""
        handler = ConfigCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = True
        coordinator_mock.set_github_config.side_effect = RuntimeError("Config failed")
        frame = command_frame_factory(
            command="/config",
            args=["user/repo", "ghp_token123"]
        )

        with pytest.raises(CommandStorageError, match="Failed to configure GitHub: Config failed"):
            await handler.handle(frame)

    @pytest.mark.asyncio
    async def test_handle_sync_error(self, coordinator_mock, command_frame_factory):
        """Test error handling when sync fails."""
        handler = ConfigCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = True
        coordinator_mock.sync.side_effect = RuntimeError("Sync failed")
        frame = command_frame_factory(
            command="/config",
            args=["user/repo", "ghp_token123"]
        )

        with pytest.raises(CommandStorageError, match="Failed to sync repository: Sync failed"):
            await handler.handle(frame)

class TestStatusCommandHandler:
    """Test cases for StatusCommandHandler."""

    @pytest.mark.asyncio
    async def test_handle_not_initialized(self, coordinator_mock, command_frame_factory):
        """Test handling when storage is not initialized."""
        handler = StatusCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = False
        frame = command_frame_factory(command="/status")

        with pytest.raises(CommandValidationError, match="Storage not initialized"):
            await handler.handle(frame)

    @pytest.mark.asyncio
    async def test_handle_success(self, coordinator_mock, command_frame_factory):
        """Test successful status command handling."""
        handler = StatusCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = True
        frame = command_frame_factory(command="/status")

        result = await handler.handle(frame)
        assert isinstance(result, TextFrame)
        assert "status" in result.content.lower()
        coordinator_mock.sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_sync_error(self, coordinator_mock, command_frame_factory):
        """Test error handling when sync fails."""
        handler = StatusCommandHandler(coordinator=coordinator_mock)
        coordinator_mock.is_initialized.return_value = True
        coordinator_mock.sync.side_effect = RuntimeError("Sync failed")
        frame = command_frame_factory(command="/status")

        with pytest.raises(CommandStorageError, match="Failed to sync repository: Sync failed"):
            await handler.handle(frame) 