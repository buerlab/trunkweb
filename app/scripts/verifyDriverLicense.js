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