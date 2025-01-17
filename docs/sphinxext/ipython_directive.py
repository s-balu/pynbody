r"""Sphinx directive to support embedded IPython code.

This directive allows pasting of entire interactive IPython sessions, prompts
and all, and their code will actually get re-executed at doc build time, with
all prompts renumbered sequentially. It also allows you to input code as a pure
python input by giving the argument python to the directive. The output looks
like an interactive ipython section.

To enable this directive, simply list it in your Sphinx ``conf.py`` file
(making sure the directory where you placed it is visible to sphinx, as is
needed for all Sphinx directives).

By default this directive assumes that your prompts are unchanged IPython ones,
but this can be customized. The configurable options that can be placed in
conf.py are

ipython_savefig_dir:
    The directory in which to save the figures. This is relative to the
    Sphinx source directory. The default is `html_static_path`.
ipython_rgxin:
    The compiled regular expression to denote the start of IPython input
    lines. The default is re.compile('In \[(\d+)\]:\s?(.*)\s*'). You
    shouldn't need to change this.
ipython_rgxout:
    The compiled regular expression to denote the start of IPython output
    lines. The default is re.compile('Out\[(\d+)\]:\s?(.*)\s*'). You
    shouldn't need to change this.
ipython_promptin:
    The string to represent the IPython input prompt in the generated ReST.
    The default is 'In [%d]:'. This expects that the line numbers are used
    in the prompt.
ipython_promptout:

    The string to represent the IPython prompt in the generated ReST. The
    default is 'Out [%d]:'. This expects that the line numbers are used
    in the prompt.

ToDo
----

- Turn the ad-hoc test() function into a real test suite.
- Break up ipython-specific functionality from matplotlib stuff into better
  separated code.

Authors
-------

- John D Hunter: orignal author.
- Fernando Perez: refactoring, documentation, cleanups, port to 0.11.
- VáclavŠmilauer <eudoxos-AT-arcig.cz>: Prompt generalizations.
- Skipper Seabold, refactoring, cleanups, pure python addition
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import cStringIO
import os
import re
import sys
import tempfile
import ast

# To keep compatibility with various python versions
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

# Third-party
import matplotlib
import sphinx
from docutils.parsers.rst import directives
from docutils import nodes
from sphinx.util.compat import Directive

matplotlib.use('Agg')

# Our own
from IPython import Config, InteractiveShell
from IPython.core.profiledir import ProfileDir
from IPython.utils import io

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
# for tokenizing blocks
COMMENT, INPUT, OUTPUT =  range(3)

#-----------------------------------------------------------------------------
# Functions and class declarations
#-----------------------------------------------------------------------------
def block_parser(part, rgxin, rgxout, fmtin, fmtout):
    """
    part is a string of ipython text, comprised of at most one
    input, one ouput, comments, and blank lines.  The block parser
    parses the text into a list of::

      blocks = [ (TOKEN0, data0), (TOKEN1, data1), ...]

    where TOKEN is one of [COMMENT | INPUT | OUTPUT ] and
    data is, depending on the type of token::

      COMMENT : the comment string

      INPUT: the (DECORATOR, INPUT_LINE, REST) where
         DECORATOR: the input decorator (or None)
         INPUT_LINE: the input as string (possibly multi-line)
         REST : any stdout generated by the input line (not OUTPUT)


      OUTPUT: the output string, possibly multi-line
    """

    block = []
    lines = part.split('\n')
    N = len(lines)
    i = 0
    decorator = None
    while 1:

        if i==N:
            # nothing left to parse -- the last line
            break

        line = lines[i]
        i += 1
        line_stripped = line.strip()
        if line_stripped.startswith('#'):
            block.append((COMMENT, line))
            continue

        if line_stripped.startswith('@'):
            # we're assuming at most one decorator -- may need to
            # rethink
            decorator = line_stripped
            continue

        # does this look like an input line?
        matchin = rgxin.match(line)
        if matchin:
            lineno, inputline = int(matchin.group(1)), matchin.group(2)

            # the ....: continuation string
            continuation = '   %s:'%''.join(['.']*(len(str(lineno))+2))
            Nc = len(continuation)
            # input lines can continue on for more than one line, if
            # we have a '\' line continuation char or a function call
            # echo line 'print'.  The input line can only be
            # terminated by the end of the block or an output line, so
            # we parse out the rest of the input line if it is
            # multiline as well as any echo text

            rest = []
            while i<N:

                # look ahead; if the next line is blank, or a comment, or
                # an output line, we're done

                nextline = lines[i]
                matchout = rgxout.match(nextline)
                #print "nextline=%s, continuation=%s, starts=%s"%(nextline, continuation, nextline.startswith(continuation))
                if matchout or nextline.startswith('#'):
                    break
                elif nextline.startswith(continuation):
                    inputline += '\n' + nextline[Nc:]
                else:
                    rest.append(nextline)
                i+= 1

            block.append((INPUT, (decorator, inputline, '\n'.join(rest))))
            continue

        # if it looks like an output line grab all the text to the end
        # of the block
        matchout = rgxout.match(line)
        if matchout:
            lineno, output = int(matchout.group(1)), matchout.group(2)
            if i<N-1:
                output = '\n'.join([output] + lines[i:])

            block.append((OUTPUT, output))
            break

    return block

class EmbeddedSphinxShell(object):
    """An embedded IPython instance to run inside Sphinx"""

    def __init__(self):

        self.cout = cStringIO.StringIO()


        # Create config object for IPython
        config = Config()
        config.Global.display_banner = False
        config.Global.exec_lines = ['import numpy as np',
                                    'from pylab import *'
                                    ]
        config.InteractiveShell.autocall = False
        config.InteractiveShell.autoindent = False
        config.InteractiveShell.colors = 'NoColor'

        # create a profile so instance history isn't saved
        tmp_profile_dir = tempfile.mkdtemp(prefix='profile_')
        profname = 'auto_profile_sphinx_build'
        pdir = os.path.join(tmp_profile_dir,profname)
        profile = ProfileDir.create_profile_dir(pdir)

        # Create and initialize ipython, but don't start its mainloop
        IP = InteractiveShell.instance(config=config, profile_dir=profile)
        # io.stdout redirect must be done *after* instantiating InteractiveShell
        io.stdout = self.cout
        io.stderr = self.cout

        # For debugging, so we can see normal output, use this:
        #from IPython.utils.io import Tee
        #io.stdout = Tee(self.cout, channel='stdout') # dbg
        #io.stderr = Tee(self.cout, channel='stderr') # dbg

        # Store a few parts of IPython we'll need.
        self.IP = IP
        self.user_ns = self.IP.user_ns
        self.user_global_ns = self.IP.user_global_ns

        self.input = ''
        self.output = ''

        self.is_verbatim = False
        self.is_doctest = False
        self.is_suppress = False

        # on the first call to the savefig decorator, we'll import
        # pyplot as plt so we can make a call to the plt.gcf().savefig
        self._pyplot_imported = False

    def clear_cout(self):
        self.cout.seek(0)
        self.cout.truncate(0)

    def process_input_line(self, line, store_history=True):
        """process the input, capturing stdout"""
        #print "input='%s'"%self.input
        stdout = sys.stdout
        stderr = sys.stderr
        splitter = self.IP.input_splitter
        try:
            sys.stdout = self.cout
            sys.stderr = self.cout
            splitter.push(line)
            more = splitter.push_accepts_more()
            if not more:
                try:
                    source_raw = splitter.source_raw_reset()[1]
                except AttributeError:
                    source_raw = splitter.raw_reset()
                self.IP.run_cell(source_raw, store_history=store_history)
        finally:
            sys.stdout = stdout
            sys.stderr = stderr

    def process_image(self, decorator):
        """
        # build out an image directive like
        # .. image:: somefile.png
        #    :width 4in
        #
        # from an input like
        # savefig somefile.png width=4in
        """
        savefig_dir = self.savefig_dir
        source_dir = self.source_dir
        saveargs = decorator.split(' ')
        filename = saveargs[1]
        # insert relative path to image file in source
        outfile = os.path.relpath(os.path.join(savefig_dir,filename),
                    source_dir)

        imagerows = ['.. image:: %s'%outfile]

        for kwarg in saveargs[2:]:
            arg, val = kwarg.split('=')
            arg = arg.strip()
            val = val.strip()
            imagerows.append('   :%s: %s'%(arg, val))

        image_file = os.path.basename(outfile) # only return file name
        image_directive = '\n'.join(imagerows)
        return image_file, image_directive


    # Callbacks for each type of token
    def process_input(self, data, input_prompt, lineno):
        """Process data block for INPUT token."""
        decorator, input, rest = data
        image_file = None
        image_directive = None
        #print 'INPUT:', data  # dbg
        is_verbatim = decorator=='@verbatim' or self.is_verbatim
        is_doctest = decorator=='@doctest' or self.is_doctest
        is_suppress = decorator=='@suppress' or self.is_suppress
        is_savefig = decorator is not None and \
                     decorator.startswith('@savefig')

        input_lines = input.split('\n')
        if len(input_lines) > 1:
            if input_lines[-1] != "":
                input_lines.append('') # make sure there's a blank line
                                       # so splitter buffer gets reset

        continuation = '   %s:'%''.join(['.']*(len(str(lineno))+2))
        Nc = len(continuation)

        if is_savefig:
            image_file, image_directive = self.process_image(decorator)

        ret = []
        is_semicolon = False

        for i, line in enumerate(input_lines):
            if line.endswith(';'):
                is_semicolon = True

            if i==0:
                # process the first input line
                if is_verbatim:
                    self.process_input_line('')
                    self.IP.execution_count += 1 # increment it anyway
                else:
                    # only submit the line in non-verbatim mode
                    self.process_input_line(line, store_history=True)
                formatted_line = '%s %s'%(input_prompt, line)
            else:
                # process a continuation line
                if not is_verbatim:
                    self.process_input_line(line, store_history=True)

                formatted_line = '%s %s'%(continuation, line)

            if not is_suppress:
                ret.append(formatted_line)

        if not is_suppress and len(rest.strip()) and is_verbatim:
            # the "rest" is the standard output of the
            # input, which needs to be added in
            # verbatim mode
            ret.append(rest)

        self.cout.seek(0)
        output = self.cout.read()
        if not is_suppress and not is_semicolon:
            ret.append(output)
        elif is_semicolon: # get spacing right
            ret.append('')

        self.cout.truncate(0)
        return (ret, input_lines, output, is_doctest, image_file,
                    image_directive)
        #print 'OUTPUT', output  # dbg

    def process_output(self, data, output_prompt,
                       input_lines, output, is_doctest, image_file):
        """Process data block for OUTPUT token."""
        if is_doctest:
            submitted = data.strip()
            found = output
            if found is not None:
                found = found.strip()

                # XXX - fperez: in 0.11, 'output' never comes with the prompt
                # in it, just the actual output text.  So I think all this code
                # can be nuked...

                # the above comment does not appear to be accurate... (minrk)

                ind = found.find(output_prompt)
                if ind<0:
                    e='output prompt="%s" does not match out line=%s' % \
                       (output_prompt, found)
                    raise RuntimeError(e)
                found = found[len(output_prompt):].strip()

                if found!=submitted:
                    e = ('doctest failure for input_lines="%s" with '
                         'found_output="%s" and submitted output="%s"' %
                         (input_lines, found, submitted) )
                    raise RuntimeError(e)
                #print 'doctest PASSED for input_lines="%s" with found_output="%s" and submitted output="%s"'%(input_lines, found, submitted)

    def process_comment(self, data):
        """Process data fPblock for COMMENT token."""
        if not self.is_suppress:
            return [data]

    def save_image(self, image_file):
        """
        Saves the image file to disk.
        """
        self.ensure_pyplot()
        command = 'plt.gcf().savefig("%s")'%image_file
        #print 'SAVEFIG', command  # dbg
        self.process_input_line('bookmark ipy_thisdir', store_history=False)
        self.process_input_line('cd -b ipy_savedir', store_history=False)
        self.process_input_line(command, store_history=False)
        self.process_input_line('cd -b ipy_thisdir', store_history=False)
        self.process_input_line('bookmark -d ipy_thisdir', store_history=False)
        self.clear_cout()


    def process_block(self, block):
        """
        process block from the block_parser and return a list of processed lines
        """
        ret = []
        output = None
        input_lines = None
        lineno = self.IP.execution_count

        input_prompt = self.promptin%lineno
        output_prompt = self.promptout%lineno
        image_file = None
        image_directive = None
        is_doctest = False

        for token, data in block:
            if token==COMMENT:
                out_data = self.process_comment(data)
            elif token==INPUT:
                (out_data, input_lines, output, is_doctest, image_file,
                    image_directive) = \
                          self.process_input(data, input_prompt, lineno)
            elif token==OUTPUT:
                out_data = \
                    self.process_output(data, output_prompt,
                                        input_lines, output, is_doctest,
                                        image_file)
            if out_data:
                ret.extend(out_data)

        # save the image files
        if image_file is not None:
            self.save_image(image_file)

        return ret, image_directive

    def ensure_pyplot(self):
        if self._pyplot_imported:
            return
        self.process_input_line('import matplotlib.pyplot as plt',
                                store_history=False)

    def process_pure_python(self, content):
        """
        content is a list of strings. it is unedited directive conent

        This runs it line by line in the InteractiveShell, prepends
        prompts as needed capturing stderr and stdout, then returns
        the content as a list as if it were ipython code
        """
        output = []
        savefig = False # keep up with this to clear figure
        multiline = False # to handle line continuation
        multiline_start = None
        fmtin = self.promptin

        ct = 0

        for lineno, line in enumerate(content):

            line_stripped = line.strip()
            if not len(line):
                output.append(line)
                continue

            # handle decorators
            if line_stripped.startswith('@'):
                output.extend([line])
                if 'savefig' in line:
                    savefig = True # and need to clear figure
                continue

            # handle comments
            if line_stripped.startswith('#'):
                output.extend([line])
                continue

            # deal with lines checking for multiline
            continuation  = '   %s:'% ''.join(['.']*(len(str(ct))+2))
            if not multiline:
                modified = "%s %s" % (fmtin % ct, line_stripped)
                output.append(modified)
                ct += 1
                try:
                    ast.parse(line_stripped)
                    output.append('')
                except Exception: # on a multiline
                    multiline = True
                    multiline_start = lineno
            else: # still on a multiline
                modified = '%s %s' % (continuation, line)
                output.append(modified)
                try:
                    mod = ast.parse(
                            '\n'.join(content[multiline_start:lineno+1]))
                    if isinstance(mod.body[0], ast.FunctionDef):
                        # check to see if we have the whole function
                        for element in mod.body[0].body:
                            if isinstance(element, ast.Return):
                                multiline = False
                    else:
                        output.append('')
                        multiline = False
                except Exception:
                    pass

            if savefig: # clear figure if plotted
                self.ensure_pyplot()
                self.process_input_line('plt.clf()', store_history=False)
                self.clear_cout()
                savefig = False

        return output

class IpythonDirective(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 4 # python, suppress, verbatim, doctest
    final_argumuent_whitespace = True
    option_spec = { 'python': directives.unchanged,
                    'suppress' : directives.flag,
                    'verbatim' : directives.flag,
                    'doctest' : directives.flag,
                  }

    shell = EmbeddedSphinxShell()

    def get_config_options(self):
        # contains sphinx configuration variables
        config = self.state.document.settings.env.config

        # get config variables to set figure output directory
        confdir = self.state.document.settings.env.app.confdir
        savefig_dir = config.ipython_savefig_dir
        source_dir = os.path.dirname(self.state.document.current_source)
        if savefig_dir is None:
            savefig_dir = config.html_static_path
        if isinstance(savefig_dir, list):
            savefig_dir = savefig_dir[0] # safe to assume only one path?
        savefig_dir = os.path.join(confdir, savefig_dir)

        # get regex and prompt stuff
        rgxin     = config.ipython_rgxin
        rgxout    = config.ipython_rgxout
        promptin  = config.ipython_promptin
        promptout = config.ipython_promptout

        return savefig_dir, source_dir, rgxin, rgxout, promptin, promptout

    def setup(self):
        # reset the execution count if we haven't processed this doc
        #NOTE: this may be borked if there are multiple seen_doc tmp files
        #check time stamp?
        seen_docs = [i for i in os.listdir(tempfile.tempdir)
            if i.startswith('seen_doc')]
        if not hasattr(self.shell, "_docs") :
            self.shell._docs = []

        if seen_docs:
            fname = os.path.join(tempfile.tempdir, seen_docs[0])
            docs = open(fname).read().split('\n')
            docs = self.shell._docs # AP modification - seems more reliable (?!)
            if not self.state.document.current_source in docs:
                self.shell.IP.history_manager.reset()
                self.shell.IP.execution_count = 1
        else: # haven't processed any docs yet
            docs = []


        # get config values
        (savefig_dir, source_dir, rgxin,
                rgxout, promptin, promptout) = self.get_config_options()

        # and attach to shell so we don't have to pass them around
        self.shell.rgxin = rgxin
        self.shell.rgxout = rgxout
        self.shell.promptin = promptin
        self.shell.promptout = promptout
        self.shell.savefig_dir = savefig_dir
        self.shell.source_dir = source_dir

        # setup bookmark for saving figures directory

        self.shell.process_input_line('bookmark ipy_savedir %s'%savefig_dir,
                                      store_history=False)
        self.shell.clear_cout()

        # write the filename to a tempfile because it's been "seen" now
        if not self.state.document.current_source in docs:
            fd, fname = tempfile.mkstemp(prefix="seen_doc", text=True)
            fout = open(fname, 'a')
            fout.write(self.state.document.current_source+'\n')
            fout.close()
            self.shell._docs.append(self.state.document.current_source) # AP modification

        return rgxin, rgxout, promptin, promptout


    def teardown(self):
        # delete last bookmark
        self.shell.process_input_line('bookmark -d ipy_savedir',
                                      store_history=False)
        self.shell.clear_cout()

    def run(self):
        debug = False

        #TODO, any reason block_parser can't be a method of embeddable shell
        # then we wouldn't have to carry these around
        rgxin, rgxout, promptin, promptout = self.setup()

        options = self.options
        self.shell.is_suppress = 'suppress' in options
        self.shell.is_doctest = 'doctest' in options
        self.shell.is_verbatim = 'verbatim' in options


        # handle pure python code
        if 'python' in self.arguments:
            content = self.content
            self.content = self.shell.process_pure_python(content)

        parts = '\n'.join(self.content).split('\n\n')

        lines = ['.. code-block:: ipython','']
        figures = []

        for part in parts:

            block = block_parser(part, rgxin, rgxout, promptin, promptout)

            if len(block):
                rows, figure = self.shell.process_block(block)
                for row in rows:
                    lines.extend(['   %s'%line for line in row.split('\n')])

                if figure is not None:
                    figures.append(figure)

        #text = '\n'.join(lines)
        #figs = '\n'.join(figures)

        for figure in figures:
            lines.append('')
            lines.extend(figure.split('\n'))
            lines.append('')

        #print lines
        if len(lines)>2:
            if debug:
                print '\n'.join(lines)
            else: #NOTE: this raises some errors, what's it for?
                #print 'INSERTING %d lines'%len(lines)
                self.state_machine.insert_input(
                    lines, self.state_machine.input_lines.source(0))

        text = '\n'.join(lines)
        txtnode = nodes.literal_block(text, text)
        txtnode['language'] = 'ipython'
        #imgnode = nodes.image(figs)

        # cleanup
        self.teardown()

        return []#, imgnode]

# Enable as a proper Sphinx directive
def setup(app):
    setup.app = app

    app.add_directive('ipython', IpythonDirective)
    app.add_config_value('ipython_savefig_dir', None, True)
    app.add_config_value('ipython_rgxin',
                         re.compile(r'In \[(\d+)\]:\s?(.*)\s*'), True)
    app.add_config_value('ipython_rgxout',
                         re.compile(r'Out\[(\d+)\]:\s?(.*)\s*'), True)
    app.add_config_value('ipython_promptin', 'In [%d]:', True)
    app.add_config_value('ipython_promptout', 'Out[%d]:', True)


# Simple smoke test, needs to be converted to a proper automatic test.
def test():

    examples = [
        r"""
