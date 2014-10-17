
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
        $clearBtn = $(".clearBtn"),
        $timeType = $("#timeType");
    
    var adminUserId = "53e9cd5915a5e45c43813d1c";
    var numPerPage = 10;
    var addedGoodesMessageData;
    var addedTrunkMessageData;

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
        // var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
        // $time.val(time1);
        // $validateTime.val(2);

        showGoodsType();
    }

    function showTrunkType(){
        $(".goods-required").hide();
        $(".trunk-required").show();
        $timeType.html("回程时间:"); 
    }

    function showGoodsType(){
        $(".trunk-required").hide();
        $(".goods-required").show();
        $timeType.html("发货时间:"); 
    }

    function getReqParams(){

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

        if($from.val()==""){
            showTips("出发地不能为空");
            return null;
        }else{
            if($from.val().indexOf(" ")>=0){
                showTips("出发地不能有空格");
                return null;
            }

            if($from.val().split("-").length !=3 ){
                showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                return null;
            }
        }

        if($to.val()==""){
            showTips("目的地不能为空");
            return null;
        }else{
            if($to.val().indexOf(" ")>=0){
                showTips("目的地不能有空格");
                return null;
            }

            if($to.val().split("-").length !=3 ){
                showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                return null;
            }
        }

        if($time.val()==""){
        }else{
            var getDate = function(str){
                var a = str.split(" ");
                var b1 = a[0].split("-");
                var b2 = a[1].split(":");
                return new Date(b1[0],(b1[1]-1),b1[2],b2[0],b2[1],b2[2])
            }
            try{
                var _d = getDate($time.val());
                data.billTime = (+ _d)/1000;//服务器以秒作为单位；
            }catch(e){
                return null;
                showTips("发布时间的格式不对");
            }
            
        }

        if($validateTime.val()==""){
        }else{
            var _d = +$validateTime.val();
            if (_d == NaN){
                showTips("有效期的格式不对");
                return null;
            }else{
                data.validTimeSec = _d * 24 * 60 * 60; //服务器以秒作为单位；
            }

        }



        data.fromAddr = $from.val();
        data.toAddr = $to.val();
        data.phoneNum = $phoneNum.val();
        data.comment = $comment.val();
        data.senderName = $nickname.val();
        data.sender = adminUserId;
        data.userId = adminUserId;
        data.qqgroup = $("#qqgroup").val();
        data.qqgroupid = $("#qqgroupid").val();

        if(data.userType=="owner"){
            if($goodsPrice.val()!=""){
                data.price = $goodsPrice.val();
            }
            if($goodsWeight.val()!=""){
                data.weight = $goodsWeight.val();
            }
            if($goodsName.val()!=""){
                data.material = $goodsName.val();
            }else{
                data.material = "普货";
            }
        
        }else if(data.userType=="driver"){

            $(".trunkType").each(function(k,v){
                if(v.checked){
                    if($(v).val()!="未知车型"){
                        data.trunkType = $(v).val();
                    }
                }
            });
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
        var url = "http://115.29.8.74:9289/message/send";
                   
        var param = getReqParams();
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
                    $confirmBtn.tooltip({
                        "animation":true,
                        "placement":"top",
                        "title":"发送成功"
                    }).tooltip('show');
                    setTimeout(function(){
                        $confirmBtn.tooltip("hide");
                        $confirmBtn.tooltip("destroy");
                    },1000);

                    sendBill2();
                });
            },

            error: function(data) {
                errLog && errLog("/api/bill/send error");
            }
        });
    }
    function sendBill2(){
        var url = "http://115.29.8.74:9288/api/bill/send";
                   
        var param = getReqParams();
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
                    getBill(param.userType);
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("/api/bill/send error");
            }
        });
    }


    function getBill(type){
        var url = "http://115.29.8.74:9288/api/bill/get";
        
        var data = {
            userId : adminUserId,
            userType : type
        }

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;

                    if(type == "driver"){
                        renderDriver(data);
                        addedTrunkMessageData = data;
                    }else{
                        renderOwner(data);
                        addedGoodesMessageData = data;
                    }
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("api/bill/get error");
            }
        });
    }

    function getBill2(type){
        var url = "http://115.29.8.74:9289/message/getVerifying";
        
        var data = {
            userType : type,
            username : G_data.admin.username 
        }

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;

                    if(type == "driver"){
                        renderDriver(data);
                        addedTrunkMessageData = data;
                    }else{
                        renderOwner(data);
                        addedGoodesMessageData = data;
                    }
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("api/bill/get error");
            }
        });
    }

      

    var secondToHour = function(seconds){
        return seconds/60/24/60 + "天";
    }

  // <th>称呼</th>
  // <th>电话号码</th>
  // <th>车辆类型</th>
  // <th>车长</th>
  // <th>载重</th>
  // <th>车牌</th>
  // <th>出发地</th>
  // <th>目的地</th>
  // <th>回程时间</th>
  // <th>有效期</th>
  // <th>备注</th>
  // <th>操作</th>
    var renderDriver = function(data){

        var page = page || 1;

        var renderPage = function(data){
            var pageNum = data.length/ numPerPage;

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
            $(".driverPaginationWrapper").empty();
            $(".driverPaginationWrapper").append(html);
            $(".driverPaginationWrapper").data("current",page);
        }

        var renderItem = function(data){
            var template = '<tr id="tr_'+ data.id +'">\
              <td>'+ data.senderName +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.trunkType +'</td>\
              <td>'+ data.trunkLength +'</td>\
              <td>'+ data.trunkLoad +'</td>\
              <td>'+ data.licensePlate +'</td>\
              <td>'+ data.fromAddr +'</td>\
              <td>'+ data.toAddr +'</td>\
              <td>'+ (data.billTime ?  Datepattern(new Date(data.billTime * 1000),"yyyy-MM-dd HH:mm:ss") : "")    +'</td>\
              <td>'+ secondToHour(data.validTimeSec)    +'</td>\
              <td>'+ data.comment  +'</td>\
              <td>\
                <div class="btn-group btn-group-lg" data-usertype="driver" data-id= "'+ data.id+'"">\
                  <button type="button" class="btn btn-danger fail">删除</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        var from = (page -1) * numPerPage;
        var count = count || data.length;

        $("#trunkList").empty();

        renderPage(data);
        for (var i = data.length-1- from; i >= data.length-from - numPerPage ; i--) {
            $("#trunkList").append(renderItem(data[i]));
        };
    }

  // <th>称呼</th>
  // <th>电话号码</th>
  // <th>货物名称</th>
  // <th>重量</th>
  // <th>目标价格</th>
  // <th>出发地</th>
  // <th>目的地</th>
  // <th>发货时间</th>
  // <th>有效期</th>
  // <th>备注</th>
  // <th>操作</th>
    var renderOwner = function(data,page){

        var page = page || 1;

        var renderPage = function(data){
            var pageNum = data.length/ numPerPage;

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
            $(".ownerPaginationWrapper").empty();
            $(".ownerPaginationWrapper").append(html);
            $(".ownerPaginationWrapper").data("current",page);
        }

        var renderItem = function(data){
            var template = '<tr id="tr_'+ data.id +'">\
              <td>'+ data.senderName +'</td>\
              <td>'+ data.phoneNum +'</td>\
              <td>'+ data.material +'</td>\
              <td>'+ data.weight +'</td>\
              <td>'+ data.price +'</td>\
              <td>'+ data.fromAddr +'</td>\
              <td>'+ data.toAddr +'</td>\
              <td>'+ (data.billTime ?  Datepattern(new Date(data.billTime * 1000),"yyyy-MM-dd HH:mm:ss") : "" )   +'</td>\
              <td>'+ secondToHour(data.validTimeSec)    +'</td>\
              <td>'+ data.comment  +'</td>\
              <td>\
                <div class="btn-group btn-group-lg" data-usertype="owner" data-id= "'+ data.id+'"">\
                  <button type="button" class="btn btn-danger fail">删除</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        var from = (page -1) * numPerPage;
        var count = count || data.length;

        $("#goodsList").empty();

        renderPage(data);
        for (var i = data.length-1- from; i >= data.length-from - numPerPage ; i--) {
            $("#goodsList").append(renderItem(data[i]));
        };
    }




    function getToAddMessage(type){
        var url = "http://115.29.8.74:9289/message/get";
        

        var jqxhr = $.ajax({
            url: url,
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    renderToAddMessage(data);
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("getToAddMessage");
            }
        });
    }

     // <th>昵称</th>
     //  <th>电话号码</th>
     //  <th>群号</th>
     //  <th>群名称</th>
     //  <th>时间</th>
     //  <th>内容</th>
     //  <th>操作</th>

    var renderToAddMessage = function(data){
        var renderItem = function(data){
            var template = '<tr id="tr_'+ data._id.$oid +'">\
              <td>'+ data.nickname +'</td>\
              <td>'+ data.phonenum +'</td>\
              <td>'+ data.groupname +'</td>\
              <td>'+ data.groupid +'</td>\
              <td>'+ Datepattern(new Date(+data.time),"yyyy-MM-dd HH:mm:ss")    +'</td>\
              <td>'+ data.content  +'</td>\
              <td>\
                <div class="btn-group" data-id= "'+ data._id.$oid+'"">\
                  <button type="button" class="btn btn-danger fail">忽略</button>\
                  <button type="button" class="btn btn-primary done">完成</button>\
                  <button type="button" class="btn btn-success smart_add">添加</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        $("#toAddMessageBody").empty();
        var len = data.length>100? 100: data.length;

        for (var i=0;i<data.length;i++){
            $("#toAddMessageBody").append(renderItem(data[i]));
        };
    }

    getBill("driver");
    getBill("owner");
    getToAddMessage();

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

        // var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
        $time.val("");
        $validateTime.val("");
        $("#qqgroupid").val("");
        $("#qqgroup").val("");
    }


    function bindEvent(){
        $goodsRadio.click(function(){
            showGoodsType();
            if($nickname.val()=="车源"){
                $nickname.val("货源");
            }
        });

        $trunkRadio.click(function(){
            showTrunkType();
            if($nickname.val()=="货源"){
                $nickname.val("车源");
            }
        });

        $("#updateTime").click(function(){
            var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
            $time.val(time1);
        });

        $("#normalGoods").click(function(){
            $goodsName.val("普货");
        });

        $("#normalNickname").click(function(){

            if($trunkRadio.get(0).checked){
                $nickname.val("车源");
            }else if($goodsRadio.get(0).checked){
                $nickname.val("货源");
            }
            
        })

        $clearBtn.click(function(){
            // if(confirm("确定要清空数据吗？")){
                reset();
            // }
        
        });
        $confirmBtn.click(function(){
            // if(confirm("确定要提交吗？")){
                sendBill();
            // }
        });
        

        var small_2_on = true;
        $("#small_2").click(function(){
            if(small_2_on){
                $(this).html("展开");
                small_2_on = false;
                $("#toAddMessageContainer").hide();
            }else{
                $(this).html("收起");
                small_2_on = true;
                $("#toAddMessageContainer").show();
            }
        });

        var small_on = true;
        $("#small").click(function(){
            if(small_on){
                $(this).html("展开");
                small_on = false;
                $("#addedMessageContainer").hide();
            }else{
                $(this).html("收起");
                small_on = true;
                $("#addedMessageContainer").show();
            }
        });

        var hasFullScreen = false;
        $(".fullscreen").click(function(){
            if(!hasFullScreen){
                $(".fullscreen").html("退出全屏");
                $(".my-panel").hide();
                $(".added-list").removeClass("col-sm-8");
                $(".added-list").addClass("col-sm-12");
                hasFullScreen = true;
            }else{
                $(".fullscreen").html("全屏");
                $(".my-panel").show();
                $(".added-list").removeClass("col-sm-12");
                $(".added-list").addClass("col-sm-8");
                hasFullScreen = false;
            }
        });


        var fixed = false;
        $("#my_panel_fixed").click(function(){
            if(!fixed){
                $("#my_panel_fixed").html("滚动");
                $(".my-panel").css({"position":"fixed"});
                $(".my-panel").css("top","72px");
                fixed = true;
            }else{
                $("#my_panel_fixed").html("固定");
                $(".my-panel").css({"position":"inherit"});
                $(".my-panel").css("top","0px");
                fixed = false;
            }
        });
        
        $("#getToAddMessage").click(function(){
            getToAddMessage();
        });



        $("#goodsList").delegate(".fail","click",function(){

            if(!confirm("确定要删除这条请求吗？")){
                return;
            }
            debugger;
            var $this = $(this),
                id = $this.parents().data("id");

            var tds = $("#tr_"+ id).find("td");
            var d = {
                phoneNum : tds.eq(1).html(),
                fromAddr : tds.eq(5).html(),
                toAddr : tds.eq(6).html(),
                userType : $this.parents().data("usertype")
            }

            debugger


            var jqxhr = $.ajax({
                url: "/addedmessage/delete",
                data: d,
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger; 
                        // location.href = "/";
                        realDelete();
                    });
                },

                error: function(data) {
                    errLog && errLog("api/bill/remove error");
                }
            });

            var realDelete = function(){
                var jqxhr = $.ajax({
                    url: "http://115.29.8.74:9288/api/bill/remove",
                    data: {
                        "billid": id,
                        "userId": adminUserId,
                        "userType": "owner"
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
                        errLog && errLog("http://115.29.8.74:9288/api/bill/remove error");
                    }
                });
            }
            
            return false;
        });


        $("#trunkList").delegate(".fail","click",function(){
            debugger;
            if(!confirm("确定要删除这条请求吗？")){
                return;
            }
            var $this = $(this),
                id = $this.parents().data("id");

            var tds = $("#tr_"+ id).find("td");
            var d = {
                phoneNum : tds.eq(1).html(),
                fromAddr : tds.eq(6).html(),
                toAddr : tds.eq(7).html(),
                userType : $this.parents().data("usertype")
            }


            var jqxhr = $.ajax({
                url: "http://115.29.8.74:9289/addedmessage/delete",
                data: d,
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger; 
                        // location.href = "/";
                        realDelete();
                    });
                },

                error: function(data) {
                    errLog && errLog("addedmessage/delete error");
                }
            });

            var realDelete = function(){
                var jqxhr = $.ajax({
                    url: "http://115.29.8.74:9288/api/bill/remove",
                    data: {
                        "billid": id,
                        "userId": adminUserId,
                        "userType": "driver"
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
                        errLog && errLog("api/bill/remove error");
                    }
                });
            }
            return false;
        });

        $("#toAddMessageBody").delegate(".fail","click",function(){

            debugger;
            var $this = $(this),
                id = $this.parents().data("id");
            var jqxhr = $.ajax({
                url: "http://115.29.8.74:9289/message/delete",
                data: {
                    "id": id,
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
                    errLog && errLog("/message/delete error");
                }
            });
            return false;
        });
        
        $("#toAddMessageBody").delegate(".done","click",function(){

            debugger;
            var $this = $(this),
                id = $this.parents().data("id");

            var jqxhr = $.ajax({
                url: "http://115.29.8.74:9289/message/done",
                data: {
                    "id": id,
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
                    errLog && errLog("message/done error");
                }
            });
            return false;
        });

        $("#toAddMessageBody").delegate(".smart_add","click",function(){
            var $this = $(this),
                id = $this.parents().data("id");

            var $tds = $("#tr_" + id).find("td");
            reset();
            $nickname.val($tds.eq(0).html());
            $phoneNum.val($tds.eq(1).html().split("-").join(""));

            $("#qqgroup").val($tds.eq(2).html());
            $("#qqgroupid").val($tds.eq(3).html());
            // $time.val($tds.eq(2).html());

            var a = $tds.eq(5).html().split("<br>").join();
            function isImportantData(str){
                var pattern=/\d{11}|\d{7,8}|\d{3,4}-\d{7,8}/;
                var ret = pattern.exec(str);
                if(ret){
                    return ret[0];
                }else{
                    return false;
                }
            }

            function getWeight(str){
                var pattern=/\d+吨|\d+.\d+吨/;
                var ret = pattern.exec(str);
                if(ret){
                    return ret[0];
                }else{
                    return false;
                }
            }

            var weight = getWeight(a);

            if(weight){
                $goodsWeight.val(weight.split("吨").join(""));
            }

            var phone = isImportantData(a);
            if(phone){
                a = a.split(phone).join().trim();
                a = a.replace(/,+/g,",").replace(/，+/,"，");

                if(a[a.length-1] == "，" || a[a.length-1] == ","){
                    a = a.substring(a,a.length-1);
                }
                $comment.val(a);
            }else{
                $comment.val(a);
            }


        });

        $(".ownerPaginationWrapper").delegate(".pageLi","click",function(){
            var index = +$(this).html();
            $(".ownerPaginationWrapper").data("current",index);
            renderOwner(addedGoodesMessageData,index);
        });

        $(".driverPaginationWrapper").delegate(".pageLi","click",function(){
            var index = +$(this).html();
            $(".driverPaginationWrapper").data("current",index);
            renderDriver(addedTrunkMessageData,index);
        });

        window.onscroll = function () { 
            var top = document.documentElement.scrollTop || document.body.scrollTop;
            if(top>0 && fixed){
                $(".my-panel").css("top", "10px");
            }else{
                if(fixed){
                    $(".my-panel").css("top","72px");
                }else{
                    $(".my-panel").css("top","0px");
                }
            }
        }
    }

    bindEvent();
    init();
});