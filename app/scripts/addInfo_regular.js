$(function(){
    $("#toAddMessageBody").delegate(".smart_add","click",function(){
        if (G_data.currentAddInfoMode !="regular"){
            return;
        }
        modifyingId = null;
        var $this = $(this),
            id = $this.parents().data("id");

        var $tds = $("#tr_" + id).find("td");
        reset();
        $("#regularNickname").val($tds.eq(0).html());
        $("#regularPhoneNum").val($tds.eq(1).html().split("-").join(""));

        $("#regularQQgroup").val($tds.eq(2).html());
        $("#regularQQgroupid").val($tds.eq(3).html());

        // $time.val($tds.eq(2).html());

        var a = $tds.eq(5).html().split("<br>").join("");
        $("#regularComment").val(a);

    }); 


    function showTrunkType(){
        $(".goods-required").hide();
        $(".trunk-required").show();
    }

    function showGoodsType(){
        $(".trunk-required").hide();
        $(".goods-required").show();
    }

    $("#regularGoodsRadio").click(function(){
        showGoodsType();
        if($("#regularNickname").val()=="车源"){
            $("#regularNickname").val("货源");
        }
    });

    $("#regularTrunkRadio").click(function(){
        showTrunkType();
        if($("#regularNickname").val()=="货源"){
            $("#regularNickname").val("车源");
        }
    });

    $("#regularNormalNickname").click(function(){

            if($("#regularTrunkRadio").get(0).checked){
                $("#regularNickname").val("车源");
            }else if($("#regularGoodsRadio").get(0).checked){
                $("#regularNickname").val("货源");
            }
            
        })

    $(".regularClearBtn").click(function(){
        // if(confirm("确定要清空数据吗？")){
            reset();
        // }
    
    });
    $(".regularConfirmBtn").click(function(){
        // if(confirm("确定要提交吗？")){
            addRegular();
        // }
    });

    $("#regularForm").delegate(".regular-add","click",function(){
        var temp = '<div class="regular-item">\
                  <div class="panel panel-default">\
                    <div class="panel-heading">\
                      <h3 class="panel-title">常规路线\
                        <div class="btn-group">\
                          <button type="button" class="btn btn-success regular-add">新增</button>\
                          <button type="button" class="btn btn-danger regular-delete">删除</button>\
                      </div>\
                      </h3>\
                    </div>\
                  <div class="form-group">\
                    <label for="from" class="col-sm-4 control-label"><span class="required">*</span>出发地:</label>\
                    <div class="col-sm-8 from-route-list">\
                        <input type="text" class="form-control typeahead from-route-value" placeholder="比如：广东-广州-天河">\
                    </div>\
                  </div>\
                  <div class="form-group">\
                    <label for="to" class="col-sm-4 control-label"><span class="required">*</span>目的地:</label>\
                    <div class="col-sm-8 to-route-list">\
                        <input type="text" class="form-control typeahead to-route-value" placeholder="比如：广东-广州-天河">\
                    </div>\
                  </div>\
                  <div class="form-group">\
                    <label class="col-sm-4 control-label">概率:</label>\
                    <div class="col-sm-8">\
                      <input type="text" class="form-control route-probability" placeholder="0 到 1 之间，可不填">\
                    </div>\
                  </div>\
                </div>';
        $("#regularList").append(temp);
        debugger;
        initTypeahead($(".regular-item").last().find(".typeahead"));

        });

    $("#regularForm").delegate(".regular-delete","click",function(){
        debugger;
        if($(".regular-item").size() <=1){
            showTips("至少一条线路");
            return;
        }
        $(this).parents().filter(".regular-item").remove();
    });


    function getReqParams(){

        var data = {};

        if($("#regularTrunkRadio").get(0).checked){
            data.userType = "driver";
        }else{
            data.userType = "owner";
        }

        $(".regularRole").each(function(k,v){
            if(v.checked){
                data.role = $(v).val();
            }
        });


        if($("#regularNickname").val()==""){
            showTips("称呼不能为空");
            return null;
        }

        if($("#regularPhoneNum").val()==""){
            showTips("电话号码不能为空");
            return null;
        }else{
            if(!isPhoneData($("#regularPhoneNum").val())){
                showTips("电话号码格式不对");
                return null
            }
        }

        $(".from-route-value.tt-input").each(function(k,v){
            if($(v).val()==""){
                showTips("出发地不能为空");
                return null;
            }else{
                if($(v).val().indexOf(" ")>=0){
                    showTips("出发地不能有空格");
                    return null;
                }

                if($(v).val().split("-").length !=3 ){
                    showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                    return null;
                }
            }
        });

        $(".to-route-value.tt-input").each(function(k,v){
            if($(v).val()==""){
                showTips("目的地不能为空");
                return null;
            }else{
                if($(v).val().indexOf(" ")>=0){
                    showTips("目的地不能有空格");
                    return null;
                }

                if($(v).val().split("-").length !=3 ){
                    showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                    return null;
                }
            }
        });

        if(+$("#regularTrunkLength").val() +"" == "NaN"){
            showTips("货车长度必须是数字");
            return null;
        }

        if(+$("#regularTrunkLoad").val() +"" == "NaN"){
            showTips("载重必须是数字");
            return null;
        }

        var routes = []
        $(".regular-item").each(function(k,v){
            var route = {};
            route.fromAddr = $(v).find(".from-route-value.tt-input").val();
            route.toAddr = $(v).find(".to-route-value.tt-input").val();
            if($(v).find(".route-probability").val()!=""){
                var _d = +$(v).find(".route-probability").val();
                if(_d +"" == "NaN"){
                    showTips("概率必须是0到1之间的数字");
                    return null;
                }
                if(_d<0 || _d >1){
                    showTips("概率必须是0到1之间的数字");
                    return null;
                }

                route.probability = _d;
            }else{
                route.probability = -1;
            }
            routes.push(route);
        });
        data.routes = JSON.stringify(routes);


        data.phoneNum = $("#regularPhoneNum").val();
        data.comment = $("#regularComment").val();
        data.nickName = $("#regularNickname").val();
        data.qqgroup = $("#regularQQgroup").val();
        data.qqgroupid = $("#regularQQgroupid").val();
        
        data.editor = G_data.admin.username || "default";
        data.time = +(new Date());
        if(data.userType=="driver"){

            $(".regularTrunkType").each(function(k,v){
                if(v.checked){
                    if($(v).val()!="未知车型"){
                        data.trunkType = $(v).val();
                    }
                }
            });
            if($("#regularTrunkLength").val()!=""){
                data.trunkLength = $("#regularTrunkLength").val();
            }
            if($("#regularTrunkLoad").val()!=""){
                data.trunkLoad = $("#regularTrunkLoad").val();
            }
        }

        return data;
    }

    function addRegular(){
        var data = getReqParams();
        var url = "http://115.29.8.74:9288/api/regular/add";

            var jqxhr = $.ajax({
                url: url,
                data: data,
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger;
                        $(".regularConfirmBtn").tooltip({
                        "animation":true,
                        "placement":"top",
                        "title":"发送成功"
                        }).tooltip('show');
                        setTimeout(function(){
                            $(".regularConfirmBtn").tooltip("hide");
                            $(".regularConfirmBtn").tooltip("destroy");
                        },1000);
                    });
                },
                error: function(data) {
                    errLog && errLog("http://115.29.8.74:9288/api/regular/get error");
                }
            });
    }


    function reset(){
        debugger;
        $("#regularNickname").val("");
        $("#regularPhoneNum").val(""); 
        $("#regularQQgroup").val("");
        $("#regularQQgroupid").val("");
        $("#regularComment").val("");
        $(".from-route-value.tt-input").val("");
        $(".to-route-value.tt-input").val("");
    }
});