In [9]: pwd
Out[9]: '/home/jdhunter/py4science/book'

In [10]: cd bookdata/
/home/jdhunter/py4science/book/bookdata

In [2]: from pylab import *

In [2]: ion()

In [3]: im = imread('stinkbug.png')

@savefig mystinkbug.png width=4in
In [4]: imshow(im)
Out[4]: <matplotlib.image.AxesImage object at 0x39ea850>

""",
        r"""

In [1]: x = 'hello world'

# string methods can be
# used to alter the string
@doctest
In [2]: x.upper()
Out[2]: 'HELLO WORLD'

@verbatim
In [3]: x.st<TAB>
x.startswith  x.strip
""",
    r"""

In [130]: url = 'http://ichart.finance.yahoo.com/table.csv?s=CROX\
   .....: &d=9&e=22&f=2009&g=d&a=1&br=8&c=2006&ignore=.csv'

In [131]: print url.split('&')
['http://ichart.finance.yahoo.com/table.csv?s=CROX', 'd=9', 'e=22', 'f=2009', 'g=d', 'a=1', 'b=8', 'c=2006', 'ignore=.csv']

In [60]: import urllib

""",
    r"""\

In [133]: import numpy.random

@suppress
In [134]: numpy.random.seed(2358)

@doctest
In [135]: numpy.random.rand(10,2)
Out[135]:
array([[ 0.64524308,  0.59943846],
       [ 0.47102322,  0.8715456 ],
       [ 0.29370834,  0.74776844],
       [ 0.99539577,  0.1313423 ],
       [ 0.16250302,  0.21103583],
       [ 0.81626524,  0.1312433 ],
       [ 0.67338089,  0.72302393],
       [ 0.7566368 ,  0.07033696],
       [ 0.22591016,  0.77731835],
       [ 0.0072729 ,  0.34273127]])

