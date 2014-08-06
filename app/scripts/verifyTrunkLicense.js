$(function() {
    var $trunkLicenseTableBody = $("#trunkLicenseTable tbody");
    var loadVerifyingUsers = function(){
        var jqxhr = $.ajax({
            url: "/api/verifyTrunkLicense",
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
              <td>'+ data.licensePlate +'</td>\
              <td>'+ data.trunkLicense +'</td>\
              <td>\
                <img height="320" src = "'+ data.trunkLicensePicFilePath+'" />\
              </td>\
              <td>\
                <div class="btn-group btn-group-lg" data-licenseplate="'+data.licensePlate+'" data-id= "'+ data._id.$oid +'">\
                  <button type="button" class="btn btn-success pass">审核通过</button>\
                  <button type="button" class="btn btn-danger fail">审核失败</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        $trunkLicenseTableBody.empty();
        for (var i = 0; i < data.length; i++) {
            $trunkLicenseTableBody.append(renderItem(data[i]));
        };
    }

    $trunkLicenseTableBody.delegate(".pass","click",function(){
        debugger;
        var $this = $(this);
        id = $this.parent().data("id");
        licensePlate = $this.parent().data("licenseplate");
         var jqxhr = $.ajax({
            url: "/api/verifyTrunkLicense",
            data: {
                "userid": id,
                "licensePlate":licensePlate,
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

    $trunkLicenseTableBody.delegate(".fail","click",function(){
        debugger;
        var $this = $(this);
        id = $this.parents().data("id");
        licensePlate = $this.parents().data("licenseplate");
         var jqxhr = $.ajax({
            url: "/api/verifyTrunkLicense",
            data: {
                "userid": id,
                "licensePlate":licensePlate,
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