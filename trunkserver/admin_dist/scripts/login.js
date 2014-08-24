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
		$navNickname.hide();
		$navLogout.show();
		$navOperate.show();
		// $navNickname.html($.cookie("username"));
	}else{
		$navLogin.show();
		$navRegister.show();
		$navNickname.hide();
		$navLogout.hide();
		$navOperate.hide();

		// $navNickname.html("");
	}


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

	loginFormParsley = $('#loginForm').parsley();
	$("#loginBtn").click(function(){
	   loginFormParsley.validate();

	   if (loginFormParsley.isValid()){
	   		loginAjax();
	   }
	});

	var loginAjax = function(){
		var userinput = $("#phoneNum").val();
		var psw = $("#password").val();
		var jqxhr = $.ajax({
			url: "/api/admin/login",
			data: {
				username: userinput,
				password: psw
			},
			type: "POST",
			dataType: "json",
			success: function(data) {
				debugger;
				dataProtocolHandler(data,function(){
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
				errLog && errLog("loginAjax");
			}
		});
	}

});