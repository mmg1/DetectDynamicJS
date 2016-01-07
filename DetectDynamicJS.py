# -*- coding: utf-8 -*-
# Burp DetectDynamicJS Extension
# Copyright (c) 2015, Veit Hailperin (scip AG)

# This extension is supposed to help detecting dynamic js files, to look for state-dependency.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from burp import IBurpExtender
from burp import IScannerCheck
from burp import IExtensionStateListener
from burp import IExtensionHelpers
from burp import IHttpRequestResponse
from burp import IScanIssue
from array import array
import difflib

<<<<<<< HEAD
VERSION = '0.3'
VERSIONNAME = 'Mia Wallace'
=======
VERSION = '0.2'
VERSIONNAME = 'Vincent Vega'
>>>>>>> fc388f65a0283a21f34b5d707faf514b76d29eeb


class BurpExtender(IBurpExtender, IScannerCheck, IExtensionStateListener, IHttpRequestResponse):

    def	registerExtenderCallbacks(self, callbacks):

        print "Loading..."

        self._callbacks = callbacks
        self._callbacks.setExtensionName('Detect Dynamic JS')
        
        self._callbacks.registerScannerCheck(self)
        self._callbacks.registerExtensionStateListener(self)
        self._helpers = callbacks.getHelpers()

        # store all js files
        self.js_files = {} # url:contents
        
        print "Loaded Detect Dynamic JS v"+VERSION+" ("+VERSIONNAME+")!"
        return


    def extensionUnloaded(self):
        print "Unloaded"
        return
    # Burp Scanner invokes this method for each base request/response that is
    # passively scanned
    def doPassiveScan(self, baseRequestResponse):
        # WARNING: NOT REALLY A PASSIVE SCAN!
        # doPassiveScan issues always one request per request scanned
        self._requestResponse = baseRequestResponse

        scan_issues = []
        issue = self.addToCollection(self._requestResponse)
        if issue:
            scan_issues.append(issue)

        request = self._requestResponse.getRequest()
        requestInfo = self._helpers.analyzeRequest(request)
        bodyOffset = requestInfo.getBodyOffset()
        headers = request.tostring()[:bodyOffset].split('\r\n')
        body = request.tostring()[bodyOffset:]
        modified_headers = "\n".join(header for header in headers if "Cookie" not in header)
        newResponse = self._callbacks.makeHttpRequest(self._requestResponse.getHttpService(), self._helpers.stringToBytes(modified_headers+body))
        respInfo = self._helpers.analyzeRequest(newResponse)
        issue = self.addToCollection(newResponse)
        if issue:
            scan_issues.append(issue)

        # doPassiveScan needs to return a list of scan issues, if any, and None
        # otherwise
        if len(scan_issues) > 0:
            return scan_issues
        else:
            return None

    def addToCollection(self, baseRequestResponse):
        self._helpers = self._callbacks.getHelpers()
        url = self._helpers.analyzeRequest(baseRequestResponse).getUrl()
        url = str(url).split("?")[0]
        response = baseRequestResponse.getResponse()
        responseInfo = self._helpers.analyzeResponse(response)
        bodyOffset = responseInfo.getBodyOffset()
        headers = response.tostring()[:bodyOffset].split('\r\n')
        contentLengthL = [x for x in headers if "content-length:" in x.lower()]
        if len(contentLengthL) >= 1:
            contentLength = int(contentLengthL[0].split(':')[1].strip())
        else:
            contentLength = 0
        result = None
        if contentLength > 0:
            contentType = ""
            contentTypeL = [x for x in headers if "content-type:" in x.lower()]
            if len(contentTypeL) == 1:
                contentType = contentTypeL[0].lower()
            statusCode = headers[0].split()[1].strip()
            if url not in self.js_files:
                if (url[-3:] == ".js" or "javascript" in contentType or "ecmascript" in contentType or "jscript" in contentType or "application/json" in contentType) and (url[-5:] != ".json") and (int(statusCode) < 300 or int(statusCode) > 399):
                    self.js_files[url] = baseRequestResponse
            else:
                result = self.compareResponses(baseRequestResponse, self.js_files[url])
        return result

            
    def compareResponses(self, newResponse, oldResponse):
        """Compare two responses in respect to their body contents"""
        nResponse = newResponse.getResponse()
        nResponseInfo = self._helpers.analyzeResponse(nResponse)
        nBodyOffset = nResponseInfo.getBodyOffset()
        nBody = nResponse.tostring()[nBodyOffset:]

        oResponse = oldResponse.getResponse()
        oResponseInfo = self._helpers.analyzeResponse(oResponse)
        oBodyOffset = oResponseInfo.getBodyOffset()
        oBody = oResponse.tostring()[oBodyOffset:]            
        result = None
        if str(nBody) != str(oBody):
            issuename = "Dynamic JavaScript Code Detected"
            issuelevel = "Information"
            issuedetail = "These two files contain differing contents. Check the contents of the files to ensure that they don't contain sensitive information."
            issuebackground = "Dynamically generated JavaScript might contain session or user relevant information. Contrary to regular content that is protected by Same-Origin Policy, scripts can be included by third parties. This can lead to leakage of user/session relevant information."
            issueremediation = "Applications should not store user/session relevant data in JavaScript files with known URLs. If strict separation of data and code is not possible, CSRF tokens should be used."
