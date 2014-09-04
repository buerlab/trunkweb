$(function(){
    var refuseReason = "";
    var refuseId = "";

    var adminUserId = "53e9cd5915a5e45c43813d1c";

    var Datepattern=function(d,fmt) {           
    var o = {           
        "M+" : d.getMonth()+1, //月份           
        "d+" : d.getDate(), //日           
        "h+" : d.getHours()%12 == 0 ? 12 : d.getHours()%12, //小时           
        "H+" : d.getHours(), //小时           
        "m+" : d.getMinutes(), //分           
        "s+" : d.getSeconds(), //秒           
        "q+" : Math.floor((d.getMonth()+3)/3), //季度           
        "S" : d.getMilliseconds() //毫秒           
        };           
    var week = {           
    "0" : "/u65e5",           
    "1" : "/u4e00",           
    "2" : "/u4e8c",           
    "3" : "/u4e09",           
    "4" : "/u56db",           
    "5" : "/u4e94",           
    "6" : "/u516d"              
    };           
    if(/(y+)/.test(fmt)){           
        fmt=fmt.replace(RegExp.$1, (d.getFullYear()+"").substr(4 - RegExp.$1.length));           
    }           
    if(/(E+)/.test(fmt)){           
        fmt=fmt.replace(RegExp.$1, ((RegExp.$1.length>1) ? (RegExp.$1.length>2 ? "/u661f/u671f" : "/u5468") : "")+week[d.getDay()+""]);           
    }           
    for(var k in o){           
        if(new RegExp("("+ k +")").test(fmt)){           
            fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));           
        }           
    }           
    return fmt;           
}

    var confirmInfoArray=[];

    var bindEvent = function(){

        $("#confirmInfo-confirm").click(function(){
            getData();
        });

        $(".confirmInfo-usertype-mode").click(function(){
            $(".confirmInfo-usertype-mode").removeClass("btn-primary");
            $(".confirmInfo-usertype-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            getData();
        });


        $(".confirmInfoPaginationWrapper").delegate(".pageLi","click",function(){
            var index = +$(this).html();
            $(".confirmInfoPaginationWrapper").data("current",index);
            getData();
        });

        $("#confirmInfoTable").delegate(".success","click",function(){
            var dataJson = $(this).parent().data("data");
            dataJson.sender = adminUserId;
            dataJson.userId = adminUserId;
            if($(this).html() != "处理中"){
                confirmBill(dataJson);
                $(this).html("处理中");
            }
            
            
        });

        $("#confirmInfoTable").delegate(".fail","click",function(){
            refuseId = $(this).parent().data("id");
        });

        $("#confirmInfoTable").delegate(".refuse-resson","click",function(){
            refuseReason = $(this).html();
            refuseBill({
                id : refuseId,
                reason : refuseReason
            });
        });
    }
 /******************
  * confirmInfo 数据总览  bengin
  *****************/    

    var getParam = function(){
        var param = {};
        param.usertype = $(".confirmInfo-usertype-mode.btn-primary").data("usertype");
        param.state = "confirming";

        if($("#confirmInfo-date-from").val().length>0){
            try{
                param.from = + getDate($("#confirmInfo-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#confirmInfo-date-to").val().length>0){
            try{
                param.to = + getDate($("#confirmInfo-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }

        if($("#confirmInfo-input-search").val().trim()==""){
        }else{
            param.keyword = $("#confirmInfo-input-search").val().trim();
        }

        if($(".confirmInfoPaginationWrapper").data("current") && $(".confirmInfoPaginationWrapper").data("current")!=""){
            param.page = $(".confirmInfoPaginationWrapper").data("current");
        }

        if($("#confirmInfo-input-perpage").val()==""){

        }else{
            param.perpage = $("#confirmInfo-input-perpage").val().trim();
        }
        
        return param;
    }


    var renderPage = function(data){

        var page = data.curPage;
        var pageNum = data.pageCount;

        var fontTemp = '<ul class="pagination">';
        var backTemp = '</ul>';

        var html = fontTemp;
        for(var i =1;i<pageNum+1;i++){
            if(i ==page){
                html += '<li class="active"><a class="pageLi" href="javascript:void(0);">'+i +'</a></li>';
            }else{
                html += '<li><a class="pageLi" href="javascript:void(0);">'+i +'</a></li>';
            }
            
        }

        html += backTemp;
        $(".confirmInfoPaginationWrapper").empty();
        $(".confirmInfoPaginationWrapper").append(html);
        $(".confirmInfoPaginationWrapper").data("current",page);
    }

    var render = function(data,page){
        renderPage(data,page);

        $("#confirmInfoTable tbody").empty();

        // <th>编辑者</th>
        // <th>提交时间</th>
        // <th>消息类型</th>
        // <th>称呼</th>
        // <th>电话号码</th>
        // <th>出发地</th>
        // <th>目的地</th>
        // <th>详细信息</th>
        // <th>备注</th>
        // <th>操作</th>

        $.each(data.data,function(k,v){

            var renderUserType = function(usertype){
                if(usertype=="driver"){
                    return "车源(求货)";
                }else if(usertype=="owner"){
                    return "货源(求车)";
                }else{
                    return ""
                }
            }

            var safeRender =function(key){
                if (key){
                    return key;
                }else{
                    return "";
                }
            }
            var renderInfo = function(data){
                var ret = "";
                if (data.billType == "trunk"){
                    ret += "车长:" + safeRender(data.trunkLength) + ";";
                    ret += "车辆类型:" + safeRender(data.trunkType) + ";";
                    ret += "回程时间:" + (data.billTime ?  Datepattern(new Date(data.billTime * 1000),"yyyy-MM-dd HH:mm:ss") : "") + ";";
                }
                if (data.billType == "goods"){
                    ret += "货重:" + safeRender(data.weight) + ";";
                    ret += "货物名称:" + safeRender(data.material) + ";";
                    ret += "发货时间:" + (data.billTime ?  Datepattern(new Date(data.billTime * 1000),"yyyy-MM-dd HH:mm:ss") : "") + ";";
                }
                ret += "有效期:" + data.validTimeSec ? data.validTimeSec /(24 * 60 * 60) : ""+ ";";
                return ret;
            }

            var renderItem = function(data){

                var dataStr = JSON.stringify(data);

                var template = '<tr id="tr_'+ data._id.$oid +'">\
                <td>'+ (data.editor? data.editor:"无") +'</td>\
                <td>'+ (data.sendTime ?  Datepattern(new Date(data.sendTime * 1000),"yyyy-MM-dd HH:mm:ss") : "") +'</td>\
                <td>'+ renderUserType(data.userType) +'</td>\
                <td>'+ data.senderName +'</td>\
                <td>'+ data.phoneNum +'</td>\
                <td>'+ data.fromAddr +'</td>\
                <td>'+ data.toAddr +'</td>\
                <td>'+ renderInfo(data) +'</td>\
                <td>'+ (data.comment? data.comment:"无") +'</td>\
                <td>\
                    <div class="btn-group" data-data=\'' + dataStr + '\' data-id= "'+ data._id.$oid+'"">\
                      <button type="button" class="btn btn-primary success">通过</button>\
                       <button type="button" class="btn btn-danger dropdown-toggle fail" data-toggle="dropdown">驳回<span class="caret"></span></button>\
                            <ul class="dropdown-menu" role="menu">\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">昵称太长了，最好四个字以内</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">昵称格式不对，</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">这条信息已经录用过了，请放弃录入</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">备注太长了，精简一点</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">备注的格式不太好，注意标点符号</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">备注不能显示任何手机号码，请删掉</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">备注显示无关内容，请删掉</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">地址格式不对</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">地址不对</a></li>\
                              <li><a  class= "refuse-resson" href="javascript:void(0);">其他错误，请联系管理员</a></li>\
                            </ul>\
                    </div>\
                </td>\
                <td>'+ (data.rawText? data.rawText:"无") +'</td>\
                </tr>';
                return template;
            } 

            $("#confirmInfoTable tbody").append(renderItem(v));
        });
    }



    var getData= function(){
        var url = "http://localhost:9289/message/getVerifying";
        
        var data = getParam();

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    render(data);
                    // showRegionChart(confirmInfoArray);
                });
            },

            error: function(data) {
                errLog && errLog("getData() error");
            }
        });
    }

    getData();

    // var getToAddDataTest = function(){
    //     // confirmInfoArray = parseSummaryArray(_d);
    //     render(_d);
    // }
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();


    function confirmBill(_param){
        var url = "http://localhost:9289/message/confirm";
                   
        var param = {
            id :_param._id.$oid
        }

        var jqxhr = $.ajax({
            url: url,
            data: param,
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    sendBill2(_param);
                });
            },

            error: function(data) {
                errLog && errLog("message/confirm error");
            }
        });
    }

    function sendBill2(_param){
        var url = "http://115.29.8.74:9288/api/bill/send";
                   
        var param = _param;
        if(param==null){
            return;
        }

        var jqxhr = $.ajax({
            url: url,
            data: param,
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    $("#tr_"+_param._id.$oid).hide("fast",function(){
                        $("#tr_"+_param._id.$oid).remove();
                    });
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("/api/bill/send error");
            }
        });
    }

    function refuseBill(_param){
        var url = "http://localhost:9289/message/refuse";
                
        if(_param.id == null || _param.id == ""){
            showTips("id错误");
            return;
        }
        var jqxhr = $.ajax({
            url: url,
            data: _param,
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                     $("#tr_"+_param.id).hide("fast",function(){
                        $("#tr_"+_param.id).remove();
                    });
                });
            },

            error: function(data) {
                errLog && errLog("message/refuse error");
            }
        });
    }
    

});
