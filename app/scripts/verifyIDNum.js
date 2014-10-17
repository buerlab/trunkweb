$(function() {
    var $IDNumTableBody = $("#IDNumTable tbody");
    var loadVerifyingUsers = function(){
        var jqxhr = $.ajax({
            url: "/api/verifyIDNum",
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
                errLog && errLog("获取身份证审核列表失败");
            }
        });
    }

    var render = function(data){
        var renderItem = function(data){
            var template = '<tr id="tr_'+ data._id.$oid +'">\
              <td>'+ data._id.$oid +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.nickName +'</td>\
              <td>'+ data.IDNum +'</td>\
              <td>\
                <img height="325" src = "'+ data.IDNumPicFilePath+'" />\
              </td>\
              <td>\
                <div class="btn-group btn-group-lg" data-id= "'+ data._id.$oid +'">\
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


        $IDNumTableBody.empty();
        for (var i = 0; i < data.length; i++) {
            $IDNumTableBody.append(renderItem(data[i]));
        };
    }

    $IDNumTableBody.delegate(".pass","click",function(){
        debugger;
        var $this = $(this);
        id = $this.parents().data("id");
         var jqxhr = $.ajax({
            url: "/api/verifyIDNum",
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
                errLog && errLog("通过失败");
            }
        });
        return false;
    });

    $IDNumTableBody.delegate(".refuse-resson","click",function(){
        debugger;
        var $this = $(this);
        var id = $this.parent().parent().parent().data("id");
        var $tr = $("#tr_" + id);
        var nick = $tr.find("td").eq(2).html();
        var phoneNum = $tr.find("td").eq(1).html();
         var jqxhr = $.ajax({
            url: "/api/verifyIDNum",
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
                errLog && errLog("驳回失败");
            }
        });
        return false;
    });
    loadVerifyingUsers();
});