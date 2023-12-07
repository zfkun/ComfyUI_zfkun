from datetime import datetime

import binascii
import hashlib
import hmac
import http.client
import json
import urllib
import os
import shutil
import time
import uuid
import yaml

import __main__
# import folder_paths

VERSION = "0.0.1"
ADDON_NAME = "zfkun"

HOME_PATH = os.path.dirname(os.path.realpath(__file__))

COMFY_PATH = os.path.dirname(__main__.__file__)
COMFY_WEB_PATH = os.path.join(COMFY_PATH, "web")
COMFY_WEB_EXTENSIONS_PATH = os.path.join(COMFY_WEB_PATH, "extensions")

_CONFIG_FILE = os.path.join(HOME_PATH, "config.yaml")

_config: dict = { "translator": {} }


def load_config():
    global _config

    if not os.path.exists(_CONFIG_FILE):
        return

    c = yaml.load(open(_CONFIG_FILE, "r"), Loader=yaml.FullLoader)

    # 翻译配置
    if c['translator'] and isinstance(c['translator'], dict):
        for p in c['translator']:
            printColor(f"[ComfyUI_zfkun] translator found: {p}")
            _config['translator'][p] = c['translator'][p]
    
    printColor(f"[ComfyUI_zfkun] translator : {_config['translator']}")


############ Nodes Start ############

# os.environ['AUX_USE_SYMLINKS'] = str(USE_SYMLINKS)
# os.environ['AUX_ANNOTATOR_CKPTS_PATH'] = annotator_ckpts_path
# os.environ['AUX_ORT_PROVIDERS'] = str(",".join(ORT_PROVIDERS))

def printColor(text, color='\033[92m'):
    CLEAR = '\033[0m'
    print(f"[ComfyUI_zfkun] {color}{text}{CLEAR}")

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

############ Nodes Start ############


############ Translation Start ############

# 翻译平台
TRANSLATOR_PLATFORMS = ["baidu", "alibaba", "tencent", "volcengine"]

# 语种代号表
LANGUAGE_CODES = ["zh-cn", "zh-tw", "en", "ja", "ko", "fr", "es", "it", "de", "tr", "ru", "pt", "vi", "id", "th", "ms", "ar", "hi"]

# 正向转义修正 (`LANGUAGE_CODES` => 平台语种代号)
_FIXED_LANGUAGE_CODES = {
    "baidu": {
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
}

# 反向转义修正 (平台语种代号 => `LANGUAGE_CODES`)
__INVERT_FIXED_LANGUAGE_CODES = {
    "baidu": {
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
}


def fix_language_code(platform: str, code: str, invert: bool = False):
    if invert:
        if platform in __INVERT_FIXED_LANGUAGE_CODES and code in __INVERT_FIXED_LANGUAGE_CODES[platform]:
            return __INVERT_FIXED_LANGUAGE_CODES[platform][code]
    else:
        if platform in _FIXED_LANGUAGE_CODES and code in _FIXED_LANGUAGE_CODES[platform]:
            return _FIXED_LANGUAGE_CODES[platform][code]

    return code


# def get_gmt_time(timestamp: float = None):
#     if not timestamp:
#         timestamp = time.time()
#     return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp))


def get_utc_time(timestamp: float = None):
    if not timestamp:
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')


# def md5_base64(s: str):
#     m = hashlib.md5(s.encode('utf-8')).digest()
#     return base64.b64encode(m).decode('utf-8')


def sha256_base64(s: str):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


# def create_hmac_sha1_signature(key, message):
#     key = key.encode('utf-8')
#     message = message.encode('utf-8')

#     digester = hmac.new(key, message, hashlib.sha1)
#     signature = digester.hexdigest()

#     return signature


def create_hmac_sha256_signature(key: str, message: str):
    return hmac.new(key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()


def create_hmac_sha256_signature_str(key: bytes, message: str):
    return hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()


def get_translator_config(platform: str):
    if platform not in _config['translator']:
        return None
    return _config['translator'][platform]


def text_translate(platform:str, text:str, source="auto", target="en"):
    if platform == 'baidu':
        return _text_translate_baidu(text, source, target)
    if platform == 'alibaba':
        return _text_translate_alibaba_v3(text, source, target)
    if platform == 'tencent':
        return _text_translate_tencent_v3(text, source, target)

    printColor(f'translate platform unsupport: {platform}')
    return (text, source, target,)

# 百度翻译
def _text_translate_baidu(text:str, source="auto", target="en"):
        c = get_translator_config("baidu")
        if not c:
            return (text, source, target,)
        
        result = text
        fromCode = fix_language_code('baidu', source)
        toCode = fix_language_code('baidu', target)
        salt = binascii.hexlify(os.urandom(16)).decode()

        sign = hashlib.md5(f"{c['key']}{text}{salt}{c['secret']}".encode()).hexdigest()
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

    # secret_id = c['key'] or ""
    secret_key = c['secret'] or ""
    region = c['region'] or region

    result = text
    from_code = fix_language_code('alibaba', source)
    to_code = fix_language_code('alibaba', target)

    host = f"mt.{region}.aliyuncs.com"
    action = "TranslateGeneral"
    version = "2018-10-12"
    algorithm = "ACS3-HMAC-SHA256"
    date = get_utc_time()
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
    hashed_request_payload = sha256_base64(payload)

    signed_headers = 'host;x-acs-action;x-acs-content-sha256;x-acs-date;x-acs-signature-nonce;x-acs-version'
    canonical_request = (
        f"{http_request_method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"

        f"host:{host}\n"
        "x-acs-action:TranslateGeneral\n"
        f"x-acs-content-sha256:{hashed_request_payload}\n"
        f"x-acs-date:{date}\n"
        f"x-acs-signature-nonce:{nonce}\n"
        f"x-acs-version:{version}\n"
        "\n"

        f'{signed_headers}\n'
        f'{hashed_request_payload}'
    )

    # ************* 步骤 2：拼接待签名字符串 *************
    hashed_canonical_request = sha256_base64(canonical_request)
    string_to_sign = (
        f"{algorithm}\n"
        f"{hashed_canonical_request}"
    )

    # ************* 步骤 3：计算签名 *************
    sign = create_hmac_sha256_signature(c['secret'], string_to_sign)

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (f"{algorithm} "
                     f"Credential={secret_key},"
                     f"SignedHeaders={signed_headers},"
                     f"Signature={sign}")

    headers = {
        "Authorization": authorization,
        "Host": host,
        "Accept": "application/json",
        "Content-Type": content_type,
        "x-acs-action": action,
        "x-acs-content-sha256": hashed_request_payload,
        "x-acs-date": date,
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
    hashed_request_payload = sha256_base64(payload)

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
    hashed_canonical_request = sha256_base64(canonical_request)
    string_to_sign = (
        f"{algorithm}\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )

    # ************* 步骤 3：计算签名 *************
    secret_date = create_hmac_sha256_signature_str(("TC3" + secret_key).encode('utf-8'), date)
    secret_service = create_hmac_sha256_signature_str(secret_date, service)
    secret_signing = create_hmac_sha256_signature_str(secret_service, "tc3_request")
    sign = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

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

    # printColor(f'canonical_request: {canonical_request}')
    # printColor(f'string_to_sign: {string_to_sign}')
    # printColor(f'secret_date: {secret_date}')
    # printColor(f'secret_service: {secret_service}')
    # printColor(f'secret_signing: {secret_signing}')
    # printColor(f'sign: {sign}')
    # printColor(f'authorization: {authorization}')
    # printColor(f'payload: {payload}')
    # printColor(f'headers: {headers}')

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



############ Translation End ############
