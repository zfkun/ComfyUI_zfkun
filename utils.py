import binascii
import codecs
import hashlib
import hmac
import http.client
import json
import urllib
import os
import re
import sys
import shutil
import time
import traceback
import uuid

import __main__
# import folder_paths

from datetime import datetime
from functools import reduce


VERSION = "0.0.4"
ADDON_NAME = "zfkun"

HOME_PATH = os.path.dirname(os.path.realpath(__file__))

COMFY_PATH = os.path.dirname(__main__.__file__)
COMFY_WEB_PATH = os.path.join(COMFY_PATH, "web")
COMFY_WEB_EXTENSIONS_PATH = os.path.join(COMFY_WEB_PATH, "extensions")

_CONFIG_FILE = os.path.join(HOME_PATH, "config.yaml")

_config: dict = { "translator": {} }
_piplist: set[str] = None


def printColor(text, color='\033[92m'):
    CLEAR = '\033[0m'
    print(f"[ComfyUI_zfkun] {color}{text}{CLEAR}")

def printColorWarn(text):
    printColor(text, '\033[93m')

def printColorError(text):
    printColor(text, '\033[91m')

############ Check Start ############

printColor(f"check start", "\033[1;35m")

try:
    import subprocess

    def get_installed_packages():
        global _piplist

        if _piplist is None:
            try:
                result = subprocess.check_output([sys.executable, '-m', 'pip', 'list'], universal_newlines=True)
                _piplist = set([line.split()[0].lower() for line in result.split('\n') if line.strip()])
            except subprocess.CalledProcessError as e:
                printColorError(f"failed to get installed packages from pip")

        return _piplist


    def is_installed(name):
        name = name.strip()

        match = re.search(r'([^<>!=]+)([<>!=]=?)', name)
        if match:
            name = match.group(1)

        return (name in get_installed_packages(), name)


    def is_requirements_installed(file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for p in f.readlines():
                    if not is_installed(p):
                        return False
                        
        return True


    def install():
        req_file = os.path.join(HOME_PATH, "requirements.txt")

        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                for line in f.readlines():
                    ok, dependency = is_installed(line)
                    if not ok:
                        printColorWarn(f'"{dependency}" is not installed. Trying to install.')
                        try:
                            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dependency])
                            printColor(f'"{dependency}" is installed')
                        except subprocess.CalledProcessError as e:
                            printColorError(f'"{dependency}" install fail: {e}')
                
                printColor('all dependency installed')

    install()

except Exception as e:
    printColorError("Dependency install failed. Please install manually.", )
    traceback.print_exc()

printColor(f"check end", "\033[1;35m")


############ Check End ############


############ Setup Start ############

import chardet
import yaml


def convert_to_utf8(file_path: str):
    raw = open(file_path, 'rb').read()
    res = chardet.detect(raw)
    encoding = res['encoding']

    if encoding != 'utf-8':
        with codecs.open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
        with codecs.open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

        return encoding

    return None


def load_config():
    global _config

    if not os.path.exists(_CONFIG_FILE):
        return
    
    origin_encoding = convert_to_utf8(_CONFIG_FILE)
    if origin_encoding:
        printColorWarn(f'convert "config.yaml" encoding: from {origin_encoding} to utf-8')

    c = yaml.load(open(_CONFIG_FILE, "r"), Loader=yaml.FullLoader)

    # 翻译配置
    if c and c['translator'] and isinstance(c['translator'], dict):
        for p in c['translator']:
            printColor(f"translator found: {p}")
            _config['translator'][p] = c['translator'][p]

############ Setup End ############


############ Nodes Start ############

from PIL import Image
import numpy as np
import torch

def checkDir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def addFilesToDir(fromDir, toDir):
    for f in os.listdir(fromDir):
        from_file = os.path.join(fromDir, f)
        to_file = os.path.join(toDir, f)

        if os.path.exists(to_file):
            os.remove(to_file)

        printColor(f"node install: {f}")
        shutil.copy(from_file, to_file)

# Tensor to PIL
def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
    
# PIL to Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

# PIL Hex
def pil2hex(image):
    return hashlib.sha256(np.array(tensor2pil(image)).astype(np.uint16).tobytes()).hexdigest()

# PIL to Mask
def pil2mask(image):
    image_np = np.array(image.convert("L")).astype(np.float32) / 255.0
    mask = torch.from_numpy(image_np)
    return 1.0 - mask

