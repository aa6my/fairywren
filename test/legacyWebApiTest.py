

import json
import hashlib
import urllib
import urllib2
import base64
import unittest
import cookielib 
import tempfile
import random
import subprocess
import os
import multipart
import MultipartPostHandler
import types
import string

def hashPassword(pw):
	h = hashlib.sha512()
	h.update(pw)
	return base64.urlsafe_b64encode(h.digest()).replace('=','')

class WebapiTest(unittest.TestCase):
	def buildFairywrenOpener(self,url,username,password):
		def hashPassword(pw):
			h = hashlib.sha512()
			h.update(pw)
			return base64.urlsafe_b64encode(h.digest()).replace('=','')

		qp=urllib.urlencode({"username":username,"password":hashPassword(password)})
		request = urllib2.Request('%s/api/session' % url,data=qp)
		response = urllib2.urlopen(request)

		body = json.load(response)

		if 'error' in body:
			raise Error(body['error'])

		cookies = cookielib.CookieJar()

		cookies.extract_cookies(response,request)
		self.assertTrue ('session' in ( cookie.name for cookie in cookies))
		
		for c in cookies:
			if c.name == "session":
				self.cookie = "%s=%s" % (c.name,c.value,)
		
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),MultipartPostHandler.MultipartPostHandler)
		self.open = self.opener.open

	def setUp(self):
		with open("test.json",'r') as fin:
			self.conf = json.load(fin)
			
		self.buildFairywrenOpener(  self.conf['url'], self.conf['username'],self.conf['password'] )

class ChangeOwnPassword(WebapiTest):
	
	def setUp(self):
		WebapiTest.setUp(self)
		
		with open('/dev/urandom','r') as randomIn:
			username = randomIn.read(64)
			username = ''.join([c for c in username if c in string.ascii_lowercase])
					
		pwHash = hashlib.sha512()
		password = 'foo'
		pwHash.update(password)
		pwHash = base64.urlsafe_b64encode(pwHash.digest()).replace('=','')
		qp = {'username': username, 'password' : pwHash }
		
		response  = self.open('%s/api/users' % self.conf['url'] , qp)
		body = json.load(response)
		
		self.assertTrue('href' in body)
		
		WebapiTest.buildFairywrenOpener(self,self.conf['url'],username,password)
		
		pwHash = hashlib.sha512()
		with open('/dev/urandom','r') as randomIn:
			password = randomIn.read(64)
			password = ''.join([c for c in password if c in string.ascii_letters])

		pwHash.update(password)
		pwHash = base64.urlsafe_b64encode(pwHash.digest()).replace('=','')
		query = { 'password' : pwHash }
		response = self.open('%s/%s/password' % (self.conf['url'], body['href']),query)		
		
		updatePwBody = json.load(response)
		self.assertTrue('error' not in updatePwBody)
		
		WebapiTest.buildFairywrenOpener(self,self.conf['url'],username,password)
		
	def test_getTorrents(self):
		response = self.open("%s/api/torrents" % self.conf['url'])
		
		body = json.load(response)
		
		self.assertTrue('torrents' in body)
		
		for t in body['torrents']:
			self.assertIn('metainfo' , t)
			self.assertIn('href',t['metainfo'])
			self.assertIn('info' ,t)
			self.assertIn('href',t['info'])
			self.assertIn('title' , t)
			self.assertIn('creationDate' , t)
			self.assertIn('creator' , t)
			self.assertIn('href' , t['creator'])
			self.assertIn('name' , t['creator'])		

class RainyDay(WebapiTest):
	def test_addExistingUser(self):
		with open('/dev/urandom','r') as randomIn:
			username = randomIn.read(64)
		username = ''.join([c for c in username if c in string.ascii_lowercase])
		password = 'password'
			
		pwHash = hashlib.sha512()
		pwHash.update(password)
		pwHash = base64.urlsafe_b64encode(pwHash.digest()).replace('=','')
		qp = {'username': username, 'password' : pwHash }
		
		response  = self.open('%s/api/users' % self.conf['url'] , qp)
		body = json.load(response)
		
		self.assertTrue('href', body)
		
		self.assertRaisesRegexp(urllib2.HTTPError,'.*409.*',self.open,'%s/api/users' % self.conf['url'] , qp)
		
	def test_uploadBadTorrent(self):
		with tempfile.NamedTemporaryFile(delete=True) as randomFile:
			randomFile.write(os.urandom(128))
			randomFile.flush()
			self.assertRaisesRegexp(urllib2.HTTPError,'.*400.*',self.opener.open,str('%s/api/torrents'%self.conf['url']),data={"title":'Random Test Data',"torrent":open(randomFile.name)})
			

		

class SunnyDay(WebapiTest):
		
	def test_addUser(self):
		with open('/dev/urandom','r') as randomIn:
			username = randomIn.read(64)
		username = ''.join([c for c in username if c in string.ascii_lowercase])
		password = 'password'
			
		pwHash = hashlib.sha512()
		pwHash.update(password)
		pwHash = base64.urlsafe_b64encode(pwHash.digest()).replace('=','')
		qp = {'username': username, 'password' : pwHash }
		
		response  = self.open('%s/api/users' % self.conf['url'] , qp)
		body = json.load(response)
		
		self.assertTrue('href' in body)
		
		response = self.open('%s/%s' % ( self.conf['url'], body['href']))
		
		body = json.load(response)
		
		self.assertEqual(body['name'], username)
		self.assertTrue('password' in body)
		self.assertEqual(body['numberOfTorrents'], 0)
		
		
		pwHash = hashlib.sha512()
		pwHash.update('password1')
		pwHash = base64.urlsafe_b64encode(pwHash.digest()).replace('=','')
		query = { 'password' : pwHash }
		response = self.open('%s/%s' % (self.conf['url'], body['password']),query)		
		
		updatePwBody = json.load(response)
		self.assertTrue('error' not in updatePwBody)
	
	def test_getSession(self):
		response = self.open("%s/api/session" % self.conf['url'])
		
		body = json.load(response)
		self.assertIn('my',body)
		self.assertIn('href',body['my'])
		
	
	def test_getTorrents(self):
		response = self.open("%s/api/torrents" % self.conf['url'])
		
		body = json.load(response)
		
		self.assertTrue('torrents' in body)
		
		for t in body['torrents']:
			self.assertIn('metainfo', t)
			self.assertIn('href', t['metainfo'])
			self.assertIn('info' , t)
			self.assertIn('href', t['info'])
			self.assertIn('title' , t)
			self.assertIn('creationDate' , t)
			self.assertIn('creator' , t)
			self.assertIn('href' , t['creator'])
			self.assertIn('name' , t['creator'])
			
	def test_addTorrent(self):
		#create a torrent
		with tempfile.NamedTemporaryFile(delete=True) as fout:
			fout.write(os.urandom(65535))
			
			fout.flush()
			
			torrentFileName= '%s.torrent' % fout.name 
			
			cmd = ['mktorrent','-a','http://127.0.0.1/announce','-o',torrentFileName, fout.name]
			self.assertEqual(0,subprocess.Popen(cmd).wait())
		
		try:
			with open(torrentFileName,'r') as fin:
				response = multipart.post_multipart('127.0.0.1','/nihitorrent/api/torrents', self.cookie, [('title','Test Torrent')],[('torrent','test.torrent',fin.read())])
				response = json.loads(response)
				torrentUrl = response['metainfo']['href']
		except Exception:
			raise
		finally:
			os.remove(torrentFileName)
		
		response = self.open('%s/%s' % ( self.conf['url'] , torrentUrl,))
		
		
			
if __name__ == '__main__':
    unittest.main()
