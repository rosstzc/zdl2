function getCookie(name){
    var strCookie=document.cookie;
    var arrCookie=strCookie.split("; ");
    for(var i=0;i<arrCookie.length;i++){
        var arr=arrCookie[i].split("=");
        if(arr[0]===name)return arr[1];
    }
    return "";
}

// function getCookie(name)
// {
//     var arr,reg=new RegExp("(^| )"+name+"=([^;]*)(;|$)");
//     if(arr=document.cookie.match(reg))
//     return unescape(arr[2]);
//     else
//     return null;
// }



/*
* 读取特定Cookie的通用函数 (匹配是有问题的，是模糊匹配)
*/
function getSpecificCookie(name) {
    if(document.cookie.length > 0) {
        start = document.cookie.indexOf(name + "=");
            if( start !== -1) {
            start = start + name.length + 1;
            end = document.cookie.indexOf(";",start);
            if( end === -1) {
                end = document.cookie.length;
                }
        }
        return decodeURI(document.cookie.substring(start,end));
    }
    return "";
}