# Mask to PIL
def mask2pil(mask):
    if mask.ndim > 2:
        mask = mask.squeeze(0)
    mask_np = mask.cpu().numpy().astype('uint8')
    mask_pil = Image.fromarray(mask_np, mode="L")
    return mask_pil


############ Nodes Start ############


############ Translation Start ############

# 翻译平台
TRANSLATOR_PLATFORMS = ["baidu", "alibaba", "tencent", "volcengine", "niutrans"]

# 语种代号表
LANGUAGE_CODES = ["zh-cn", "zh-tw", "en", "ja", "ko", "fr", "es", "it", "de", "tr", "ru", "pt", "vi", "id", "th", "ms", "ar", "hi"]

# 正向转义修正 (`LANGUAGE_CODES` => 平台语种代号)
_FIXED_LANGUAGE_CODES = {
    "baidu": {
        "zh-cn": "zh",
        "zh-tw": "cht",
        "ja": "jp",
        "ko": "kor",
        "fr": "fra",
        "es": "spa",
        "vi": "vie",
        "ar": "ara",
        "ms": "may",
    },
    "tencent": {
        "zh-tw": "zh-TW",
    },
    "volcengine": {
        "zh-tw": "zh-Hant",
    },
    "niutrans": {
        "zh-cn": "zh",
        "zh-tw": "cht",
    },
}

# 反向转义修正 (平台语种代号 => `LANGUAGE_CODES`)
__INVERT_FIXED_LANGUAGE_CODES = {
    "baidu": {
        "zh": "zh-cn",
        "cht": "zh-tw",
        "jp": "ja",
        "kor": "ko",
        "fra": "fr",
        "spa": "es",
        "vie": "vi",
        "ara": "ar",
        "may": "ms",
    },
    "tencent": {
        "zh-TW": "zh-tw",
    },
    "volcengine": {
        "zh-Hant": "zh-tw",
    },
    "niutrans": {
        "zh": "zh-cn",
        "cht": "zh-tw",
    },
}


def fix_language_code(platform: str, code: str, invert: bool = False):
    if invert:
        if platform in __INVERT_FIXED_LANGUAGE_CODES and code in __INVERT_FIXED_LANGUAGE_CODES[platform]:
            return __INVERT_FIXED_LANGUAGE_CODES[platform][code]
    else:
        if platform in _FIXED_LANGUAGE_CODES and code in _FIXED_LANGUAGE_CODES[platform]:
            return _FIXED_LANGUAGE_CODES[platform][code]

    return code


def get_translator_config(platform: str):
    if platform not in _config['translator']:
        return None
    return _config['translator'][platform]


def to_hex(content):
    lst = []
    for ch in content:
        if sys.version_info[0] == 3:
            hv = hex(ch).replace('0x', '')
        else:
            hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0' + hv
        lst.append(hv)
    return reduce(lambda x, y: x + y, lst)


def sha256(content):
    # type(content) == <class 'str'>
    if sys.version_info[0] == 3:
        if isinstance(content, str) is True:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        else:
            return hashlib.sha256(content).hexdigest()
    else:
        if isinstance(content, (str, unicode)) is True:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        else:
            return hashlib.sha256(content).hexdigest()


def hmac_sha256(key, content):
    # type(key) == <class 'bytes'>
    if sys.version_info[0] == 3:
        return hmac.new(key, bytes(content, encoding='utf-8'), hashlib.sha256).digest()
    else:
        return hmac.new(key, bytes(content.encode('utf-8')), hashlib.sha256).digest()



def text_translate(platform:str, text:str, source="auto", target="en"):
    if platform == 'baidu':
        return _text_translate_baidu(text, source, target)
    if platform == 'alibaba':
        return _text_translate_alibaba_v3(text, source, target)
    if platform == 'tencent':
        return _text_translate_tencent_v3(text, source, target)
    if platform == 'volcengine':
        return _text_translate_volcengine_v4(text, source, target)
    if platform == 'niutrans':
        return _text_translate_niutrans(text, source, target)

    printColor(f'translate platform unsupport: {platform}')
    return (text, source, target,)


