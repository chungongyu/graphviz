# backend.py - execute rendering, open files in viewer

import os
import sys
import errno
import platform
import subprocess

from . import tools

__all__ = ['render', 'pipe', 'view']

ENGINES = {  # http://www.graphviz.org/pdf/dot.1.pdf
    'dot', 'neato', 'twopi', 'circo', 'fdp', 'sfdp', 'patchwork', 'osage',
}

FORMATS = {  # http://www.graphviz.org/doc/info/output.html
    'bmp',
    'canon', 'dot', 'gv', 'xdot', 'xdot1.2', 'xdot1.4',
    'cgimage',
    'cmap',
    'eps',
    'exr',
    'fig',
    'gd', 'gd2',
    'gif',
    'gtk',
    'ico',
    'imap', 'cmapx',
    'imap_np', 'cmapx_np',
    'ismap',
    'jp2',
    'jpg', 'jpeg', 'jpe',
    'json', 'json0', 'dot_json', 'xdot_json',  # Graphviz 2.40
    'pct', 'pict',
    'pdf',
    'pic',
    'plain', 'plain-ext',
    'png',
    'pov',
    'ps',
    'ps2',
    'psd',
    'sgi',
    'svg', 'svgz',
    'tga',
    'tif', 'tiff',
    'tk',
    'vml', 'vmlz',
    'vrml',
    'wbmp',
    'webp',
    'xlib',
    'x11',
}

PLATFORM = platform.system().lower()

STARTUPINFO = None

if PLATFORM == 'windows':  # pragma: no cover
    STARTUPINFO = subprocess.STARTUPINFO()
    STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    STARTUPINFO.wShowWindow = subprocess.SW_HIDE


def command(engine, format, filepath=None):
    """Return args list for subprocess.Popen and name of the rendered file."""
    if engine not in ENGINES:
        raise ValueError('unknown engine: %r' % engine)
    if format not in FORMATS:
        raise ValueError('unknown format: %r' % format)

    args, rendered = [engine, '-T%s' % format], None
    if filepath is not None:
        args.extend(['-O', filepath])
        rendered = '%s.%s' % (filepath, format)

    return args, rendered


def render(engine, format, filepath):
    """Render file with Graphviz engine into format,  return result filename.

    Args:
        engine: The layout commmand used for rendering ('dot', 'neato', ...).
        format: The output format used for rendering ('pdf', 'png', ...).
        filepath: Path to the DOT source file to render.
    Returns:
        The (possibly relative) path of the rendered file.
    Raises:
        ValueError: If engine or format are not known.
        RuntimeError: If the Graphviz executable is not found.
        subprocess.CalledProcessError: If the exit status is non-zero.
    """
    args, rendered = command(engine, format, filepath)

    try:
        subprocess.check_call(args, startupinfo=STARTUPINFO)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise RuntimeError('failed to execute %r, '
                'make sure the Graphviz executables '
                'are on your systems\' path' % args)
        else:  # pragma: no cover
            raise

    return rendered


def pipe(engine, format, data, quiet=False):
    """Return data piped through Graphviz engine into format.

    Args:
        engine: The layout commmand used for rendering ('dot', 'neato', ...).
        format: The output format used for rendering ('pdf', 'png', ...).
        data: The binary (encoded) DOT source string to render.
        quiet(bool): Suppress stderr output on non-zero exit status.
    Returns:
        Binary (encoded) stdout of the layout command.
    Raises:
        ValueError: If engine or format are not known.
        RuntimeError: If the Graphviz executable is not found.
        subprocess.CalledProcessError: If the exit status is non-zero.
    """
    args, _ = command(engine, format)

    try:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=STARTUPINFO)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise RuntimeError('failed to execute %r, '
                'make sure the Graphviz executables '
                'are on your systems\' path' % args)
        else:  # pragma: no cover
            raise

    outs, errs = proc.communicate(data)
    if proc.returncode:
        if not quiet:  # pragma: no cover
            sys.stderr.write(errs)
            sys.stderr.flush()
        raise subprocess.CalledProcessError(proc.returncode, args, output=outs)

    return outs


def view(filepath):
    """Open filepath with its default viewing application (platform-specific).

    Raises:
        RuntimeError: If the current platform is not supported.
    """
    try:
        view_func = getattr(view, PLATFORM)
    except AttributeError:
        raise RuntimeError('platform %r not supported' % PLATFORM)
    view_func(filepath)


@tools.attach(view, 'darwin')
def view_darwin(filepath):
    """Open filepath with its default application (mac)."""
    subprocess.Popen(['open', filepath])


@tools.attach(view, 'linux')
@tools.attach(view, 'freebsd')
def view_unixoid(filepath):
    """Open filepath in the user's preferred application (linux, freebsd)."""
    subprocess.Popen(['xdg-open', filepath])


@tools.attach(view, 'windows')
def view_windows(filepath):
    """Start filepath with its associated application (windows)."""
    os.startfile(os.path.normpath(filepath))