<<<<<<< HEAD
           
=======
>>>>>>> fc388f65a0283a21f34b5d707faf514b76d29eeb
            oOffsets = self.calculateHighlights(nBody, oBody, oBodyOffset)
            nOffsets = self.calculateHighlights(oBody, nBody, nBodyOffset)
            result = ScanIssue(self._requestResponse.getHttpService(),
                               self._helpers.analyzeRequest(self._requestResponse).getUrl(),
                               issuename, issuelevel, issuedetail, issuebackground, issueremediation,
                               [self._callbacks.applyMarkers(oldResponse, None, oOffsets), self._callbacks.applyMarkers(newResponse, None, nOffsets)])
        else:
            url = self._helpers.analyzeRequest(newResponse).getUrl()
            url = str(url)
            print "File "+url+" is the same with and without cookies"
            
        return result


    def calculateHighlights(self, newBody, oldBody, bodyOffset):
        """find the exact points for highlighting the responses"""
        s = difflib.SequenceMatcher(None, oldBody, newBody)
        matching_blocks = s.get_matching_blocks()
        offsets = []
        poszero = 0
        posone = 0
        first = True
        # can create slightly weird marks because of being as
        # exact as one character. But I'd rather keep precision
        for m in matching_blocks:
            offset = array('i', [0, 0])
            if first:
                poszero = m.a + m.size + bodyOffset
                first = False
            else:
                posone = m.a + bodyOffset
                if posone != poszero:
                    offset[0] = poszero
                    offset[1] = posone
                    offsets.append(offset)
                poszero = m.a + m.size + bodyOffset
        return offsets


    def consolidateDuplicateIssues(self, existingIssue, newIssue):
        existingIssueResponses = []
        newIssueResponses = []
        sameMessages = 0
        for newResponse in newIssue.getHttpMessages():
            nResponse = newResponse.getResponse()
            nResponseInfo = self._helpers.analyzeResponse(nResponse)
            nBodyOffset = nResponseInfo.getBodyOffset()
            nBody = nResponse.tostring()[nBodyOffset:]
            newIssueResponses.append(nBody)
            
        for oldResponse in existingIssue.getHttpMessages():
            oResponse = oldResponse.getResponse()
            oResponseInfo = self._helpers.analyzeResponse(oResponse)
            oBodyOffset = oResponseInfo.getBodyOffset()
            oBody = oResponse.tostring()[oBodyOffset:]
            existingIssueResponses.append(oBody)

        for newIssueResp in newIssueResponses:
            for existingIssueResp in existingIssueResponses:
                if newIssueResp == existingIssueResp:
                    sameMessages += 1
                    break
        if sameMessages == 2:
            return -1
        else:
            return 0

        
class ScanIssue(IScanIssue):
    def __init__(self, httpservice, url, name, severity, detailmsg, background, remediation, requests):
        self._url = url
        self._httpservice = httpservice
        self._name = name
        self._severity = severity
        self._detailmsg = detailmsg
        self._issuebackground = background
        self._issueremediation = remediation
        self._httpmsgs = requests
        
    def getUrl(self):
        return self._url

    def getHttpMessages(self):
        return self._httpmsgs

    def getHttpService(self):
        return self._httpservice

    def getRemediationDetail(self):
        return None

    def getIssueDetail(self):
        return self._detailmsg

    def getIssueBackground(self):
        return self._issuebackground

    def getRemediationBackground(self):
        return self._issueremediation

    def getIssueType(self):
        return 0

    def getIssueName(self):
        return self._name

    def getSeverity(self):
        return self._severity

    def getConfidence(self):
        return "Certain"
