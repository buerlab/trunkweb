$(function(){
    var addedStatArray=[];

    var bindEvent = function(){

        $(".addedStat-usertype").click(function(){
            $(".addedStat-usertype").removeClass("btn-primary");
            $(".addedStat-usertype").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            $(".addedStatPaginationWrapper").data("current",1);
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
                  <td>'+ data.phoneNum +'</td>\
                  <td>'+ data.senderName +'</td>\
                  <td>'+ renderUserType(data.userType) +'</td>\
                  <td>'+ data.fromAddr +'</td>\
                  <td>'+ data.toAddr +'</td>\
                  <td>'+ (data.sendTime ?  Datepattern(new Date(data.sendTime * 1000),"yyyy-MM-dd HH:mm:ss") : "") +'</td>\
                  <td>'+ (data.comment? data.comment:"无") +'</td>\
                  <td>'+ (data.editor? data.editor:"无") +'</td>\
                </tr>';
                return template;
            } 

            $("#addedStatTable tbody").append(renderItem(v));
        });
    }


    var getData= function(){
        var url = "http://115.29.8.74:9289/stat/added";
        
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

    getData();

    var getDataTest = function(){
        // addedStatArray = parseSummaryArray(_d);
        render(_d);
    }
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();
});
