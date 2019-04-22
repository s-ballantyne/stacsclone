#!/usr/bin/env python3

import argparse, requests, errno, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode
from clint.textui import progress

parser = argparse.ArgumentParser("Clones practicals from studres")

parser.add_argument("module", type=str, help="Module (e.g. CS1003)")
parser.add_argument("week", type=int, help="Week (e.g. 11)")

parser.add_argument("--url", type=str, default="https://studres.cs.st-andrews.ac.uk", help="Base url to use")
parser.add_argument("-d", "--depth", type=int, default=99, help="Maximum depth of subdirectories")

args = parser.parse_args()

baseurl = args.url
baseurl = urljoin(baseurl, "/{:s}/Practicals/W{:02d}".format(args.module, args.week))

# mkdir -p
def mkdir(path):
	if len(path) == 0:
		return

	try:
		os.makedirs(path)
	except OSError as err:
		if err.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

# Filter out all the crap
def is_crap(name):
	if len(name) < 3:
		return True

	if name == "." or name == "..":
		return True

	if "?" in name:
		return True

	if "=" in name:
		return True

	return False

# Detect if url refers to a file (todo: better way of doing this?)
def is_file(name):
	return name.find(".") != -1

# Download a file
def download_file(url):
	path = url[(len(baseurl) + 1):]
	r = requests.get(url, stream=True)

	mkdir(os.path.dirname(path))

	print(path)
	with open(path, 'wb') as f:
		length = int(r.headers.get("content-length"))
		for chunk in progress.bar(r.iter_content(1024), expected_size=length/1024 + 1):
			if chunk:
				f.write(chunk)


# Iterate over every url and suburl up to a given depth
def recurse(url, depth=99):
	if depth <= 0:
		return 0

	if not url.endswith("/"):
		url += "/"

	nfiles = 0

	r = requests.get(url)
	if r.status_code == 404:
		print("404 not found:", url)
	elif r.status_code != 200:
		print("Request failed:", url)

	soup = BeautifulSoup(r.text, "html.parser")
	for a in soup.find_all("a"):
		href = a.get("href")
		newurl = urljoin(url, href)

		if is_crap(href) or len(newurl) <= len(url):
			continue

		if is_file(href):
			download_file(newurl)
			nfiles += 1
		else:
			nfiles += recurse(newurl, depth - 1)

	return nfiles

print(recurse(baseurl), "file(s) downloaded.")