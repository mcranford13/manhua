#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  manhua.py
#  
#  Copyright 2019 Matthew <matthew@Hohenheim>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


import requests as rs
from bs4 import BeautifulSoup as bs
import os, sys, shutil, threading, re

'''
	TODO:

	1. Threading
	2. Resume from last chapter
	3. GUI?
	4. Delay

'''


def ExtractTitle(htmlContent):

	print('Extracting Title...')

	title = htmlContent.find('div', {'class':'post-title'}).find('h3')
			
	if('HOT' in title.text or 'NEW' in title.text):
		title = title.contents[2].strip()
	else:
		title = title.text.strip()

	return title


def ExtractMetadata(htmlContent):

	print("Extracting metadata...")
	metadata = htmlContent.findAll('div', {'class':'post-content_item'})
	m = open('metadata.xml', 'w')
	m.write('<?xml version="1.0" encoding="UTF-8"?>\n<metadata>\n')
			
	for meta in metadata:
		heading = meta.find('div', {'class':'summary-heading'}).get_text().strip()
		data = meta.find('div', {'class':'summary-content'}).get_text().strip()
				
		if("(s)" in heading):
			heading = heading.replace('(s)', "")

		m.write(f"<{heading}>{data}</{heading}>\n")	

	m.write('</metadata>')
	m.close()
				

def ExtractCoverArt(htmlContent):
	print("Extracting cover art...")
			
	picUrl = htmlContent.find('div', {'class':'summary_image'}).find('img')
						
	try:
		pic = rs.get(picUrl['src'], stream=True)
				
		if(pic.status_code == 200):
			p = open('cover.jpg', 'wb')
			pic.raw.decode_content = True
			shutil.copyfileobj(pic.raw, p)
					
			p.close()
				
	except Exception as e:
		print("Error trying to extract image...")
		print(e +"\n")
		

def ExtractChapters(htmlContent):

	print('Extracting urls...')
	return htmlContent.find('div', {'class':'c-page__content'}).findAll('a', href=True)
	

def DownloadChapter(chapter):

	print(f"Downloading {chapter.text.strip()}...")

	f = open(chapter.text.strip() + ".html", 'w', encoding='utf-8')
		#f.write(f'<html>\n<h1>{chapter.text.strip()}</h1>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n')
	try:
		response = rs.get(chapter['href'])
					
		if(response.status_code == 200):
						
			content = bs(response.content, 'lxml')
						
			paragraphs = content.find('div', {'class':'text-left'})
						
			for paragraph in paragraphs:
							
				f.write(str(paragraph))
												
	except Exception as e:
		print("Error downloading chapter...")
		print(e +"\n")
					
	f.write("</html>")
	f.close()

def DownloadChapters(chapters, resume):

	if(resume):
		lastFile = FindLastChapter(os.getcwd())

		for chapter in chapters:
			if(chapter.text.strip() + ".html" == lastFile):
				break
			DownloadChapter(chapter)
	else:
		for chapter in chapters:
			DownloadChapter(chapter)

		
		


def FindLastChapter(directory):

	print("Finding last chapter...")
	files = os.listdir(directory)
	files.sort(reverse = True, key=Match)

	print(files[2])
	return files[2]			#This is accounting for the cover art and metadate file


def atoi(text):
	return int(text) if text.isdigit() else text

def Match(chapter):

	return [atoi(c) for c in re.split(r'(\d+)', chapter)]
	

def main(args):
	
	url = input("URL: ")
	resume = False
	
	try:
		response = rs.get(url)
		
		if(response.status_code == 200):
			
			content = bs(response.content, 'lxml')
			
			title = ExtractTitle(content)
			
				
			if(os.path.exists(title)):
				print("Folder already exists... no problem!")
				os.chdir(title)
				resume = True
			else:
				os.mkdir(title)
				os.chdir(title)
			
			
			ExtractMetadata(content)

			ExtractCoverArt(content)
							
			chapters = ExtractChapters(content)

			DownloadChapters(chapters, resume)
			
		else:
			print("Error: incorrect URL")
			exit(-1)
		
	except Exception as e:
		print(e)
		exit(-1)
		
	print("Done!")
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
