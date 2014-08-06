function showTips(str){
    alert(str);
    console.log(str);
}

function errLog(str){
    debugger;
    console.log("ERROR:" +str);
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

 

    var $feebackTableBody = $("#feedbackTable tbody");
    var loadVerifyingUsers = function(){
        var jqxhr = $.ajax({
            url: "/userFeedback",
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


    // <th>id</th>
    //           <th>电话号码</th>
    //           <th>昵称</th>
    //           <th>反馈</th>
    var render = function(data){
        var renderItem = function(data){
            debugger;

            var d = new Date(data.time * 1000)
            var template = '<tr id="tr_'+ data._id.$oid +'">\
              <td>'+ data.userId +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.nickName +'</td>\
              <td>'+ data.feedbackString +'</td>\
              <td>'+ d +'</td>\
            </tr>';
            return template;
        }

        $feebackTableBody.empty();
        for (var i = 0; i < data.length; i++) {
            $feebackTableBody.append(renderItem(data[i]));
        };
    }

    loadVerifyingUsers();
});