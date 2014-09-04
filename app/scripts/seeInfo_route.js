$(function(){
    var routeStatArray=[];

    var bindEvent = function(){

        $(".routeStat-view-mode").click(function(){
            $(".routeStat-view-mode").removeClass("btn-primary");
            $(".routeStat-view-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");

            getRouteData();
        });

        $(".routeStat-region-mode").click(function(){
            $(".routeStat-region-mode").removeClass("btn-primary");
            $(".routeStat-region-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            getRouteData();
        });

        $(".routeStat-usertype-mode").click(function(){
            $(".routeStat-usertype-mode").removeClass("btn-primary");
            $(".routeStat-usertype-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            getRouteData();
        });

        $("#routeStat-region-confirm").click(function(){
            debugger;
            // getRegionDataTest2();
            getRouteData();
        });
    }
 /******************
  * routeStat 数据总览  bengin
  *****************/    

    var getParam = function(){
        var param = {};
        param.viewmode = $(".routeStat-view-mode.btn-primary").data("viewmode");
        param.regionmode = $(".routeStat-region-mode.btn-primary").data("regionmode");
        param.usertype = $(".routeStat-usertype-mode.btn-primary").data("usertype");
        param.routemode = true;

        if($("#routeStat-date-from").val().length>0){
            console.log(getDate($("#routeStat-date-from").val()));
            try{
                param.from = + getDate($("#routeStat-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#routeStat-date-to").val().length>0){
            try{
                param.to = + getDate($("#routeStat-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }

        if($("#routeStat-input-search").val().trim()==""){
            param.region = "all";
        }else{
            param.region = $("#routeStat-input-search").val().trim();
        }

        debugger;
        return param;
    }

    var renderRegion = function(array){
        $("#routeStatTable tbody").empty();
        debugger;
         
        
        $.each(array,function(k,v){
            var html = '<tr><td>'+ v.time+'</td>'+
                        '<td> {%tmp%} </td>' +
                        '</tr>';
            var cont="";

            var regionItemArray =  [];
            $.each(v,function(k2,v2){
                if(k2 != "time"){
                    v2.region = k2;
                    regionItemArray.push(v2);
                }
            });

            regionItemArray.sort(function(a,b){
                return -(a.to + a.from - b.to - b.from);
            });

            $.each(regionItemArray,function(k2,v2){
                    cont += '<span class="route-item">' + v2.region + "[" + v2.count + "]" + '</span>';
            });

            // if(v.time != "summary"){
            $("#routeStatTable tbody").append(html.replace("{%tmp%}",cont));
        });

    }


    var getRouteData= function(){
        var url = "http://localhost:9289/stat/summary";
        
        var data = getParam();

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    routeStatArray = parseSummaryArray(data);
                    renderRegion(routeStatArray);
                    // showRegionChart(routeStatArray);
                });
            },

            error: function(data) {
                errLog && errLog("getRouteData() error");
            }
        });
    }




    // getRegionDataTest();
    getRouteData();

    // getRegionDataTest2 = function(){
    //     // routeStatArray = parseSummaryArray(_d);
    //     renderRegion(_d);
    // }
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();
});
