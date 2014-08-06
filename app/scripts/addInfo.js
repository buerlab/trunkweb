



$(function() {
    var $goodsRadio = $("#goodsRadio"),
        $trunkRadio= $("#trunkRadio"),
        $nickname = $("#nickname"),
        $phoneNum = $("#phoneNum"),
        $goodsName = $("#goodsName"),
        $goodsWeight = $("#goodsWeight"),
        $goodsPrice = $("#goodsPrice"),
        $trunkType = $(".trunkType"),
        $licensePlate = $("#licensePlate"),
        $trunkLength = $("#trunkLength"),
        $trunkLoad = $("#trunkLoad"),
        $from = $("#from"),
        $to = $("#to"),
        $time = $("#time"),
        $validateTime = $("#validateTime"),
        $comment = $("#comment"),
        $confirmBtn = $(".confirmBtn"),
        $clearBtn = $(".clearBtn");

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


function initAddressSuggest(){
    var myAddress = []
for(var i =0;i<ADDRESS.length;i++){

    var provName= ADDRESS[i]["provName"];
    if(provName){
        myAddress.push(provName + "-不限-不限");
    }
    if(ADDRESS[i]["cities"]){
        var cities = ADDRESS[i]["cities"];
        for(var j =0;j<cities.length;j++){
            var cityName = cities[j]["cityName"];
            myAddress.push(provName + "-" + cityName + "-不限");
            var regions = cities[j]["regions"];
            for(var k =0;k<regions.length;k++){
                myAddress.push(provName + "-" + cityName + "-" + regions[k]["regionName"]);
            }
        }
    }
}



var region = new Bloodhound({
              datumTokenizer: Bloodhound.tokenizers.obj.chinese('value'),
              queryTokenizer: Bloodhound.tokenizers.chinese,
              // `states` is an array of state names defined in "The Basics"
              local: $.map(myAddress, function(myAddress) { return { value: myAddress }; }),
              limit:30
            });
 
// kicks off the loading/processing of `local` and `prefetch`
region.initialize();
 
$('.typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},

{
  name: 'region',
  displayKey: 'value',
  // `ttAdapter` wraps the suggestion engine in an adapter that
  // is compatible with the typeahead jQuery plugin
  source: region.ttAdapter()
});
}




    function init(){
        initAddressSuggest();   
        var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
        $time.val(time1);
        $validateTime.val(2);

        showGoodsType();
    }

    function showTrunkType(){
        $(".goods-required").hide();
        $(".trunk-required").show();
    }

    function showGoodsType(){
        $(".trunk-required").hide();
        $(".goods-required").show();
    }

    function getData(){

        var data = {};

        if($trunkRadio.get(0).checked){
            data.userType = "driver";
            data.billType = "trunk";
        }else if($goodsRadio.get(0).checked){
            data.userType = "owner";
            data.billType = "goods";
        }

        if($nickname.val()==""){
            showTips("称呼不能为空");
            return null;
        }

        if($phoneNum.val()==""){
            showTips("电话号码不能为空");
            return null;
        }

        if(data.billType=="goods" && $goodsName.val()==""){
            showTips("货物名称不能为空");
        }

        if($from.val()==""){
            showTips("出发地不能为空");
            return null;
        }

        if($to.val()==""){
            showTips("目的地不能为空");
            return null;
        }

        if($time.val()==""){
            showTips("发布时间不能为空");
            return null;
        }else{
            var _d = new Date($time.val());
            if (_d == "Invalid Date"){
                showTips("发布时间的格式不对");
                return null;
            }

        }

        if($validateTime.val()==""){
            showTips("有效期不能为空");
            return null;
        }else{
            var _d = +$validateTime.val();
            if (_d == NaN){
                showTips("有效期的格式不对");
                return null;
            }

        }


        debugger;
        data.fromAddr = $from.val();
        data.toAddr = $to.val();
        data.billTime = (+ new Date($time.val()))/1000;//服务器以秒作为单位；
        data.validTimeSec = (+$validateTime.val()) * 24 * 60 * 60; //服务器以秒作为单位；
        data.phoneNum = $phoneNum.val();
        data.comment = $comment.val();
        data.senderName = $nickname.val();

        if(data.userType=="owner"){
            if($goodsPrice.val()!=""){
                data.price = $goodsPrice.val();
            }
            if($goodsWeight.val()!=""){
                data.weight = $goodsWeight.val();
            }
            if($goodsName.val()!=""){
                data.material = $goodsName.val();
            }
        
        }else if(data.userType=="driver"){
            if($trunkType.val()!=""){
                data.trunkType = $trunkType.val();
            }
            if($trunkLength.val()!=""){
                data.trunkLength = $trunkLength.val();
            }
            if($trunkLoad.val()!=""){
                data.trunkLoad = $trunkLoad.val();
            }
            if($licensePlate.val()!=""){
                data.licensePlate = $licensePlate.val();
            }
        }else{
            return null;
        }

        return data;
    }

        //  requiredParams = {
    //     "userType":unicode,
    //     "billType": unicode,

    //     "fromAddr": unicode,
    //     "toAddr": unicode,
    //     "billTime": unicode,
    //     "validTimeSec":unicode
    // }

    // optionalParams = {
    //     "comment":unicode,
    //     "IDNumber": unicode,
    //     "price": unicode,
    //     "weight": unicode,
    //     "material": unicode,

    //     "trunkType": unicode,
    //     "trunkLength": unicode,
    //     "trunkLoad": unicode,
    //     "licensePlate": unicode,
    // } 
    function sendBill(){
        var url = "http://115.29.8.74:9288/api/bill/send";
                   
        var data = getData();
        if(data==null){
            return;
        }

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    showTips("添加成功");
                    // location.href = "/";
                },function(code,msg,data,dataType){
                    
                });
            },

            error: function(data) {
                errLog && errLog("loginAjax");
            }
        });
            
    }

    function reset(){
        $nickname.val("");
        $phoneNum.val("");
        $goodsName.val("");
        $goodsWeight.val("");
        $licensePlate.val("");
        $trunkLength.val("");
        $trunkLoad.val("");
        $from.val("");
        $to.val("");
        $comment.val("");

        var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
        $time.val(time1);
        $validateTime.val(2);
    }

    function bindEvent(){
        $goodsRadio.click(function(){
            showGoodsType();
        });

        $trunkRadio.click(function(){
            showTrunkType();
        });

        $clearBtn.click(function(){
            if(confirm("确定要清空数据吗？")){
                reset();
            }
            
        });
        $confirmBtn.click(function(){
            if(confirm("确定要提交吗？")){
                sendBill();
            }
        });
    }






    bindEvent();
    init();
});