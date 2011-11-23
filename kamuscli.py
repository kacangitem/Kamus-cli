#!/usr/bin/env python
# 	Copyleft 2010 Imam Omar Mochtar <kerupuk[at]kacangitem.web.id>
# 
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the
#     Free Software Foundation, Inc.,
#         59 Temple Place, Suite 330,
#           Boston, MA  02111-1307  USA

import sqlite3
import sys
import os
import optparse
import urllib
import simplejson
import re
from xml.etree import ElementTree as ET


#########################################################
### SET PATH DATABASE KAMUS DAN OPENTEACHER FILE DISINI
#########################################################
db = '/home/kacang/Desktop/kamuscli/kacangitem.db'
otpath = '/home/kacang/Desktop/kamuscli/latihankosakata.ot'
##########################################################

class kamus:
	def __init__(self):
		"Inisialisasi hal-hal yang dibutuhkan"
		self.version = "1.0"
		self.osd = sys.platform
		self.checkDB(db)
		self.dbkon = sqlite3.connect(db)
		self.cursor = self.dbkon.cursor()
		self.gtrans = False
		self.interact = False
		self.word = None
		self.otwrite = False
		self.parsingARG()
		if self.interact:
			self.interactive()
		else:
			self.fetchREST(self.word)
			self.dbkon.close()

	def checkGT(self,word):
		got = False
		for lang in ['en|id','id|en']:
			site = 'http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&langpair=%s&q=%s' % (lang,word)
			try:
				getme = simplejson.load(urllib.urlopen(site))
			except:
				self.dbkon.close()
				print "TERJADI MASALAH PADA KONEKSI !!!!"	
				sys.exit(0)
			else:
				if getme['responseData']['translatedText'] != word: 
					if lang == "en|id":
						table = lang
						mean = getme['responseData']['translatedText']
						print ("[*]en-id>>%s"  if self.osd == 'win32' \
						 else "\033[1;31m[*]en->id>>\033[1;32m%s\033[0m") % mean
						got = True
					elif lang == "id|en":
						table = lang
						mean = getme['responseData']['translatedText']
						print ("[*]en-id>>%s"  if self.osd == 'win32' \
						 else "\033[1;31m[*]en->id>>\033[1;32m%s\033[0m") % mean
						got = True
					break
		if got:
			return  "insert into kacang%s(%s) values('%s','%s')" % (re.sub(r'\|','',table),table.replace('|',','),word,mean)
		else:
			return None 
		
	
	def checkOT(self):
		"Method untukCek OpenTeacher file, jika tidak ada maka akan langsung dibuatkan"
		if not os.path.isfile(otpath):
			head = ET.Element('root')
			bawah1 = ET.SubElement(head,'title')
			bawah2 = ET.SubElement(head,'question_language')
			bawah3 = ET.SubElement(head,'answer_language')
			bawah1.text = 'English Words Translation Exercise'
			bawah2.text = 'English'
			bawah3.text = 'Indonesia'
			try:
				with open(otpath,'w') as tulis:
					tulis.write(ET.tostring(head))
			except:
				print "Ups.. tidak bisa menulis file %s" % otpath
					
	def saveOT(self,word,mean):
		self.checkOT()
		with open(otpath,'rt') as f:
			tree = ET.parse(f)
		top  = ET.Element('word')
		asing = ET.SubElement(top,'known')
		arti = ET.SubElement(top,'foreign')
		nilai = ET.SubElement(top,'results')
		asing.text = word
		arti.text = mean
		nilai.text = '0/0'
		save = tree.find('.')
		save.append(top)
		tree.write(otpath)
			
	
	def parsingARG(self):		   
		pars = optparse.OptionParser(usage="%prog -w|--word [kata] -i|--interaktif")
		pars.add_option('-i','--interaktif',action="store_true",\
		default=False,dest="interact",help="Masuk Mode Kamus Interaktif")

		pars.add_option('-w','--word',action="store",default=None,\
		dest="word",help="Set Kata yang ingin diterjemahkan",metavar="kata")

		pars.add_option('-o','--openteacher',action="store_true",\
		default=False,dest="openteacher",help="Simpan hasil terjemahan ke dalam OpenTeacher file")


		pars.add_option('-g','--gtrans',action="store_true",\
		default=False,dest="gtranslate",help="Jika kata tidak ditemukan maka akan langsung dicari ke google translate")	
	
		pars.add_option('-v','--version',dest="version",\
		action="store_true",default=False,help="Cetak versi")

		if len(sys.argv) == 1:
			pars.print_help()
			sys.exit(0)
		option , remain = pars.parse_args(sys.argv[1:])
		if option.version:
			print "Versi %s : %s" % (sys.argv[0],self.version)
			print "Dibuat oleh kerupuk[at]kacangitem.web.id"
			sys.exit(1)

		if option.gtranslate:
			self.gtrans = True
		if option.openteacher:
			self.otwrite = True
		if option.word:
			self.word = option.word
		if option.interact and option.word:
			print "Dilarang untuk memasukan kata pada argumen bersamaan dengan mode intereaktif !!!"
			sys.exit(0)
		if option.interact:
			self.interact = True
			
	def checkDB(self,path):
		"Cek database yang berisikan terjemahan kata b.ing dan b.indo"
		if not os.path.isfile(path):
			print "Database kamus %s tidak ditemukan !!!" % path
			sys.exit(0)
	
	def translateME(self,word):
		enid = self.cursor.execute("select id from kacangenid where en='%s'" % word).fetchone()
		iden = self.cursor.execute("select en from kacangiden where id='%s'" % word).fetchone()
		return {'en2id':enid,'id2en':iden}
		
	def writeOT(self,word):
		ote = raw_input("OT>>" if self.osd == 'win32' else "\033[1;33mOT>>\033[0m")
		if ote:
			self.saveOT(word,ote)
		
	def fetchREST(self,word):
		result = self.translateME(word)
		if result['en2id']:
			print ("[*]en-id>>%s"  if self.osd == 'win32'  else "\033[1;31m[*]en->id>>\033[1;32m%s\033[0m") % result['en2id']	
		if result['id2en']:
			print ("[*]id-en>>%s"  if self.osd == 'win32' else "\033[1;31m[*]id-en>>\033[1;32m%s\033[0m") % result['id2en']
		if result['en2id'] or result['id2en']:
			if self.otwrite:
				self.writeOT(word)
		if not result['en2id'] and not result['id2en']:
			print ("\"%s\" tidak ditemukan" if self.osd == 'win32' else "\033[1;31m\"%s\" tidak ditemukan\033[0m" ) % word
			if self.gtrans:
				print ("Mencari di Google Translate" if self.osd == 'win32' else "\033[1;31mMencari di Google Translate\033[0m" ) 
				gainME = self.checkGT(word)
				if gainME:
					self.cursor.execute(gainME)
					self.dbkon.commit()
					if self.otwrite:
						self.writeOT(word)
				else:
					print ("\"%s\" tidak ditemukan pada google translate" if self.osd == 'win32' else "\033[1;31m\"%s\" tidak ditemukan pada google translate\033[0m" ) % word
							
	
	def interactive(self):
		while True:
			print "\nTinggalkan kosong untuk keluar .."
			try:
				searchME = raw_input("kamus>" if self.osd == 'win32' else "\033[1;34mkamus>\033[0m")
			except KeyboardInterrupt:
				print "KeyBoardInterrput terdeteksi..."
				print "Menutup koneksi database"
				self.dbkon.close()
				sys.exit(0)
			if not searchME:
				break
			self.fetchREST(searchME)
		self.dbkon.close()
		
if __name__ == '__main__':
	begin = kamus()
