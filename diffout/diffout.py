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
import colorama


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


def splitPath( path ):
	path = os.path.abspath(path)
	path = os.path.expanduser(path)
	path = os.path.expandvars(path)
	path = os.path.normpath(path)

	return os.path.split(path)


def getFilesModifiedAfterFile( fileName ):
	startTime = os.path.getmtime(fileName)

	p, _ = splitPath(fileName)
	searchPath = os.path.join(p, "*")

	modifiedFiles = []
	for f in glob.glob(searchPath):
		mtime = os.path.getmtime(f)
		if mtime > startTime:
			modifiedFiles.append(f)

	return modifiedFiles


def saveResults( fileList ):
	for f in fileList:
		path, fname = splitPath(f)

		expectedDirPath = os.path.join(path,"expected")
		if not os.path.exists(expectedDirPath):
			os.makedirs(expectedDirPath)

		dstfile = os.path.join(path,"expected",fname)
		srcfile = f
		shutil.copy(srcfile,dstfile)


def main():
	testDirectoryPath = "~/pp/tools/repo/diffout/"
	args = docopt(__doc__, version="diffout v{}".format(VERSION))

	colorama.init()

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

	import sys
	sys.setrecursionlimit(1500)
	# Clean up
	# Delete any output files in base directory that match those in expected/

	# Write marker file for time index
	f = open("STARTTIME",'w')
	f.write('.')
	f.close()
	time.sleep(1)

	# Run command on each input file
	commandCount = 0
	commandErrorCount = 0
	for infile in args['<infile>']:
		for f in glob.glob(infile):
			commandline = args['<commandline>']
			commandline = commandline.replace('%F',f)

			matchText = colorama.Fore.LIGHTRED_EX + "[ DIFF ]" + colorama.Fore.RESET
			s = colorama.Fore.LIGHTYELLOW_EX + "\n----- Running command:\n{}\n".format(commandline) + colorama.Fore.RESET
			print(s)
			commandCount += 1

			cl = shlex.split(commandline)
			logging.debug("args: {}".format(str(cl)))
			proc=subprocess.Popen(cl)
			proc.wait()
			if( proc.returncode != 0 ):
				logging.error("Command failed: {}".format(commandline))
				commandErrorCount += 1

	# HTML Header
	outBuf = []
	outBuf.extend(htmlHeader)

	outFiles = getFilesModifiedAfterFile("STARTTIME")
	print(outFiles)

	if args['--save']:
		logging.info("--- Saving results to expected")
		saveResults(outFiles)

	# Check for missing/unexpected files
	expectedFiles = glob.glob(os.path.join("expected","*"))
	efSet = set()
	for f in expectedFiles:
		efSet.add(os.path.basename(f))

	ofSet = set()
	for f in outFiles:
		ofSet.add(os.path.basename(f))

	extraFiles = ofSet - efSet
	missingFiles = efSet - ofSet

	for f in sorted(extraFiles):
		logging.info("Unexpected output file was generated: {}".format(f))

	for f in sorted(missingFiles):
		logging.info("Expected output file not generated: {}".format(f))

	logging.info("--- Comparing outputs with expected outputs:")
	fileChangeCount = 0
	d = difflib.HtmlDiff(8,80)
	for f in sorted(outFiles):
		# Diffs
		basePath = os.path.dirname(f)
		outFileName = os.path.basename(f)
		expectedFilePath = os.path.join(basePath,"expected",outFileName)

		actual = loadFile(f)

		if os.path.exists(expectedFilePath):
			expected = loadFile(expectedFilePath)

			matchText = colorama.Style.BRIGHT + colorama.Back.LIGHTRED_EX + "[  DIFF  ]" + colorama.Back.RESET + colorama.Style.RESET_ALL
			if actual==expected:
				matchText = colorama.Back.LIGHTGREEN_EX + "[ NODIFF ]" + colorama.Style.RESET_ALL
			else:
				fileChangeCount += 1

			logging.info("{} {}".format(matchText,f))

			s = d.make_table(expected, actual, expectedFilePath, f, True)
			outBuf.append(s)
			outBuf.append('<br />')

	# HTML Footer
	outBuf.extend(htmlFooter)

	htmlout.writelines(["%s\n" % item for item in outBuf])

	print("\nFinished executing {} commands ({} error(s) occured).".format(commandCount,commandErrorCount))
	print("{} output files were generated ({} expected).".format(len(outFiles),len(expectedFiles)))

	if len(extraFiles) > 0:
		print("{} unexpected output files were generated.".format(len(extraFiles)))

	if len(missingFiles) > 0:
		print("{} expected output files were not generated.".format(len(missingFiles)))

	if fileChangeCount > 0:
		print("{} output files differ with expected output, view results.html for diff results".format(fileChangeCount))
	else:
		print("No differences with expected output found.")

	print()

	return


htmlHeader = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
			  '<html>',
			  '',
			  '<head>',
			  ' <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />',
			  ' <title>diffout results</title>',
			  ' <style type="text/css">',
			  '     table.diff {font-family:Courier; border:medium;}',
			  '     .diff_header {background-color:#e0e0e0}',
			  '     td.diff_header {text-align:right}',
			  '     .diff_next {background-color:#c0c0c0}',
			  '     .diff_add {background-color:#aaffaa}',
			  '     .diff_chg {background-color:#ffff77}',
			  '     .diff_sub {background-color:#ffaaaa}',
			  ' </style>',
			  '</head>',
			  '',
			  '<body>')

htmlFooter = ('    <table class="diff" summary="Legends">',
             '        <tr> <th colspan="2"> Legends </th> </tr>',
             '        <tr> <td> <table border="" summary="Colors">',
             '                   <tr><th> Colors </th> </tr>',
             '                   <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>',
             '                   <tr><td class="diff_chg">Changed</td> </tr>',
             '                   <tr><td class="diff_sub">Deleted</td> </tr>',
             '               </table></td>',
             '        <td> <table border="" summary="Links">',
             '                   <tr><th colspan="2"> Links </th> </tr>',
             '                   <tr><td>(f)irst change</td> </tr>',
             '                   <tr><td>(n)ext change</td> </tr>',
             '                   <tr><td>(t)op</td> </tr>',
             '               </table>',
             '        </td> </tr>',
             '    </table>',
             '</body>',
             '',
             '</html>')



if __name__ == "__main__":
	main()
