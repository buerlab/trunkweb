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

$(".menu-item").click(function(){
    $(".menu-item").removeClass("active");
    $(this).addClass("active");
    $(".main-container").hide();
    $("#" + $(this).data("id")).show();
});
$(".menu-item").eq(0).trigger("click");