# 百度翻译 (https://fanyi-api.baidu.com/product/113)
def _text_translate_baidu(text:str, source="auto", target="en"):
        c = get_translator_config("baidu")
        if not c:
            return (text, source, target,)
        
        result = text
        fromCode = fix_language_code('baidu', source)
        toCode = fix_language_code('baidu', target)

        salt = binascii.hexlify(os.urandom(16)).decode()
        sign = hashlib.md5(f"{c['key']}{text}{salt}{c['secret']}".encode('utf-8')).hexdigest()
        path = f"/api/trans/vip/translate?appid={c['key']}&q={urllib.parse.quote(text)}&from={fromCode}&to={toCode}&salt={salt}&sign={sign}"

        printColor(f'baidu translate start: {fromCode} => {toCode}')

        hc = http.client.HTTPConnection('api.fanyi.baidu.com')
        # hc.set_debuglevel(2)
        try:
            hc.request('GET', path)

            res = hc.getresponse()
            body = res.read().decode("utf-8")

            printColor(f'baidu translate response: {body}')

            r = json.loads(body)
            if not r or not r['trans_result'] or not r['trans_result'][0] or not r['trans_result'][0]['dst']:
                printColor(f'translate fail: {body}')
            else:
                result = str(r['trans_result'][0]['dst'])
                if r['from']:
                    fromCode = fix_language_code('baidu', str(r['from']), True)
                if r['to']:
                    toCode = fix_language_code('baidu', str(r['to']), True)
        except Exception as e:
            hc.close()
            printColor(f'baidu translate exception: {e}')

        printColor(f'baidu translate end: {fromCode} => {toCode}')
        return (result, fromCode, toCode,)


# 阿里翻译 (https://help.aliyun.com/zh/sdk/product-overview/v3-request-structure-and-signature)
def _text_translate_alibaba_v3(text: str, source="auto", target="en", region="cn-beijing"):
    c = get_translator_config("alibaba")
    if not c:
        return (text, source, target,)

    secret_id = c['key'] or ""
    secret_key = c['secret'] or ""
    region = c['region'] or region

    result = text
    from_code = fix_language_code('alibaba', source)
    to_code = fix_language_code('alibaba', target)

    host = f"mt.{region}.aliyuncs.com"
    action = "TranslateGeneral"
    version = "2018-10-12"
    algorithm = "ACS3-HMAC-SHA256"
    request_date = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    nonce = str(uuid.uuid4())

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = 'POST'
    canonical_uri = "/api/translate/web/general"
    canonical_querystring = ''
    content_type = "application/x-www-form-urlencoded"
    payload = urllib.parse.urlencode({
        "FormatType": "text",
        "SourceLanguage": from_code,
        "TargetLanguage": to_code,
        "SourceText": text,
        "Scene": "general"
    })
    hashed_request_payload = sha256(payload)

    signed_headers = 'host;x-acs-action;x-acs-content-sha256;x-acs-date;x-acs-signature-nonce;x-acs-version'
    canonical_request = (
        f"{http_request_method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"

        f"host:{host}\n"
        f"x-acs-action:{action}\n"
        f"x-acs-content-sha256:{hashed_request_payload}\n"
        f"x-acs-date:{request_date}\n"
        f"x-acs-signature-nonce:{nonce}\n"
        f"x-acs-version:{version}\n"
        "\n"

        f'{signed_headers}\n'
        f'{hashed_request_payload}'
    )

    # ************* 步骤 2：拼接待签名字符串 *************
    hashed_canonical_request = sha256(canonical_request)
    string_to_sign = (
        f"{algorithm}\n"
        f"{hashed_canonical_request}"
    )

    # ************* 步骤 3：计算签名 *************
    sign = to_hex(hmac_sha256(secret_key.encode('utf-8'), string_to_sign))

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (f"{algorithm} "
                     f"Credential={secret_id},"
                     f"SignedHeaders={signed_headers},"
                     f"Signature={sign}")

    headers = {
        "Authorization": authorization,
        "Host": host,
        "Accept": "application/json",
        "Content-Type": content_type,
        "x-acs-action": action,
        "x-acs-content-sha256": hashed_request_payload,
        "x-acs-date": request_date,
        "x-acs-signature-nonce": nonce,
        "x-acs-version": version,
    }

    printColor(f'alibaba translate start: {from_code} => {to_code}')

    hc = http.client.HTTPConnection(host)
    # hc.set_debuglevel(2)
    try:
        hc.request('POST', canonical_uri, payload.encode('utf-8'), headers)

        res = hc.getresponse()
        body = res.read().decode("utf-8")

        printColor(f'alibaba translate response: {body}')

        r = json.loads(body)
        if not r or not r['Data'] or not r['Data']['Translated']:
            printColor(f'translate fail: {body}')
        else:
            result = str(r['Data']['Translated'])
            if r['Data']['DetectedLanguage']:
                from_code = fix_language_code('alibaba', str(r['Data']['DetectedLanguage']), True)
    except Exception as e:
        printColor(f'alibaba translate exception: {e}')
    finally:
        hc.close()

    printColor(f'alibaba translate end: {from_code} => {to_code}')
    return result, from_code, to_code


