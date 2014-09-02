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



	$navLogout.click(function(){
		var loginoutAjax = function(){
			var jqxhr = $.ajax({
				url: "/api/admin/logout",
				type: "POST",
				dataType: "json",
				success: function(data) {
					debugger;
					dataProtocolHandler(data,function(){
						if(location.pathname.indexOf("main.html")>=0){
							location.href = "index.html";
						}else{
							location.href = location.href;

						}
						
					},function(code,msg,data,dataType){
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
    var $driverLicenseTableBody = $("#driverLicenseTable tbody");
    var loadVerifyingUsers = function(){
        var jqxhr = $.ajax({
            url: "/api/verifyDriverLicense",
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    render(data);
                    // location.href = "/";
                },function(code,msg,data,dataType){
                    if(code == -7){
                        showTips("账号密码输入有误");
                    }else{
                        showTips("未知错误");
                    }
                });
            },

            error: function(data) {
                errLog && errLog("loginAjax");
            }
        });
    }

    var render = function(data){
        var renderItem = function(data){
            var template = '<tr id="tr_'+ data._id.$oid +'">\
              <td>'+ data._id.$oid +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.nickName +'</td>\
              <td>'+ data.driverLicense +'</td>\
              <td>\
                <img height="320" src = "'+ data.driverLicensePicFilePath+'" />\
              </td>\
              <td>\
                <div class="btn-group btn-group-lg" data-id= "'+ data._id.$oid +'"">\
                  <button type="button" class="btn btn-success pass">审核通过</button>\
                  <button type="button" class="btn btn-danger fail">审核失败</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        $driverLicenseTableBody.empty();
        for (var i = 0; i < data.length; i++) {
            $driverLicenseTableBody.append(renderItem(data[i]));
        };
    }

    $driverLicenseTableBody.delegate(".pass","click",function(){
        debugger;
        var $this = $(this);
        id = $this.parents().data("id");
         var jqxhr = $.ajax({
            url: "/api/verifyDriverLicense",
            data: {
                "userid": id,
                "op":"pass",
            },
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    $this.parents().filter("tr").hide("fast", function() {
                        $(this).remove();
                    });
                    // location.href = "/";
                },function(code,msg,data,dataType){
                    if(code == -7){
                        showTips("账号密码输入有误");
                    }else{
                        showTips("未知错误");
                    }
                });
            },

            error: function(data) {
                errLog && errLog("pass verify fail");
            }
        });
        return false;
    });

    $driverLicenseTableBody.delegate(".fail","click",function(){
        debugger;
        var $this = $(this);
        id = $this.parents().data("id");
         var jqxhr = $.ajax({
            url: "/api/verifyDriverLicense",
            data: {
                "userid": id,
                "op":"fail",
            },
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    $this.parents().filter("tr").hide("fast", function() {
                        $(this).remove();
                    });
                    // location.href = "/";
                },function(code,msg,data,dataType){
                    if(code == -7){
                        showTips("账号密码输入有误");
                    }else{
                        showTips("未知错误");
                    }
                });
            },

            error: function(data) {
                errLog && errLog("pass verify fail");
            }
        });
        return false;
    });
    loadVerifyingUsers();
});