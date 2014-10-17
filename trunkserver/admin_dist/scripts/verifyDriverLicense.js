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
                });
            },

            error: function(data) {
                errLog && errLog("loadVerifyingUsers");
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
                  <button type="button" class="btn btn-danger dropdown-toggle fail" data-toggle="dropdown">审核失败<span class="caret"></span></button>\
                  <ul class="dropdown-menu" role="menu">\
                      <li><a  class= "refuse-resson" href="javascript:void(0);" data-type="1">太模糊了</a></li>\
                      <li><a  class= "refuse-resson" href="javascript:void(0);" data-type="2">照片和号码对不上</a></li>\
                      <li><a  class= "refuse-resson" href="javascript:void(0);" data-type="3">照片不符合要求</a></li>\
                    </ul>\
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
        var id = $this.parents().data("id");
        var $tr = $("#tr_" + id);
        var nick = $tr.find("td").eq(2).html();
        var phoneNum = $tr.find("td").eq(1).html();
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
                });
            },

            error: function(data) {
                errLog && errLog("pass verify fail");
            }
        });
        return false;
    });

    $driverLicenseTableBody.delegate(".refuse-resson","click",function(){
        debugger;
        var $this = $(this);
        id = $this.parents().data("id");
         var jqxhr = $.ajax({
            url: "/api/verifyDriverLicense",
            data: {
                "userid": id,
                "op":"fail",
                "type":$(this).data("type"),
                "phoneNum":phoneNum,
                "nick":nick
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