# 腾讯翻译 (https://cloud.tencent.com/document/api/551/15619)
# v3: https://cloud.tencent.com/document/api/551/30636
def _text_translate_tencent_v3(text: str, source="auto", target="en", region="ap-beijing"):
    c = get_translator_config("tencent")
    if not c:
        return (text, source, target,)

    secret_id = c['key'] or ""
    secret_key = c['secret'] or ""
    region = c['region'] or region

    result = text
    from_code = fix_language_code('tencent', source)
    to_code = fix_language_code('tencent', target)

    service = "tmt"
    host = "tmt.tencentcloudapi.com"
    action = "TextTranslate"
    version = "2018-03-21"
    algorithm = "TC3-HMAC-SHA256"
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = 'POST'
    canonical_uri = "/"
    canonical_querystring = ''
    content_type = "application/json"
    payload = json.dumps({
        "SourceText": text,
        "Source": from_code,
        "Target": to_code,
        "ProjectId": c['project'] or 0,
    })
    hashed_request_payload = sha256(payload)

    canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (content_type, host, action.lower())
    signed_headers = 'content-type;host;x-tc-action'.lower()
    canonical_request = (f"{http_request_method}\n"
                         f"{canonical_uri}\n"
                         f"{canonical_querystring}\n"
                         f"{canonical_headers}\n"
                         f'{signed_headers}\n'
                         f'{hashed_request_payload}')

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = sha256(canonical_request)
    string_to_sign = (
        f"{algorithm}\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )

    # ************* 步骤 3：计算签名 *************
    secret_date = hmac_sha256(("TC3" + secret_key).encode('utf-8'), date)
    secret_service = hmac_sha256(secret_date, service)
    secret_signing = hmac_sha256(secret_service, "tc3_request")
    sign = to_hex(hmac_sha256(secret_signing, string_to_sign))

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + sign)
    headers = {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": version,
        "X-TC-Region": region,
    }

    printColor(f'tencent translate start: {from_code} => {to_code}')

    hc = http.client.HTTPSConnection(host)
    hc.set_debuglevel(2)
    try:
        hc.request('POST', canonical_uri, payload.encode('utf-8'), headers)

        res = hc.getresponse()
        body = res.read().decode("utf-8")

        printColor(f'tencent translate response: {body}')

        r = json.loads(body)
        if not r or not r['Response'] or not r['Response']['TargetText']:
            printColor(f'translate fail: {body}')
        else:
            result = str(r['Response']['TargetText'])
            if r['Response']['Source']:
                from_code = fix_language_code('tencent', str(r['Response']['Source']), True)
            if r['Response']['Target']:
                to_code = fix_language_code('tencent', str(r['Response']['Target']), True)
    except Exception as e:
        printColor(f'tencent translate exception: {e}')
    finally:
        hc.close()

    printColor(f'tencent translate end: {from_code} => {to_code}')
    return result, from_code, to_code


