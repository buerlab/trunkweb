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