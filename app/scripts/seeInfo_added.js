$(function(){
    var addedStatArray=[];
    var adminUserId = "53e9cd5915a5e45c43813d1c";
    var bindEvent = function(){

        $(".addedStat-usertype").click(function(){
            $(".addedStat-usertype").removeClass("btn-primary");
            $(".addedStat-usertype").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            $(".addedStatPaginationWrapper").data("current",1);

            if($(this).data("usertype") == "owner"){
                $("#todayTrunkInfoList").hide();
                $("#todayGoodsInfoList").show();
            }else if($(this).data("usertype") == "driver"){
                $("#todayTrunkInfoList").show();
                $("#todayGoodsInfoList").hide();                
            }else{
                $("#todayTrunkInfoList").hide();
                $("#todayGoodsInfoList").hide();   
            }
            getData();
        });

        $("#addedStat-confirm").click(function(){
            debugger;
            // getDataTest2();
            getData();
            // getDataTest();
        });

        $(".addedStatPaginationWrapper").delegate(".pageLi","click",function(){
            var index = +$(this).html();
            $(".addedStatPaginationWrapper").data("current",index);
            getData();
        });
    }
 /******************
  * addedStat 数据总览  bengin
  *****************/    

    var getParam = function(){
        var param = {};
        
        param.usertype = $(".addedStat-usertype.btn-primary").data("usertype");
        if($("#addedStat-date-from").val().length>0){
            try{
                param.from = + getDate($("#addedStat-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#addedStat-date-to").val().length>0){
            try{
                param.to = + getDate($("#addedStat-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }

        if($("#addedStat-addr-to").val().trim()==""){
        }else{
            param.toAddr = $("#addedStat-addr-to").val().trim();
        }

        if($("#addedStat-addr-from").val().trim()==""){
        }else{
            param.fromAddr = $("#addedStat-addr-from").val().trim();
        }
        

        if($("#addedStat-input-keyword").val().trim()==""){
        }else{
            param.keyword = $("#addedStat-input-keyword").val().trim();
        }

        if($(".addedStatPaginationWrapper").data("current") && $(".addedStatPaginationWrapper").data("current")!=""){
            param.page = $(".addedStatPaginationWrapper").data("current");
        }

        if($("#addedStat-input-perpage").val()==""){
        }else{
            param.perpage = $("#addedStat-input-perpage").val().trim();
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
        $(".addedStatPaginationWrapper").empty();
        $(".addedStatPaginationWrapper").append(html);
        $(".addedStatPaginationWrapper").data("current",page);
    }

    var render = function(data,page){
        renderPage(data,page);

        $("#addedStatTable tbody").empty();

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
            var renderItem = function(data){
                var template = '<tr id="tr_'+ data._id.$oid +'">\
                    <td><input type="checkbox" class="info-list-checkbox" /></td>\
                    <td><a href="javascript:void(0);" class="fail" data-id=\"'+ data._id.$oid +'\" data-usertype=\"'+ data.userType +'\">删除</a></td>\
                  <td class="phoneNum-text">'+ data.phoneNum +'</td>\
                  <td class="senderName-text">'+ data.senderName +'</td>\
                  <td>'+ renderUserType(data.userType) +'</td>\
                  <td class="fromAddr-text">'+ data.fromAddr +'</td>\
                  <td class="toAddr-text">'+ data.toAddr +'</td>\
                  <td class="sendTime-text">'+ (data.sendTime ?  Datepattern(new Date(data.sendTime * 1000),"yyyy-MM-dd HH:mm:ss") : "") +'</td>\
                  <td class="comment-text">'+ (data.comment? data.comment:"无") +'</td>\
                  <td>'+ (data.editor? data.editor:"无") +'</td>\
                </tr>';
                return template;
            } 

            $("#addedStatTable tbody").append(renderItem(v));
        });
    }


    var getData= function(){
        var url = "/stat/added";
        
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
                    // showRegionChart(addedStatArray);
                });
            },

            error: function(data) {
                errLog && errLog("getData() error");
            }
        });
    }

    $("#addedStatMenu").click(function(){
        getData();
    });
    // getData();

    var getDataTest = function(){
        // addedStatArray = parseSummaryArray(_d);
        render(_d);
    }
     /******************
      * summary 数据总览  end
      *****************/  


    $("#todayTrunkInfoList").click(function(){
        var ret = "【天天回程车】" + Datepattern(new Date(),"MM-dd") + "今日车讯:\r\n";
        var array = []
        $("#addedStatTable tr").each(function(k, v){
            if($(this).find(".info-list-checkbox").get(0) && $(this).find(".info-list-checkbox").get(0).checked){
                var phoneNum = $(this).find(".phoneNum-text").html();
                var nickname = $(this).find(".senderName-text").html();
                var fromAddr = $(this).find(".fromAddr-text").html();
                var toAddr = $(this).find(".toAddr-text").html();
                var sendTime = $(this).find(".sendTime-text").html();
                var comment = $(this).find(".comment-text").html();

                var getAddr = function(addr){
                    addrArray = addr.split("-");
                    if(addrArray.length !=3){
                        showTips("地址格式不对");
                        return;
                    }
                    return (addrArray[0] + addrArray[1] + addrArray[2]).replace(/不限/g,"");
                }

                // array.push( getAddr(fromAddr) + " 到 " + getAddr(toAddr) + " " + nickname + " 联系方式：" + phoneNum + " " + comment + "\r\n");
                array.push( getAddr(fromAddr) + " 到 " + getAddr(toAddr) + " " + nickname + " " + comment + "\r\n");
             }
        });
        array.sort();
        ret += array.join("");
        ret += "\r\n";
        ret += "更多回程车信息尽在【天天回程车】\r\n";
        ret += "官方QQ群：215785844\r\n";
        ret += "官方网址：http://t.cn/RhfEjuH \r\n";
        ret += "点击直接下载：http://t.cn/Rhfnzt7 \r\n";
        ret += "微信公众账号开通了！搜索【天天回程车】可以直接在上面免费查看大量车源信息哦\r\n";
        
        console.log(ret);
        showTips("已生成，按F12 在console里面获取");
    });


    $("#todayGoodsInfoList").click(function(){
        var ret = "【天天回程车】" + Datepattern(new Date(),"MM-dd") + "今日货讯:\r\n";
        var array = [];
        $("#addedStatTable tr").each(function(k, v){
            if($(this).find(".info-list-checkbox").get(0) && $(this).find(".info-list-checkbox").get(0).checked){
                var phoneNum = $(this).find(".phoneNum-text").html();
                var nickname = $(this).find(".senderName-text").html();
                var fromAddr = $(this).find(".fromAddr-text").html();
                var toAddr = $(this).find(".toAddr-text").html();
                var sendTime = $(this).find(".sendTime-text").html();
                var comment = $(this).find(".comment-text").html();

                var getAddr = function(addr){
                    addrArray = addr.split("-");
                    if(addrArray.length !=3){
                        showTips("地址格式不对");
                        return;
                    }
                    return (addrArray[0] + addrArray[1] + addrArray[2]).replace(/不限/g,"");
                }

                array.push(getAddr(fromAddr) + " 到 " + getAddr(toAddr) + " " + nickname + " " + comment + "\r\n");
             }
        });
        array.sort();
        ret += array.join("");
        ret += "\r\n";
        ret += "更多货源信息尽在【天天回程车】\r\n";
        ret += "官方QQ群：215785844\r\n";
        ret += "官方网址：http://t.cn/RhfEjuH \r\n";
        ret += "点击直接下载：http://t.cn/Rhf3I4W \r\n";
        ret += "微信公众账号开通了！搜索【天天回程车】可以直接在上面免费查看大量货源信息哦\r\n";
        console.log(ret);
        showTips("已生成，按F12 在console里面获取");
    });



    $("#check-all").click(function(){
        if($("#check-all").html() == "全选"){
            $(".info-list-checkbox").each(function(k,v){
                v.checked = true;
            });
            $("#check-all").html("全不选");
        }else{
            $(".info-list-checkbox").each(function(k,v){
                v.checked = false;
            });
            $("#check-all").html("全选");
        }
        
    });
    $("#addedStat-date-from").val(Datepattern(new Date(),"yyyy-MM-dd"))
    $("#addedStat-date-to").val(Datepattern(new Date(),"yyyy-MM-dd"))
    bindEvent();

    $("#addedStatTable").delegate(".fail","click",function(){

            if(!confirm("确定要删除这条请求吗？")){
                return;
            }
            debugger;
            var $this = $(this),
                id = $this.data("id");

            var tds = $("#tr_"+ id).find("td");
            var d = {
                phoneNum : tds.eq(2).html(),
                fromAddr : tds.eq(5).html(),
                toAddr : tds.eq(6).html(),
                userType : $this.data("usertype")
            }


            var jqxhr = $.ajax({
                url: "/addedmessage/delete",
                data: d,
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger; 
                        $this.parents().filter("tr").hide("fast", function() {
                            $(this).remove();
                        });
                    });
                },


                error: function(data) {
                    errLog && errLog("api/bill/remove error");
                }
            });

            // var realDelete = function(){
            //     var jqxhr = $.ajax({
            //         url: "http://115.29.8.74:9288/api/bill/remove",
            //         data: {
            //             "billid": id,
            //             "userId": adminUserId,
            //             "userType": "owner"
            //         },
            //         type: "POST",
            //         dataType: "json",
            //         success: function(data) {
            //             dataProtocolHandler(data,function(data){
            //                 debugger; 
            //                 $this.parents().filter("tr").hide("fast", function() {
            //                     $(this).remove();
            //                 });
            //                 // location.href = "/";
            //             });
            //         },

            //         error: function(data) {
            //             errLog && errLog("http://115.29.8.74:9288/api/bill/remove error");
            //         }
            //     });
            // }
            
            return false;
        });

});
