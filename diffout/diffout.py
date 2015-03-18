#!/usr/bin/env python3

"""diffout

Usage:
  diffout [options] [--] <commandline> <infile>...
  diffout -s | --save
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

HTML_PATH       = os.path.join("diffout","diffs")
EXPECTED_PATH   = os.path.join("diffout","expected")
OUTPUT_PATH     = os.path.join("diffout","output")


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
			encoding = "ASCII"
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

	return inBuf;


def expandPath( path ):
	path = os.path.abspath(path)
	path = os.path.expanduser(path)
	path = os.path.expandvars(path)
	path = os.path.normpath(path)

	return path


def getFilesModifiedAfterFile( path ):

	path = expandPath(path)
	startTime = os.path.getmtime(path)

	lp, rp = os.path.split(path)
	searchPath = os.path.join(lp, "*")

	modifiedFiles = []
	for f in glob.glob(searchPath):
		mtime = os.path.getmtime(f)
		if mtime > startTime:
			modifiedFiles.append(f)

	return modifiedFiles


def getDirectoryFileList( path ):
	path = expandPath(path)
	lp, rp = os.path.split(path)
	if not os.path.isdir(rp):
		logging.error("{} is not a directory".format(path))
		return []

	searchPath = os.path.join(lp,rp,"*")
	return glob.glob(searchPath)


def saveFiles( fileList, destDir ):
	destDir = expandPath(destDir)
	for f in fileList:
		f = expandPath(f)
		lp, rp = os.path.split(f)

		if not os.path.exists(destDir):
			os.makedirs(destDir)

		dstFile = os.path.join(destDir,rp)
		srcFile = f
		shutil.copy(srcFile,dstFile)


def diffDir( newDir, oldDir ):
	logging.info("--- Comparing new outputs with expected outputs:")

	if not os.path.exists(HTML_PATH):
		os.makedirs(HTML_PATH)

	# Index HTML Header
	indexHtml = []
	indexHtml.extend(htmlHeader)
	indexHtml.append("<table class='results'>")

	# Check for missing/unexpected files
	newDir = expandPath(newDir)
	oldDir = expandPath(oldDir)
	newFiles = getDirectoryFileList(newDir)
	oldFiles = getDirectoryFileList(oldDir)
	ofSet = set()
	for f in oldFiles:
		ofSet.add(os.path.basename(f))

	nfSet = set()
	for f in newFiles:
		nfSet.add(os.path.basename(f))

	extraFiles = nfSet - ofSet
	missingFiles = ofSet - nfSet

	#for f in sorted(extraFiles):
		#logging.info("Unexpected output file was generated: {}".format(f))

	for f in sorted(missingFiles):
		matchText = colorama.Style.BRIGHT + colorama.Back.CYAN + "[ MISSING]" + colorama.Back.RESET + colorama.Style.RESET_ALL
		print("{} Expected output file not generated: {}".format(matchText,f))

	fileChangeCount = 0
	d = difflib.HtmlDiff(8,80)
	for f in sorted(newFiles):
		# HTML Header
		outBuf = []
		outBuf.extend(htmlHeader)

		# Diffs
		fn = os.path.basename(f)
		expectedFilePath = os.path.join(oldDir,fn)

		actual = loadFile(f)
		isDiff = False
		if os.path.exists(expectedFilePath):
			expected = loadFile(expectedFilePath)

			matchText = colorama.Style.BRIGHT + colorama.Back.LIGHTRED_EX + "[ DIFF   ]" + colorama.Back.RESET + colorama.Style.RESET_ALL
			if actual==expected:
				matchText = colorama.Back.LIGHTGREEN_EX + "[ NODIFF ]" + colorama.Style.RESET_ALL
			else:
				isDiff = True
				fileChangeCount += 1

			print("{} {}".format(matchText,f))

			s = d.make_table(expected, actual, expectedFilePath, f, True)
			outBuf.append(s)
			outBuf.append('<br />')
		else:
			matchText = colorama.Style.BRIGHT + colorama.Back.BLUE + "[ EXTRA  ]" + colorama.Back.RESET + colorama.Style.RESET_ALL
			print("{} Unexpected output file was generated: {}".format(matchText,os.path.basename(f)))

		# HTML Footer
		outBuf.extend(htmlFooter)

		# Write out results
		p = os.path.join(HTML_PATH,"{}.html".format(fn))
		htmlout = open(p, mode='w', encoding="utf-8")
		htmlout.writelines(["%s\n" % item for item in outBuf])
		htmlout.close()

		# Add to index
		if isDiff:
			indexHtml.append("<tr><td style='text-align:center;background:red;color:white;font: bold 1em sans-serif, serif;'>DIFF</td><td><a href='{1}/{0}.html'>{0}</a></td></tr>".format(fn,os.path.basename(HTML_PATH)))
		else:
			indexHtml.append("<tr><td style='text-align:center;background:green;color:white;font: bold 1em sans-serif, serif;'>NODIFF</td><td><a href='{1}/{0}.html'>{0}</a></td></tr>".format(fn,os.path.basename(HTML_PATH)))

	# Index HTML Footer
	indexHtml.append("</table>")
	indexHtml.append("</body>")
	indexHtml.append("</html>")

	# Write out index.html
	parentDir = os.path.dirname(HTML_PATH)
	p = os.path.join(parentDir,"index.html")
	htmlout = open(p, mode='w', encoding="utf-8")
	htmlout.writelines(["%s\n" % item for item in indexHtml])
	htmlout.close()

	# Finished, summarize results
	print()
	if len(extraFiles) > 0:
		print("{} unexpected output files were generated.".format(len(extraFiles)))
	if len(missingFiles) > 0:
		print("{} expected output files were not generated.".format(len(missingFiles)))
	if fileChangeCount > 0:
		print("{} output file(s) differ with expected output, view results.html for diff results".format(fileChangeCount))
	else:
		print("No differences with expected output found.")
	print()

	return


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

	if args['--save']:
		p = expandPath(EXPECTED_PATH)
		if os.path.exists(p):
			logging.info("--- Clearing current expected results")
			print(p)
			shutil.rmtree(p)

		logging.info("--- Saving latest results to expected")
		saveFiles(getDirectoryFileList(OUTPUT_PATH),EXPECTED_PATH)
		return

	# Delete output files from previous run
	p = expandPath(OUTPUT_PATH)
	if os.path.exists(p):
		logging.info("--- Clearing results from last run")
		print(p)
		shutil.rmtree(p)

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

	# Copy recently modified files into output/
	outFiles = getFilesModifiedAfterFile("STARTTIME")
	saveFiles(outFiles,OUTPUT_PATH)

	print("\nFinished executing {} command(s) ({} error(s) occured).".format(commandCount,commandErrorCount))
	print("{} output file(s) were generated ({} expected).".format(len(getDirectoryFileList(OUTPUT_PATH)),len(getDirectoryFileList(EXPECTED_PATH))))
	print()

	diffDir(OUTPUT_PATH,EXPECTED_PATH)

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
			  '		table.results {margin:3em auto; width:auto;background:#eee;border-spacing:0.3em;border:thin solid #ccc}',
			  '		.results td {text-align: left; padding: 0.3em 0.6em; border: none;}',
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
