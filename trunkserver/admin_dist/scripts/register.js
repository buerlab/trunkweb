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
	var registerFormParsley = $('#registerForm').parsley();
		$("#registerBtn").click(function(){
		   registerFormParsley.validate();

		   if (registerFormParsley.isValid()){
		   		registerAjax();
		   }
	});

	var registerAjax = function(){
		var username = $("#username").val();
		var psw = $("#password").val();
		var jqxhr = $.ajax({
			url: "/api/admin/register",
			data: {
				username: username,
				password: psw,
				realname : $("#realname").val(),
				bankName : $("#bankName").val(),
				bankNum :$("#bankNum").val(),
				phoneNum : $("#phoneNum").val()
			},
			type: "POST",
			dataType: "json",
			success: function(data) {
				dataProtocolHandler(data,function(){
					showTips("注册成功，你现在还没有任何权限，联系18575594301或15507507400开通权限");
					location.href = "/";
				},function(code,msg,data,dataType){
					if(code == -7){
						showTips("账号密码输入有误");
					}else{
						showTips("未知错误");
					}
				});
				
			},
			error: function(data) {
				errLog && error("registerAjax");
			}
		});
	} 
});