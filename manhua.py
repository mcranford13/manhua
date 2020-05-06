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
from pathlib import Path
import os, sys, shutil, re, time, zipfile

'''
	TODO:

	1. Fix metadata to actually extract and write properly
	2. Create a function for adding a cover to the epub
	3. 

'''

def CreateEpub(files, name, htmlContent):
	print("Creating epub file...")
	epub = zipfile.ZipFile(name + ".epub", "w")

	epub.writestr("mimetype", "application/epub+zip")

	epub.writestr("META-INF/container.xml", '''<container version="1.0"
	xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/Content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')

	md = ExtractMetadata(htmlContent)
	metadata = ""
	manifest = ""
	spine = ""

	for meta in md:

		if("Author" in meta):
			metadata += f'<dc:creator id="cre">{md[meta]}</dc:creator><meta refines="#cre" property="role" scheme="marc:relators">aut</meta>>'
		else:
			metadata += f'<{meta}>{md[meta]}</{meta}>'

	toc_manifest = '<item href="toc.xhtml" id="toc" properties="nav" media-type="application/xhtml+xml"/>'

	for i, html in enumerate(files):
		basename = os.path.basename(html)
		manifest += f'<item id="file_{i + 1}" href="{basename}" media-type="application/xhtml+xml"/>'  
		spine += f'<itemref idref="file_{i + 1}" />'
		epub.write(html, "OEBPS/" + basename)


	index_tpl = f'''<package version="3.1"
xmlns="http://www.idpf.org/2007/opf">
  <metadata>
    {metadata}
      </metadata>
        <manifest>
         {manifest + toc_manifest}
        </manifest>
        <spine>
          <itemref idref="toc" linear="no"/>
          {spine}
        </spine>
</package>'''


	epub.writestr("OEBPS/Content.opf", index_tpl)
def ExtractTitle(htmlContent):

	print('Extracting Title...')

	title = htmlContent.find('div', {'class':'post-title'}).find('h3')
			
	if('HOT' in title.text or 'NEW' in title.text):
		title = title.contents[2].strip()
	else:
		title = title.text.strip()

	return title


def ExtractMetadata(htmlContent):

	md = {}
	print("Extracting metadata...")
	metadata = htmlContent.findAll('div', {'class':'post-content_item'})
	#m = open('metadata.xml', 'w', encoding="utf-8")
	#m.write('<?xml version="1.0" encoding="UTF-8"?>\n<metadata>\n')
			
	for meta in metadata:
		heading = meta.find('div', {'class':'summary-heading'}).get_text().strip()
		data = meta.find('div', {'class':'summary-content'}).get_text().strip()
				
		if("(s)" in heading):
			heading = heading.replace('(s)', "")

		md[heading] = data
		#m.write(f"<{heading}>{data}</{heading}>\n")	

	#m.write('</metadata>')
	#m.close()

	return md
				

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
	chapters = htmlContent.find('div', {'class':'c-page__content'}).findAll('a', href=True)

	return chapters
	

def DownloadChapter(chapter):

	chapTitle = chapter.text.strip()
	print(f"Downloading {chapTitle}")

	notAllowed = ['?', '/', '\\', ':', '*', '\"', '<', '>', '|']		#this only for windows & mac operating systems but *shrug*

	for those in notAllowed:
		if(those in chapTitle):
			chapTitle = chapTitle.replace(those, "")


	f = open(chapTitle + ".html", 'w', encoding='utf-8')
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

def DownloadChapters(chapters, resume, delay):

	if(delay > 0):
		print(f"Estimated time: {(len(chapters) * delay) / 60} minutes")
	else:
		print(f"Estimated time: {(len(chapters)) / 60} minutes")

	if(resume):
		lastFile = FindLastChapter(os.getcwd())
	
		for chapter in chapters:
			time.sleep(delay)
			if(chapter.text.strip() + ".html" == lastFile):
				break
			DownloadChapter(chapter)
	else:
		for chapter in chapters:
			time.sleep(delay)
			DownloadChapter(chapter)

	
def FindLastChapter(directory):

	print("Finding last chapter...")
	files = os.listdir(directory)
	files.sort(reverse = True, key=Match)

	if(".epub" in files[2]):
		os.remove(files[2])
		print(f"Last Chapter found is: {files[3]}")
		return files[3]
	else:
		print(f"Last Chapter found is: {files[2]}")
		return files[2]			#This is accounting for the cover art and metadate file


def atoi(text):
	return int(text) if text.isdigit() else text

def Match(chapter):

	return [atoi(c) for c in re.split(r'(\d+)', chapter)]
	

def main(args):
	
	url = input("URL: ")
	delay = int(input("Delay: "))
	resume = False


	saveLoc = 	directory = Path(str(Path.home())) / 'Documents' / 'Ebooks'
	directory = Path(str(Path.home())) / 'Documents' / 'WebNovels'
			
	if(directory.exists()):
		os.chdir(directory)
	else:
		os.mkdir(directory)
		os.chdir(directory)

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
			
			
			#ExtractMetadata(content)

			ExtractCoverArt(content)
							
			chapters = ExtractChapters(content)

			DownloadChapters(chapters, resume, delay)

			files = os.listdir(os.getcwd())
			files.sort(key=Match)


			CreateEpub(files, title, content)

			print(f"Moving to {saveLoc}")

			if(os.path.exists(f"{str(saveLoc)}\\{title}.epub")):
				os.remove(f"{str(saveLoc)}\\{title}.epub")

			os.rename(f"{title}.epub", f"{str(saveLoc)}\\{title}.epub")
			
		else:
			print("Error: incorrect URL")
			exit(-1)
		
	except Exception as e:
		print(e)
		exit(-1)
		
	print("All Finished, Enjoy!")
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
