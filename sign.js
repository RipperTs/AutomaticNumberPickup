// openid oq_eI5Q4LQjpLlWN78PbQWlSI8tY

function xorEncryptDecrypt(a, t) {
    for (var e = "", o = 0; o < a.length; o++) e += String.fromCharCode(a.charCodeAt(o) ^ t.charCodeAt(o % t.length));
    return e
}

function utf8Encode(a) {
    return unescape(encodeURIComponent(a))
}

function base64Encode(a) {
    for (var t = utf8Encode(a), e = "", o = 0, d = 0, s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="; t.charAt(0 | d) || (s = "=", d % 1); e += s.charAt(63 & o >> 8 - d % 1 * 8)) o = o << 8 | t.charCodeAt(d += 3 / 4);
    return e
}

function getCode(openid, lat = '', lon = '') {
    if (lat !== '' || lon !== '') {
        lat += '26996528';
        lon += '93836805'
    }
    const signParams = {
        lat: lat + "8967876876876876876876785675765765765543454354345345",
        lon: lon + "6786876876868976876868686868687678674353453453434534534",
        openid: openid,
        newtime: Math.floor(Date.now() / 1e3),
        htime: Date.now()
    };

    const i = JSON.stringify(signParams);
    return base64Encode(xorEncryptDecrypt(i, "yaQINGKEJI826paidui"));
}

// Base64解码函数
function base64Decode(str) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    let output = '';
    str = str.replace(/[^A-Za-z0-9\+\/\=]/g, '');

    let i = 0;
    while (i < str.length) {
        const enc1 = chars.indexOf(str.charAt(i++));
        const enc2 = chars.indexOf(str.charAt(i++));
        const enc3 = chars.indexOf(str.charAt(i++));
        const enc4 = chars.indexOf(str.charAt(i++));

        const chr1 = (enc1 << 2) | (enc2 >> 4);
        const chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
        const chr3 = ((enc3 & 3) << 6) | enc4;

        output = output + String.fromCharCode(chr1);
        if (enc3 !== 64) output = output + String.fromCharCode(chr2);
        if (enc4 !== 64) output = output + String.fromCharCode(chr3);
    }

    return decodeURIComponent(escape(output));
}


// 完整的解密函数
function decrypt(encryptedStr, key) {
    // 1. 先base64解码
    const base64Decoded = base64Decode(encryptedStr);
    // 2. 再进行XOR解密
    return xorEncryptDecrypt(base64Decoded, key);
}