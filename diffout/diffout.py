#!/usr/bin/env python3

"""diffout

Usage:
  diffout [options] [--] <commandline> <infile>...
  diffout -h | --help
  diffout --version

Runs a command on a list of input files, then compares the resulting outputs with copies stored from a previous run.

Examples:
  diffout <commandline> <infile>...

Options:
  -s, --save       Clear expected results, then save all test generated output as new expected results.
  -h, --help       Show help.
  -q, --quiet      Print less text.
  -v, --verbose    Print more text.
  --version        Show version.
"""

from docopt import docopt
import logging
import difflib
import glob
import re
import os
import shutil
import shlex
import subprocess
import time


VERSION="0.1.0" # MAJOR.MINOR.PATCH | http://semver.org


def fatal( errorMsg ):
	logging.critical(errorMsg)
	exit(1)
	return

def loadFile(fn):
	inBuf = []
	encoding = ""

	if not os.path.isfile(fn):
		fatal("File not found: {}".format(fn))

	if encoding == "":
		try:
			wbuf = open(fn, "r", encoding='ascii').read()
			encoding = "ASCII" # we consider ASCII as a subset of Latin-1 for DP purposes
			inBuf = wbuf.split("\n")
		except Exception as e:
			pass

	if encoding == "":
		try:
			wbuf = open(fn, "rU", encoding='UTF-8').read()
			encoding = "utf_8"
			inBuf = wbuf.split("\n")
			# remove BOM on first line if present
			t = ":".join("{0:x}".format(ord(c)) for c in inBuf[0])
			if t[0:4] == 'feff':
				inBuf[0] = inBuf[0][1:]
		except:
			pass

	if encoding == "":
		try:
			wbuf = open(fn, "r", encoding='latin_1').read()
			encoding = "latin_1"
			inBuf = wbuf.split("\n")
		except Exception as e:
			pass

	if encoding == "":
		fatal("Cannot determine input file decoding")
	else:
		# self.info("input file is: {}".format(encoding))
		if encoding == "ASCII":
			encoding = "latin_1" # handle ASCII as Latin-1 for DP purposes

	return inBuf;


def getFilesModifiedAfterFile( fileName ):
	startTime = os.path.getmtime(fileName)

	basePath = os.path.abspath(fileName)
	basePath = os.path.expanduser(basePath)
	basePath = os.path.expandvars(basePath)
	basePath = os.path.dirname(basePath)

	searchPath = os.path.join(basePath, "*")
	print(searchPath)

	modifiedFiles = []
	for f in glob.glob(searchPath):
		mtime = os.path.getmtime(f)
		if mtime > startTime:
			modifiedFiles.append(f)

	return modifiedFiles


def saveResults( fileList ):
	for f in fileList:
		f = os.path.abspath(f)
		f = os.path.expanduser(f)
		f = os.path.expandvars(f)
		basePath = os.path.dirname(f)

		expectedDirPath = os.path.join(basePath,"expected")
		if not os.path.exists(expectedDirPath):
			os.makedirs(expectedDirPath)

		dstfile = os.path.join(basePath,"expected",os.path.basename(f))
		srcfile = f
		shutil.copy(srcfile,dstfile)