# 火山翻译 (https://www.volcengine.com/docs/4640/65067)
def _text_translate_volcengine_v4(text: str, source="auto", target="en", region="cn-beijing"):
    c = get_translator_config("volcengine")
    if not c:
        return (text, source, target,)

    secret_id = c['key'] or ""
    secret_key = c['secret'] or ""
    region = c['region'] or region

    result = text
    from_code = fix_language_code('volcengine', source)
    to_code = fix_language_code('volcengine', target)

    service = "translate"
    host = "translate.volcengineapi.com"
    action = "TranslateText"
    version = "2020-06-01"
    algorithm = "HMAC-SHA256"
    timestamp = int(time.time())
    request_date = datetime.utcfromtimestamp(timestamp).strftime("%Y%m%dT%H%M%SZ")

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = 'POST'
    canonical_uri = "/"
    canonical_querystring = f'Action={action}&Version={version}'
    content_type = "application/json"
    payload = {"TargetLanguage": to_code, "TextList": [text]}
    payload.update({"SourceLanguage": from_code} if from_code and from_code != "auto" else {})
    jsoned_payload = json.dumps(payload)
    hashed_request_payload = sha256(jsoned_payload)

    canonical_headers = "content-type:%s\nhost:%s\nx-content-sha256:%s\nx-date:%s\n" % (content_type, host, hashed_request_payload, request_date)
    signed_headers = 'content-type;host;x-content-sha256;x-date'.lower()
    canonical_request = (f"{http_request_method}\n"
                         f"{canonical_uri}\n"
                         f"{canonical_querystring}\n"
                         f"{canonical_headers}\n"
                         f'{signed_headers}\n'
                         f'{hashed_request_payload}')

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = request_date[:8] + "/" + region + "/" + service + "/" + "request"
    hashed_canonical_request = sha256(canonical_request)
    string_to_sign = (
        f"{algorithm}\n"
        f"{request_date}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )

    # ************* 步骤 3：计算签名 *************
    date_for_sign = datetime.utcfromtimestamp(timestamp).strftime("%Y%m%d")
    secret_date = hmac_sha256(secret_key.encode('utf-8'), date_for_sign)
    secret_region = hmac_sha256(secret_date, region)
    secret_service = hmac_sha256(secret_region, service)
    secret_signing = hmac_sha256(secret_service, "request")
    sign = to_hex(hmac_sha256(secret_signing, string_to_sign))

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + sign)
    headers = {
        "Authorization": authorization,
        "Content-Type": content_type,
        'User-Agent': 'volc-sdk-python/v1.0.118',
        "Host": host,
        "X-Content-Sha256": hashed_request_payload,
        "X-Date": request_date,
    }

    printColor(f'volcengine translate start: {from_code} => {to_code}')

    hc = http.client.HTTPConnection(host)
    # hc.set_debuglevel(2)
    try:
        hc.request(http_request_method, canonical_uri + f'?{canonical_querystring}', jsoned_payload.encode('utf-8'), headers)

        res = hc.getresponse()
        body = res.read().decode("utf-8")

        printColor(f'volcengine translate response: {body}')

        r = json.loads(body)
        if not r or not r['TranslationList'] or not r['TranslationList'][0] or not r['TranslationList'][0]['Translation']:
            printColor(f'translate fail: {body}')
        else:
            result = str(r['TranslationList'][0]['Translation'])
            if r['TranslationList'][0]['DetectedSourceLanguage']:
                from_code = fix_language_code('volcengine', str(r['TranslationList'][0]['DetectedSourceLanguage']), True)
    except Exception as e:
        printColor(f'volcengine translate exception: {e}')
    finally:
        hc.close()

    printColor(f'volcengine translate end: {from_code} => {to_code}')
    return result, from_code, to_code


# 小牛翻译 (https://niutrans.com/documents/contents/trans_text)
def _text_translate_niutrans(text: str, source="auto", target="en"):
    c = get_translator_config("niutrans")
    if not c:
        return (text, source, target,)

    secret_key = c['secret'] or ""

    result = text
    from_code = fix_language_code('niutrans', source)
    to_code = fix_language_code('niutrans', target)

    host = "api.niutrans.com"
    
    http_request_method = 'POST'
    canonical_uri = "/NiuTransServer/translation"
    content_type = "application/json"
    payload = {"from": from_code, "to": to_code, "apikey": secret_key, "src_text": text}
    jsoned_payload = json.dumps(payload)

    headers = {
        "Content-Type": content_type,
        "Host": host,
    }

    printColor(f'niutrans translate start: {from_code} => {to_code}')

    hc = http.client.HTTPConnection(host)
    # hc.set_debuglevel(2)
    try:
        hc.request(http_request_method, canonical_uri, jsoned_payload.encode('utf-8'), headers)

        res = hc.getresponse()
        body = res.read().decode("utf-8")

        printColor(f'niutrans translate response: {body}')

        r = json.loads(body)
        if not r or not r['tgt_text']:
            printColor(f'translate fail: {body}')
        else:
            result = str(r['tgt_text'])
            if r['from']:
                from_code = fix_language_code('niutrans', str(r['from']), True)
            if r['to']:
                to_code = fix_language_code('niutrans', str(r['to']), True)
    except Exception as e:
        printColor(f'niutrans translate exception: {e}')
    finally:
        hc.close()

    printColor(f'niutrans translate end: {from_code} => {to_code}')
    return result, from_code, to_code


############ Translation End ############
