import json
import logging
import re
import requests
import time
import json
from typing import Optional, List
from dataclasses import dataclass, field

from datetime import datetime
from requests.exceptions import TooManyRedirects

from dataclasses_json import dataclass_json, config
from vdataclass import Firmware

from bs4 import BeautifulSoup

MANIFEST_URL= "https://www.2n.com/en_GB/c/portal/render_portlet"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "x-requested-with": "XMLHttpRequest"

}

PAYLOAD ={
    "p_l_id": 618795,
    "p_p_id": "101_INSTANCE_ONpHHwoLjEag",
    "p_p_lifecycle": 0,
    "p_t_lifecycle": 0,
    "p_p_state": "normal",
    "p_p_mode": "view",
    "p_p_col_id": "column-1",
    "p_p_col_pos": 1,
    "p_p_col_count": 2,
    "p_p_isolated": 1,
    "currentURL": "/en_GB/web/2n/support/documents/firmware",
    "_101_INSTANCE_ONpHHwoLjEag_2n-search-document": "2N® Indoor Touch 2.0,2N® Indoor View,2N® Indoor Compact,2N® Indoor Talk,2N® IP Handset,2N® Indoor Touch,2N® Mobile Video,2N® SIP Speaker,2N® SIP Speaker Horn,2N® SIP Audio Converter,2N® SIP Mic,2N® IP Audio Manager,2N® Net Speaker,2N® Net Audio Decoder,2N® Net Audio Decoder Lite,2N® Net Mic,2N® Net Audio Encoder,2N® Remote Configuration,2N® Partner API,2N® IP Style,2N® IP Verso,2N® LTE Verso,2N® IP Solo,2N® IP Force,2N® IP Safety,2N® IP Vario,2N® IP Base,2N® IP Uni,2N® IP Audio Kit,2N® IP Video Kit,2N® Analog Force,2N® Analog Safety,2N® Analog Vario,2N® Analog Uni,2N® Induction Loop,2N® 2Wire,NVT PoLRE LPC Switch,2N® SmartCom PRO,2N® SmartCom Server,2N® LiftGate,2N® Elevator Center,2N® Lift8,2N® Lift1,2N® LiftIP,2N® EasyGate IP,GSM/UMTS Gateway for Lifts,Induction Loop for Lifts,2N Floor Annunciator,2N® 2Wire for Lifts,2N® Lift8 Camera module,2N® Call Center,2N Access Unit 2.0,2N Access Unit M,2N® Access Commander,2N® EasyGate PRO,2N® VoiceBlue Next,2N® NetStar,2N® Contact Centre Solution,2N® NetStar SW,2N® SmartGate,2N® SmartGate UMTS,2N® BRI Enterprise,2N® VoiceBlue MAX,2N® BlueTower,2N® OfficeRoute,2N® SIM Star – SIM Server,",
    "portletAjaxable": 1,
    "_101_INSTANCE_ONpHHwoLjEag_2n-custom-params": "2n-search-document"
}

@dataclass_json
@dataclass
class VendorMetadata:
    product_family: str
    model: str
    os: str
    landing_urls: Optional[List[str]] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    firmware_urls: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    bootloader_url: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    release_notes_url: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    md5_url: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )
    data: Optional[str] = field(
        default=None, metadata=config(exclude=lambda x: x is None)
    )

def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def main():
    # Printing the List[Firmware] of the function output_firmware.
    manifest = get_manifest(MANIFEST_URL)
    output_firmware(manifest)

def output_firmware(manifest_url: str) -> List[Firmware]:
    vendor_firmwares = []

    firmwareInfoData = []
    for m in manifest_url:
        if m.data != None:
            firmwareInfoData.append(m.data)
    
    for data in firmwareInfoData:
        modelNVersion = data.find('div', {'class': 'p2n-info-block-heading'}).text.strip()
        firmwareInfo = data.find('div', {'class': 'p2n-bottom-info'}).text.strip()
        url = 'https://www.2n.com' + data.find('a').get('href')
        
        #Here we get the Version
        dotPosition = find_nth(modelNVersion, '.', 1)
        dashSeparator = find_nth(modelNVersion, '-', 1)
        versionData = modelNVersion[dotPosition - 1: dashSeparator].strip()
        if '(' in versionData:
            parenthesisPos = find_nth(versionData, '(', 1)
            version = versionData[0:parenthesisPos].strip()
        else:
            version = versionData

        #Here we get the model
        nposition = find_nth(modelNVersion, '2N', 1)
        model = modelNVersion[nposition:]

        #Here we get the file name
        lastDash = url.rfind('/')
        filename = url[lastDash + 1:]

        #Checking for additional data
        try:
            mbPosition = find_nth(firmwareInfo, 'MB', 1)
            thirdPipe = find_nth(firmwareInfo, '|', 2)
            sizeMB = firmwareInfo[thirdPipe + 1: mbPosition].strip()
            bytes = str(int(sizeMB) * 1048576)
        except:
            kbPosition = find_nth(firmwareInfo, 'kB', 1)
            thirdPipe = find_nth(firmwareInfo, '|', 2)
            sizeKB = firmwareInfo[thirdPipe + 1: kbPosition].strip()
            bytes = str(int(sizeKB) * 1024)

        #Get the realese notes
        try:
            lastDot = find_nth(firmwareInfo, '.', 2)
            realesData = firmwareInfo[lastDot:]
            realeseNotes = realesData[3:].strip()
        except:
            realeseNotes = None
        
        tn = Firmware(
            version = version,
            models = [model],
            filename = filename,
            url = url, 
            size_bytes = bytes,
            release_notes = realeseNotes,
        )
        vendor_firmwares.append(tn)

    print(len(vendor_firmwares))
    return vendor_firmwares

def get_manifest(manifest_url: str) -> List[VendorMetadata]:

    twon_models = []

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    p = requests.post(
    manifest_url, data= PAYLOAD, headers=HEADERS
    )
    html = BeautifulSoup(p.content, "html.parser")
    
    containers = html.find_all('div', {'class': 'p2n-container'})

    for container in containers:
        title = container.find('div', {'class': 'p2n-info-block-heading'}).text.strip()
        # info = container.find('div', {'class': 'p2n-bottom-info'}).text.strip()
        # url = container.find('a').get('href')

        if 'Firmware' in title:
            positionOfN = find_nth(title, '2N', 1)
            model = title[positionOfN:]
            tn = VendorMetadata(
                product_family = None,
                model = model,
                os =  None,
                data = container,
            )
            twon_models.append(tn)
            
    return twon_models

if __name__ == "__main__":
    main()