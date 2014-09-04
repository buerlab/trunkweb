var getDate = function(str){
        var b1 = str.split("-");
        return new Date(b1[0],(b1[1]-1),b1[2],0,0,0);
    }

var parseSummaryArray = function(data){
    var summaryArray =  [];
    $.each(data,function(k,v){
        var a = v;
        a.time = k.replace("t-","");
        summaryArray.push(a);
    });

    summaryArray.sort(function(a,b){

        if(a.time == "summary"){
            return -1;
        }

        if(b.time == "summary"){
            return 1;
        }
        if(+getDate(a.time) > +getDate(b.time)){
            return 1;
        }else if(+getDate(a.time) == +getDate(b.time)){
            return 0;
        }else{
            return -1;
        }
    });
    return summaryArray;
}

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




$(function(){

    var tmpLog = [];

    var getLogList = function(){
        var jqxhr = $.ajax({
            url: "/log/getList",
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    render(data.sort());
                });
            },
            error: function(data) {
                errLog && errLog("getLogList error");
            }
        });
    }

    var render = function(data){
        $(".list-group").empty();

        $.each(data,function(k,v){
            var tmp = '<a href="javascript:void(0);" class="menu-item list-group-item">{name}</a>';
            var html = tmp.replace("{name}",v);
            $(".list-group").prepend(html);
        });
    }

    var getLog = function(filename,keyword,viewmode){
        var jqxhr = $.ajax({
            url: "/log/get",
            data: {
                "filename":filename
            },
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    renderLog(data,keyword,viewmode);
                    tmpLog = data;
                });
            },

            error: function(data) {
                errLog && errLog("getLog error");
            }
        });
    }

    var renderLog = function(data,keyword,viewmode){
        $(".log-container").empty();

        if(viewmode=="倒序"){
            $.each(data, function(k, v){
                if(keyword && keyword != ""){
                    if(v.indexOf(keyword) >=0){
                        a = v.replace(keyword, "<span class='keyword' style='color:red'>" + keyword + "</span>");
                        $(".log-container").prepend(a);
                    }
                }else{
                    $(".log-container").prepend("<p>" + k + " : " + v + "</p>");
                }
            });
        }else{
            $.each(data, function(k, v){
                if(keyword && keyword != ""){
                    if(v.indexOf(keyword) >=0){
                        a = v.replace(keyword, "<span class='keyword' style='color:red'>" + keyword + "</span>");
                        $(".log-container").append("<p>" + k + " : " + a + "</p>");
                    }
                }else{
                    $(".log-container").append("<p>" + k + " : " + v + "</p>");
                }
            });

            
        }
        
        
    }

    $(".log-view-mode").click(function(){
        $(".log-view-mode").removeClass("btn-primary");
        $(".log-view-mode").addClass("btn-default");
        $(this).removeClass("btn-default");
        $(this).addClass("btn-primary");

        if(tmpLog){
            renderLog(tmpLog,$("#keyword").val(), $(".log-view-mode.btn-primary").data("viewmode"));
        }else{
            getLog( $(".menu-item.active").html(), $("#keyword").val(), $(".log-view-mode.btn-primary").data("viewmode"))
        }

    });

    $(".list-group").delegate(".menu-item","click",function(){
        $(".menu-item").removeClass("active");
        $(this).addClass("active");
        $("#keyword").val("");
        getLog($(this).html(),$("#keyword").val(), $(".log-view-mode.btn-primary").data("viewmode"));
    });

    $("#confirm").click(function(){
        if(tmpLog){
            renderLog(tmpLog,$("#keyword").val(), $(".log-view-mode.btn-primary").data("viewmode"));
        }else{
            getLog( $(".menu-item.active").html(), $("#keyword").val(), $(".log-view-mode.btn-primary").data("viewmode"))
        }
    });
    getLogList();
   
});


