#!/usr/bin/env python3
"""
LLM CLI Tool for MCPZoo Backend

A Click-based CLI tool that allows LLMs to execute Python code within the MCPZoo backend environment.
"""

import ast, os, select, subprocess, sys, tempfile, time

from typing import Optional

import click


def validate_code(code: str) -> str:
    """Basic syntax validation."""
    try:
        ast.parse(code)
        return code
    except SyntaxError as e:
        raise ValueError(f"Syntax error in code: {e}")
    except Exception as e:
        raise ValueError(f"Error analyzing code: {e}")

def has_stdin_data() -> bool:
    """Check if stdin has data available."""
    try:
        # Check if stdin is a TTY (interactive terminal)
        if sys.stdin.isatty():
            return False
        # Use select to check if data is available
        return select.select([sys.stdin], [], [], 0)[0] != []
    except Exception:
        return False

def execute_code(code: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> dict:
    """Execute Python code and return results."""
    result = {
        'success': False,
        'stdout': '',
        'stderr': '',
        'error': None,
        'execution_time': 0.0,
        'timeout': False
    }

    start_time = time.time()

    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute the code using subprocess
            cmd = [sys.executable, temp_file]
            if cwd:
                result_proc = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                result_proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

            result['stdout'] = result_proc.stdout
            result['stderr'] = result_proc.stderr
            result['success'] = result_proc.returncode == 0
            if not result['success']:
                result['error'] = f"Process exited with code {result_proc.returncode}"

        except subprocess.TimeoutExpired:
            result['timeout'] = True
            result['error'] = f"Code execution timed out after {timeout} seconds"
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    except Exception as e:
        result['error'] = f"Execution failed: {str(e)}"

    result['execution_time'] = time.time() - start_time
    return result

@click.group()
@click.version_option(version="1.0.0", prog_name="llmcli")
def cli():
    """LLM CLI Tool for MCPZoo Backend - Execute Python code."""
    pass

@cli.command()
@click.argument('code', nargs=-1)
@click.option('--code-file', '-f', type=click.Path(exists=True), help='File containing Python code to execute')
@click.option('--stdin', '-s', is_flag=True, help='Read code from stdin')
@click.option('--cwd', type=click.Path(exists=True, file_okay=False), help='Working directory for execution')
@click.option('--timeout', type=int, help='Timeout in seconds (max 300)')
def run(code, code_file, stdin, cwd, timeout):
    """
    Execute Python code within the MCPZoo backend environment.

    CODE: Python code to execute (can be multiple arguments, will be joined with spaces).
    Use --code-file to read from a file, or --stdin to read from standard input.

    Examples:
        llmcli run "print('Hello World')"
        llmcli run --code-file script.py
        echo "import sys; print(sys.version)" | llmcli run --stdin
    """
    # Validate timeout
    if timeout and (timeout < 1 or timeout > 300):
        click.echo("Error: Timeout must be between 1 and 300 seconds", err=True)
        sys.exit(1)

    # Determine code source
    if code_file and stdin:
        click.echo("Error: Cannot specify both --code-file and --stdin", err=True)
        sys.exit(1)
    elif code_file:
        try:
            with open(code_file, 'r') as f:
                code_str = f.read()
        except Exception as e:
            click.echo(f"Error reading file: {e}", err=True)
            sys.exit(1)
    elif stdin or (not code and has_stdin_data()):
        try:
            code_str = sys.stdin.read()
        except Exception as e:
            click.echo(f"Error reading from stdin: {e}", err=True)
            sys.exit(1)
    elif code:
        code_str = ' '.join(code)
    else:
        click.echo("Error: No code provided. Use CODE argument, --code-file, or pipe code to stdin.", err=True)
        sys.exit(1)

    # Validate code
    try:
        validated_code = validate_code(code_str)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Execute code
    result = execute_code(validated_code, cwd, timeout)

    # Output stdout and stderr directly
    if result['stdout']:
        click.echo(result['stdout'], nl=False)

    if result['stderr']:
        click.echo(result['stderr'], err=True, nl=False)

    if result['error']:
        click.echo(f"Error: {result['error']}", err=True)

    # Exit with appropriate code
    sys.exit(0 if result['success'] and not result['timeout'] else 1)

@cli.command()
def version():
    """Show version information."""
    click.echo("LLM CLI Tool for MCPZoo Backend")
    click.echo("Version: 1.0.0")
    click.echo("Author: MCPZoo Team")

@cli.command()
def help_commands():
    """Show available commands and usage."""
    click.echo("LLM CLI Tool Commands:")
    click.echo("  run [OPTIONS] [CODE]...  Execute Python code")
    click.echo("  version                  Show version information")
    click.echo("  help-commands           Show available commands")
    click.echo("")
    click.echo("Usage examples:")
    click.echo("  llmcli run \"print('Hello World')\"")
    click.echo("  llmcli run --code-file script.py")
    click.echo("  echo \"import sys; print(sys.version)\" | llmcli run --stdin")

if __name__ == '__main__':
    cli()
