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