def main():
	testDirectoryPath = "~/pp/tools/repo/diffout/"
	args = docopt(__doc__, version="diffout v{}".format(VERSION))

	# Configure logging
	logLevel = logging.INFO #default
	if args['--verbose']:
		logLevel = logging.DEBUG
	elif args['--quiet']:
		logLevel = logging.ERROR

	logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)
	logging.debug(args)

	#actual = open("out/t1-utf8.txt", encoding="utf-8").readlines()
	#expected = open("out/expected/t1-utf8.txt", encoding="utf-8").readlines()
	htmlout = open("results.html", mode='w', encoding="utf-8")

	#testIndex = buildTestIndex(testDirectoryPath)
	#print(testIndex)

	# Clean up
	# Delete any output files in base directory that match those in expected/

	# Write marker file for time index
	f = open("STARTTIME",'w')
	f.write('.')
	f.close()
	time.sleep(2)

	# Run command on each input file
	for infile in args['<infile>']:
		for f in glob.glob(infile):
			commandline = args['<commandline>']
			commandline = commandline.replace('%F',f)

			logging.info("\n\n----- Running command:\n{}\n".format(commandline))

			cl = shlex.split(commandline)
			logging.debug("args: {}".format(str(cl)))
			proc=subprocess.Popen(cl)
			proc.wait()
			if( proc.returncode != 0 ):
				logging.error("Command failed: {}".format(commandline))

	# HTML Header
	outBuf = []
	outBuf.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
	outBuf.append('<html>')
	outBuf.append('')
	outBuf.append('<head>')
	outBuf.append(' <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />')
	outBuf.append(' <title></title>')
	outBuf.append(' <style type="text/css">')
	outBuf.append('     table.diff {font-family:Courier; border:medium;}')
	outBuf.append('     .diff_header {background-color:#e0e0e0}')
	outBuf.append('     td.diff_header {text-align:right}')
	outBuf.append('     .diff_next {background-color:#c0c0c0}')
	outBuf.append('     .diff_add {background-color:#aaffaa}')
	outBuf.append('     .diff_chg {background-color:#ffff77}')
	outBuf.append('     .diff_sub {background-color:#ffaaaa}')
	outBuf.append(' </style>')
	outBuf.append('</head>')
	outBuf.append('')
	outBuf.append('<body>')

	outFiles = getFilesModifiedAfterFile("STARTTIME")

	logging.info("--- Saving results to expected")
	if args['--save']:
		saveResults(outFiles)

	logging.info("--- Comparing outputs with expected outputs:")
	d = difflib.HtmlDiff(8,80)
	for f in sorted(outFiles):
		# Diffs
		basePath = os.path.dirname(f)
		outFileName = os.path.basename(f)
		expectedFilePath = os.path.join(basePath,"expected",outFileName)

		actual = loadFile(f)

		if os.path.exists(expectedFilePath):
			expected = loadFile(expectedFilePath)

			matchText = "[ DIFF ]"
			if actual==expected:
				matchText = "        "

			logging.info("{} {}".format(matchText,f))

			s = d.make_table(actual, expected, f, expectedFilePath, True)
			outBuf.append(s)
			outBuf.append('<br />')

	# HTML Footer
	outBuf.append('    <table class="diff" summary="Legends">')
	outBuf.append('        <tr> <th colspan="2"> Legends </th> </tr>')
	outBuf.append('        <tr> <td> <table border="" summary="Colors">')
	outBuf.append('                   <tr><th> Colors </th> </tr>')
	outBuf.append('                   <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>')
	outBuf.append('                   <tr><td class="diff_chg">Changed</td> </tr>')
	outBuf.append('                   <tr><td class="diff_sub">Deleted</td> </tr>')
	outBuf.append('               </table></td>')
	outBuf.append('        <td> <table border="" summary="Links">')
	outBuf.append('                   <tr><th colspan="2"> Links </th> </tr>')
	outBuf.append('                   <tr><td>(f)irst change</td> </tr>')
	outBuf.append('                   <tr><td>(n)ext change</td> </tr>')
	outBuf.append('                   <tr><td>(t)op</td> </tr>')
	outBuf.append('               </table>')
	outBuf.append('        </td> </tr>')
	outBuf.append('    </table>')
	outBuf.append('</body>')
	outBuf.append("")
	outBuf.append('</html>')

	htmlout.writelines(["%s\n" % item for item in outBuf])

	# Check for missing/unexpected files
	expectedFiles = glob.glob(os.path.join(os.path.dirname(outFiles[0]),"expected","*"))
	efSet = set()
	for f in expectedFiles:
		efSet.add(os.path.basename(f))

	ofSet = set()
	for f in outFiles:
		ofSet.add(os.path.basename(f))

	extraFiles = ofSet - efSet
	missingFiles = efSet - ofSet

	for f in sorted(extraFiles):
		logging.error("Unexpected output file: {}".format(f))

	for f in sorted(missingFiles):
		logging.error("Missing output file: {}".format(f))


	return


if __name__ == "__main__":
	main()