""",

    r"""
In [106]: print x
jdh

In [109]: for i in range(10):
   .....:     print i
   .....:
   .....:
0
1
2
3
4
5
6
7
8
9
""",

        r"""

In [144]: from pylab import *

In [145]: ion()

# use a semicolon to suppress the output
@savefig test_hist.png width=4in
In [151]: hist(np.random.randn(10000), 100);


@savefig test_plot.png width=4in
In [151]: plot(np.random.randn(10000), 'o');
   """,

        r"""
# use a semicolon to suppress the output
In [151]: plt.clf()

@savefig plot_simple.png width=4in
In [151]: plot([1,2,3])

@savefig hist_simple.png width=4in
In [151]: hist(np.random.randn(10000), 100);

""",
     r"""
# update the current fig
In [151]: ylabel('number')

In [152]: title('normal distribution')


@savefig hist_with_text.png
In [153]: grid(True)

        """,
        ]
    # skip local-file depending first example:
    examples = examples[1:]

    #ipython_directive.DEBUG = True  # dbg
    #options = dict(suppress=True)  # dbg
    options = dict()
    for example in examples:
        content = example.split('\n')
        ipython_directive('debug', arguments=None, options=options,
                          content=content, lineno=0,
                          content_offset=None, block_text=None,
                          state=None, state_machine=None,
                          )

# Run test suite as a script
if __name__=='__main__':
    if not os.path.isdir('_static'):
        os.mkdir('_static')
    test()
    print 'All OK? Check figures in _static/'
