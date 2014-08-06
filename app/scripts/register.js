$(function() {
	registerFormParsley = $('#registerForm').parsley();
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
				password: psw
			},
			type: "POST",
			dataType: "json",
			success: function(data) {
				dataProtocolHandler(data,function(){
					showTips("注册成功");
					location.href = "main.html";
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