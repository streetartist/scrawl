"""
Game Runner

Manages running the game in a subprocess.
"""

import os
import sys
import subprocess
import tempfile
from typing import Optional

from PySide6.QtCore import QObject, Signal, QProcess, QTimer

from .code_generator import CodeGenerator
from core.i18n import tr


class GameRunner(QObject):
    """Manages game execution in a subprocess."""

    output_received = Signal(str)
    error_received = Signal(str)
    game_started = Signal()
    game_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._process: Optional[QProcess] = None
        self._temp_file: Optional[str] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def run(self, project) -> bool:
        """Run the game from the project."""
        if self._running:
            self.output_received.emit(tr("runner.already_running"))
            return False

        if not project.model or not project.path:
            self.error_received.emit(tr("runner.no_project"))
            return False

        try:
            # Generate code
            project_dir = project.project_dir
            generator = CodeGenerator(project.model, project_dir)

            # Create temp file for generated code
            fd, self._temp_file = tempfile.mkstemp(suffix='.py', prefix='scrawl_game_')
            os.close(fd)

            generator.save_generated_code(self._temp_file)
            self.output_received.emit(tr("runner.generated").format(path=self._temp_file))

            # Start process
            self._process = QProcess(self)
            self._process.setWorkingDirectory(project_dir)

            # Connect signals
            self._process.readyReadStandardOutput.connect(self._on_stdout)
            self._process.readyReadStandardError.connect(self._on_stderr)
            self._process.finished.connect(self._on_finished)
            self._process.errorOccurred.connect(self._on_error)

            # Find Python executable
            python_exe = sys.executable

            # Start the game
            self._process.start(python_exe, [self._temp_file])

            if self._process.waitForStarted(5000):
                self._running = True
                self.game_started.emit()
                self.output_received.emit(tr("runner.started"))
                return True
            else:
                self.error_received.emit(tr("runner.start_failed"))
                return False

        except Exception as e:
            self.error_received.emit(tr("runner.error").format(error=str(e)))
            return False

    def stop(self):
        """Stop the running game."""
        if self._process and self._running:
            self.output_received.emit(tr("runner.stopping"))
            self._process.terminate()

            # Give it time to terminate gracefully
            if not self._process.waitForFinished(3000):
                self._process.kill()
                self._process.waitForFinished(1000)

    def _on_stdout(self):
        """Handle stdout from the game process."""
        if self._process:
            data = self._process.readAllStandardOutput().data()
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                text = data.decode('latin-1')
            self.output_received.emit(text)

    def _on_stderr(self):
        """Handle stderr from the game process."""
        if self._process:
            data = self._process.readAllStandardError().data()
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                text = data.decode('latin-1')
            self.error_received.emit(text)

    def _on_finished(self, exit_code: int, exit_status):
        """Handle process finished."""
        self._running = False
        self.output_received.emit(tr("runner.exited").format(code=exit_code))
        self.game_stopped.emit()

        # Clean up temp file
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except OSError:
                pass
            self._temp_file = None

        self._process = None

    def _on_error(self, error):
        """Handle process error."""
        error_messages = {
            QProcess.FailedToStart: "Failed to start",
            QProcess.Crashed: "Process crashed",
            QProcess.Timedout: "Process timed out",
            QProcess.WriteError: "Write error",
            QProcess.ReadError: "Read error",
            QProcess.UnknownError: "Unknown error"
        }
        msg = error_messages.get(error, "Unknown error")
        self.error_received.emit(tr("runner.process_error").format(error=msg))


class GameDebugRunner(GameRunner):
    """Game runner with debugging support."""

    breakpoint_hit = Signal(str, int)  # file, line

    def __init__(self, parent=None):
        super().__init__(parent)
        self._breakpoints = {}

    def add_breakpoint(self, file: str, line: int):
        """Add a breakpoint."""
        if file not in self._breakpoints:
            self._breakpoints[file] = set()
        self._breakpoints[file].add(line)

    def remove_breakpoint(self, file: str, line: int):
        """Remove a breakpoint."""
        if file in self._breakpoints:
            self._breakpoints[file].discard(line)

    def clear_breakpoints(self):
        """Clear all breakpoints."""
        self._breakpoints.clear()

    def run_debug(self, project) -> bool:
        """Run the game in debug mode."""
        # For now, just run normally
        # Future: integrate with pdb or debugpy
        return self.run(project)
