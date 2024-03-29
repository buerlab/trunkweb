function showTips(str){
    alert(str);
    console.log(str);
}

function errLog(str){
    debugger;
    console.log("ERROR:" +str);
    alert(str);
}

function dataProtocolHandler(data,successCallback,failCallback){
    if(data){
        if(data.code===0){
            if(successCallback && typeof successCallback == "function"){
                successCallback(data.data,data.datatype);
            }
        }else{
            if(failCallback && typeof failCallback == "function"){
                failCallback(data.code,data.msg,data.data,data.datatype);
            }else{
                showTips("data msg="+ data.msg+";data.code="+ data.code);
            }
           
        }
    }else{
        showTips("data is null");
    }
}

//header登录态展示处理
//依赖$.cookie

var G_data = G_data || {};
G_data.admin = G_data.admin || {};
if(localStorage){
	G_data.admin = JSON.parse(localStorage.getItem("admin"))|| {};
}



(loginHandler = function () {
	var $navLogin = $("#navLogin"),
		$navRegister = $("#navRegister"),
		$navNickname = $("#navNickname"),
		$navLogout = $("#navLogout"),
		$navVerifyIDNum = $("#navVerifyIDNum"),
		$navOperate = $(".navOperate"),
		$navVerifyDriverLicense = $("#navVerifyDriverLicense");

	if ($.cookie("mark") && $.cookie("username")){
		$navLogin.hide();
		$navRegister.hide();
		$navNickname.show();
		$navLogout.show();
		if(G_data.admin && G_data.admin.username){
			$navNickname.html(G_data.admin.username);
		}
		
	}else{
		$navLogin.show();
		$navRegister.show();
		$navNickname.hide();
		$navLogout.hide();
		$navOperate.hide();

		$navNickname.html("");
	}
	debugger;
	$.each(G_data.admin,function(k,v){
		if(k.indexOf("Permission")>=0){
			if(v){
				$("."+k).show();
			}else{
				$("."+k).hide();
			}
		}
	});

	$("#navNickname").click(function(){
		location.href = "me.html";
	});


	$navLogout.click(function(){
		var loginoutAjax = function(){
			var jqxhr = $.ajax({
				url: "/api/admin/logout",
				type: "POST",
				dataType: "json",
				success: function(data) {
					debugger;
					dataProtocolHandler(data,function(){
						location.href = location.href;
						G_data.admin= {};
						localStorage.setItem("admin","{}");
						
					});
					
				},
				error: function(data) {
					errLog && errLog("loginoutAjax");
				}
			});
		}
		loginoutAjax();
	});
})();



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
        ret += "<p>车长:" + safeRender(data.trunkLength) + "米</p>";
        ret += "<p>载重:" + safeRender(data.trunkLoad) + "吨</p>";
        ret += "<p>车辆类型:" + safeRender(data.trunkType) + "</p>";
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
            var template = '<tr id="tr_'+ data.id +  '">\
              <td>'+ data.editor +'</td>\
              <td>'+ (data.time ?  Datepattern(new Date(data.time),"yyyy-MM-dd HH:mm:ss") : "") +'</td>\
              <td>'+ renderUserType(data.userType) +'</td>\
              <td>'+ data.role +'</td>\
              <td>'+ data.nickName +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.qqgroup + ":" + data.qqgroupid +'</td>\
              <td>'+ renderInfo(data) +'</td>\
              <td>'+ renderRoute(data) +'</td>\
              <td>'+ data.comment +'</td>\
              <td>\
                <div class="btn-group" data-id= "'+ data.id +'">\
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

    $("#table").delegate(".delete", "click",function(){
        var id = $(this).parent().data("id");

        var jqxhr = $.ajax({
            url: "http://115.29.8.74:9288/api/regular/remove",
            data: {
                "id":id
            },
            
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    $("#tr_" + id).hide("fast",function(){
                        $(this).remove();   
                    });
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("删除常规路线失败");
            }
        });
    });

});