$(function() {

    var Datepattern=function(d,fmt) {           
    var o = {           
        "M+" : d.getMonth()+1, //月份           
        "d+" : d.getDate(), //日           
        "h+" : d.getHours()%12 == 0 ? 12 : d.getHours()%12, //小时           
        "H+" : d.getHours(), //小时           
        "m+" : d.getMinutes(), //分           
        "s+" : d.getSeconds(), //秒           
        "q+" : Math.floor((d.getMonth()+3)/3), //季度           
        "S" : d.getMilliseconds() //毫秒           
        };           
    var week = {           
    "0" : "/u65e5",           
    "1" : "/u4e00",           
    "2" : "/u4e8c",           
    "3" : "/u4e09",           
    "4" : "/u56db",           
    "5" : "/u4e94",           
    "6" : "/u516d"              
    };           
    if(/(y+)/.test(fmt)){           
        fmt=fmt.replace(RegExp.$1, (d.getFullYear()+"").substr(4 - RegExp.$1.length));           
    }           
    if(/(E+)/.test(fmt)){           
        fmt=fmt.replace(RegExp.$1, ((RegExp.$1.length>1) ? (RegExp.$1.length>2 ? "/u661f/u671f" : "/u5468") : "")+week[d.getDay()+""]);           
    }           
    for(var k in o){           
        if(new RegExp("("+ k +")").test(fmt)){           
            fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));           
        }           
    }           
    return fmt;           
}

    var $tableBody = $("#table tbody");
    var getData = function(){
        var jqxhr = $.ajax({
            url: "http://115.29.8.74:9288/api/regular/get",
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    render(data);
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("获取常规路线失败");
            }
        });
    }

var renderUserType = function(usertype){
    if(usertype=="driver"){
        return "车源(求货)";
    }else if(usertype=="owner"){
        return "货源(求车)";
    }else{
        return ""
    }
}

var safeRender =function(key){
    if (key){
        return key;
    }else{
        return "";
    }
}
var renderInfo = function(data){
    var ret = "";
    if (data.userType == "driver"){
        ret += "车长:" + safeRender(data.trunkLength) + "米;";
        ret += "载重:" + safeRender(data.trunkLoad) + "吨;";
        ret += "车辆类型:" + safeRender(data.trunkType) + ";";
    }

    return ret;
}
var renderRoute = function(data){
    var ret = "";
    if(!data.routes){
        return ret;
    }

    $.each(data.routes,function(k,v){
        ret += '<p>' + v.fromAddr + "->" + v.toAddr + ";概率：" + v.probability + "</p>";
    })

    return ret;
}
    var render = function(data){
        var renderItem = function(data){
            var template = '<tr id="tr_'+ '">\
              <td>'+ data.editor +'</td>\
              <td>'+ (data.time ?  Datepattern(new Date(data.time),"yyyy-MM-dd HH:mm:ss") : "") +'</td>\
              <td>'+ renderUserType(data.userType) +'</td>\
              <td>'+ data.role +'</td>\
              <td>'+ data.nickName +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.qqgroup + ":" + data.qqgroupid +'</td>\
              <td>'+ renderInfo(data) +'</td>\
              <td>'+ renderRoute(data) +'</td>\
              <td>\
                <div class="btn-group btn-group-lg" data-id= "' +'"">\
                  <button type="button" class="btn btn-success edit">修改</button>\
                  <button type="button" class="btn btn-danger delete">删除</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        $tableBody.empty();
        for (var i = 0; i < data.length; i++) {
            $tableBody.append(renderItem(data[i]));
        };
    }

    getData();
});