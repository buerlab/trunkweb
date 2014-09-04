$(function() {
    var adminUserId = "53e9cd5915a5e45c43813d1c";
    var safeRender =function(key){
        if (key){
            return key;
        }else{
            return "";
        }
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

    var getData = function(){
        var url = "http://115.29.8.74:9288/api/get_match";
        
        var jqxhr = $.ajax({
            url: url,
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    renderTitle(data);
                });
            },

            error: function(data) {
                errLog && errLog("api/get_match error");
            }
        });
    }

    var renderTitle = function(data){
        $(".match-route").empty();

        $.each(data,function(k,v){
            // var template = '<a href="javascript:void(0);" data-data=\'{data}\' class="menu-item list-group-item">{route}\
            //     <span class="badge goodes-count">货源{goodes-count}</span>\
            //     <span class="badge trunk-count">车源{trunk-count}</span>\
            //   </a>';


             var template ='<a href="javascript:void(0);" class="menu-item list-group-item" data-data=\'{data}\'>\
                <span class="pull-left route">{route}</span>\
                <span class="badge pull-left goodes-count">货源{goodes-count}</span>\
                <span class="badge pull-left trunk-count">车源{trunk-count}</span>\
                <div class="clearfix"></div>\
              </a><div class="data-list clearfix" data-route="{route}" style="display:none">\
                <div class="col-sm-3">\
                  <h3>货源</h3>\
                  <div class="goods-list"></div>\
                </div>\
                <div class="col-sm-3">\
                  <h3>车源</h3>\
                  <div class="trunk-list"></div>\
                </div>\
              </div>';
              debugger;
            var html = template.replace(/{route}/g,k.replace("->","→"))
                            .replace(/{goodes-count}/g,v.goods.length)
                            .replace(/{trunk-count}/g,v.trunk.length)
                            .replace(/{data}/g,JSON.stringify(v));

            $(".match-route").append(html);
        });
    }

    // getData();


    var getGoodsBill = function(id,container,index){
        var url = "http://115.29.8.74:9288/api/bill/get_one";
        // renderGoodsItem(data,container,index);

        var jqxhr = $.ajax({
            url: url,
            data: {
                billId:id
            },
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    renderGoodsItem(data,container,index);
                });
            },

            error: function(data) {
                errLog && errLog("getGoodsBill");
            }
        });
    }

    var getGoodsBillTest = function(id,container,index){
        renderGoodsItem(_d,container,index);
        
    }

    var _d ={"comment":"今天东莞厚街装海绵回中山，要一个9.6米以上车子，有车马上联系","IDNumber":"","material":"普货","visitedTimes":14,"receiver":"","weight":0,"fromAddr":"广东-东莞-南城","price":0,"trunkLoad":0,"phoneNum":"13829249901","id":"54040e597938ee519051e2af","validTimeSec":86400,"toAddr":"广东-中山-不限","sendTime":1409551961,"trunkType":"","passAddr":[],"senderName":"货源","trunkLength":0,"billType":"goods"}
    var renderGoodsItem = function(data,container,index){
        var template = '<div id="item_{id}" class="goods-item">\
                      <p><span class="sub-text">序号:</span><span class="value-text id-text">{index}</span></p>\
                      <p><span class="sub-text">id:</span><span class="value-text id-text">{id}</span></p>\
                      <p><span class="sub-text">称呼:</span><span class="value-text senderName-text">{senderName}</span></p>\
                      <p><span class="sub-text">电话号码:</span><span class="value-text phoneNum-text">{phoneNum}</span></p>\
                      <p><span class="sub-text">出发地:</span><span class="value-text from-text">{fromAddr}</span></p>\
                      <p><span class="sub-text">目的地:</span><span class="value-text to-text">{toAddr}</span></p>\
                      <p><span class="sub-text">货物名称:</span><span class="value-text material-text">{material}</span></p>\
                      <p><span class="sub-text">重量:</span><span class="value-text weight-text">{weight}</span></p>\
                      <p><span class="sub-text">价格:</span><span class="value-text price-text">{price}</span></p>\
                      <p><span class="sub-text">发货时间:</span><span class="value-text billTime-text">{billTime}</span></p>\
                      <p><span class="sub-text">有效期:</span><span class="value-text validTimeSec-text">{validTimeSec}</span></p>\
                      <p><span class="sub-text">发布时间:</span><span class="value-text sendtsendTimeime-text">{sendTime}</span></p>\
                      <p><span class="sub-text">备注:</span><span class="value-text comment-text">{comment}</span></p>\
                      <p><span class="sub-text">操作:</span><a herf="javascript:void(0);" data-id="{id}" data-type="owner"  class="value-text delete btn btn-danger">删除</a></p>\
                    </div>';
        var html = template.replace(/{index}/g,index)
                            .replace(/{id}/g,data.id)
                            .replace(/{senderName}/g,safeRender(data.senderName))
                            .replace(/{phoneNum}/g,safeRender(data.phoneNum))
                            .replace(/{fromAddr}/g,data.fromAddr)
                            .replace(/{toAddr}/g,data.toAddr)
                            .replace(/{material}/g,data.material)
                            .replace(/{weight}/g,safeRender(data.weight))
                            .replace(/{price}/g,safeRender(data.price))
                            .replace(/{billTime}/g,data.billTime? Datepattern(new Date((+data.billTime) * 1000),"yyyy-MM-dd HH:mm:ss") : "")
                            .replace(/{validTimeSec}/g,data.validTimeSec ?  data.validTimeSec/(24 * 60 * 60) +"天" : "")
                            .replace(/{comment}/g,safeRender(data.comment))
                            .replace(/{sendTime}/g,Datepattern(new Date((+data.sendTime) * 1000),"yyyy-MM-dd HH:mm:ss"))
                            
        container.append(html);

        debugger;
    }

    var getTrunkBill = function(id,container,index){
        var url = "http://115.29.8.74:9288/api/bill/get_one";
        // renderGoodsItem(data,container,index);

        var jqxhr = $.ajax({
            url: url,
            data: {
                billId:id
            },
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    renderTrunkItem(data,container,index);
                });
            },

            error: function(data) {
                errLog && errLog("getTrunkBill");
            }
        });
    }

    var getTrunkBillTest = function(id,container,index){
        renderTrunkItem(_d,container,index);
        
    }
     
    var renderTrunkItem = function(data,container,index){
        var template = '<div id="item_{id}" class="trunk-item">\
                      <p><span class="sub-text">序号:</span><span class="value-text id-text">{index}</span></p>\
                      <p><span class="sub-text">id:</span><span class="value-text id-text">{id}</span></p>\
                      <p><span class="sub-text">称呼:</span><span class="value-text senderName-text">{senderName}</span></p>\
                      <p><span class="sub-text">电话号码:</span><span class="value-text phoneNum-text">{phoneNum}</span></p>\
                      <p><span class="sub-text">出发地:</span><span class="value-text from-text">{fromAddr}</span></p>\
                      <p><span class="sub-text">目的地:</span><span class="value-text to-text">{toAddr}</span></p>\
                      <p><span class="sub-text">车长:</span><span class="value-text trunkLength-text">{trunkLength}</span></p>\
                      <p><span class="sub-text">载重:</span><span class="value-text trunkLoad-text">{trunkLoad}</span></p>\
                      <p><span class="sub-text">车辆类型:</span><span class="value-text trunkType-text">{trunkType}</span></p>\
                      <p><span class="sub-text">回程时间:</span><span class="value-text billTime-text">{billTime}</span></p>\
                      <p><span class="sub-text">有效期:</span><span class="value-text validTimeSec-text">{validTimeSec}</span></p>\
                      <p><span class="sub-text">发布时间:</span><span class="value-text sendtsendTimeime-text">{sendTime}</span></p>\
                      <p><span class="sub-text">备注:</span><span class="value-text comment-text">{comment}</span></p>\
                      <p><span class="sub-text">操作:</span><a herf="javascript:void(0);" data-id="{id}" data-type="driver" class="value-text delete btn btn-danger">删除</a></p>\
                    </div>';
        var html = template.replace(/{index}/g,index)
                            .replace(/{id}/g,data.id)
                            .replace(/{senderName}/g,safeRender(data.senderName))
                            .replace(/{phoneNum}/g,safeRender(data.phoneNum))
                            .replace(/{fromAddr}/g,data.fromAddr)
                            .replace(/{toAddr}/g,data.toAddr)
                            .replace(/{trunkLength}/g,data.trunkLength + "米")
                            .replace(/{trunkLoad}/g,safeRender(data.trunkLoad)+"吨")
                            .replace(/{trunkType}/g,data.trunkType ? safeRender(data.trunkType) : "未知车型")
                            .replace(/{billTime}/g,data.billTime? Datepattern(new Date((+data.billTime) * 1000),"yyyy-MM-dd HH:mm:ss") : "")
                            .replace(/{validTimeSec}/g,data.validTimeSec ?  data.validTimeSec/(24 * 60 * 60) +"天" : "")
                            .replace(/{comment}/g,safeRender(data.comment))
                            .replace(/{sendTime}/g,Datepattern(new Date((+data.sendTime) * 1000),"yyyy-MM-dd HH:mm:ss"))
                            
        container.append(html);

        debugger;
    }

    $(".match-route").delegate(".menu-item","click",function(){
        debugger;
          

        if($(this).hasClass("active")){
            $(".menu-item").removeClass("active");
            $(".data-list").hide();
        }else{
            $(".menu-item").removeClass("active");
            $(this).addClass("active");
            var route = $(this).find(".route").html();
            $(".data-list").hide();
            var $datalist = $(".data-list[data-route=\'"+route +"\']");
            $datalist.show();
            // getGoodsBillTest("",$datalist.find(".goods-list"),1); 
            var titleData = $(this).data("data");

            if(!$datalist.data("renderData") ){

                $datalist.find(".goods-list").empty();
                $datalist.find(".trunk-list").empty();
                if(!titleData){
                    showTips("没有数据");
                    return;
                }
                for(var i =0;i<titleData.goods.length;i++){
                    getGoodsBill(titleData.goods[i],$datalist.find(".goods-list"),i+1);
                    // getGoodsBillTest(titleData.goods[i],$datalist.find(".goods-list"),i+1);
                }
                for(var i =0;i<titleData.trunk.length;i++){
                    getTrunkBill(titleData.trunk[i],$datalist.find(".trunk-list"),i+1);
                    // getGoodsBillTest(titleData.goods[i],$datalist.find(".goods-list"),i+1);
                }
                $datalist.data("renderData",true);
            }
        }
        
    });

    var realDelete = function(id, _type){
        var jqxhr = $.ajax({
            url: "http://115.29.8.74:9288/api/bill/remove",
            data: {
                "billid": id,
                "userId": adminUserId,
                "userType": _type
            },
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger; 
                    $("#item_"+id).remove();
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("api/bill/remove error");
            }
        });
    }

    $(".match-route").delegate(".delete","click",function(){
        realDelete($(this).data("id"),$(this).data("type"));
    });

    

    getData();
});