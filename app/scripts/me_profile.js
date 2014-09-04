$(function(){
    registerFormParsley = $('#profileForm').parsley();
    $("#profileBtn").click(function(){
       registerFormParsley.validate();

       if (registerFormParsley.isValid()){
            registerAjax();
       }
    });

    var getProfile = function(){
        var jqxhr = $.ajax({
            url: "/api/admin/get",
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    render(data);
                });
                
            },
            error: function(data) {
                errLog && errLog("getProfile");
            }
        });
    }

    var render = function(data){
        $("#realname").val(data.realname);
        $("#bankName").val(data.bankName);
        $("#bankNum").val(data.bankNum);
        $("#phoneNum").val(data.phoneNum);
    }

    var editData = function(){
        var jqxhr = $.ajax({
            url: "/api/admin/edit",
            data: {
                realname : $("#realname").val(),
                bankName : $("#bankName").val(),
                bankNum :  $("#bankNum").val(),
                phoneNum : $("#phoneNum").val()
            },
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(){
                    showTips("修改成功");
                });
                
            },
            error: function(data) {
                errLog && error("editData");
            }
        });
    } 

    $("#editBtn").click(function(){
        editData();
    });

    getProfile();
});