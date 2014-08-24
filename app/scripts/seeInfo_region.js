var _d = [{"芜湖":{"to":0,"from":1},"南充":{"to":0,"from":1},"湛江":{"to":1,"from":1},"乌海":{"to":0,"from":1},"三亚":{"to":1,"from":0},"淄博":{"to":2,"from":0},"昆明":{"to":2,"from":0},"深圳":{"to":3,"from":3},"防城港":{"to":1,"from":0},"长沙":{"to":1,"from":0},"盘锦":{"to":0,"from":1},"烟台":{"to":1,"from":0},"镇江":{"to":0,"from":1},"新乡":{"to":0,"from":1},"宝鸡":{"to":0,"from":1},"不限":{"to":2,"from":0},"江门":{"to":0,"from":2},"德州":{"to":1,"from":0},"大同":{"to":1,"from":0},"乌鲁木齐":{"to":1,"from":0},"唐山":{"to":1,"from":1},"柳州":{"to":1,"from":0},"南宁":{"to":1,"from":0},"东莞":{"to":4,"from":0},"佛山":{"to":1,"from":3},"保定":{"to":1,"from":1},"吉安":{"to":1,"from":0},"菏泽":{"to":1,"from":0},"武汉":{"to":1,"from":0},"吕梁":{"to":0,"from":1},"杭州":{"to":0,"from":2},"临汾":{"to":0,"from":1},"广州":{"to":6,"from":13},"张家口":{"to":0,"from":1},"太原":{"to":1,"from":0},"滨州":{"to":2,"from":0},"清远":{"to":0,"from":1},"沧州":{"to":1,"from":0},"安阳":{"to":0,"from":1},"南京":{"to":0,"from":1},"青岛":{"to":1,"from":0},"东营":{"to":2,"from":0},"济宁":{"to":1,"from":0},"巴彦淖尔":{"to":0,"from":1},"包头":{"to":0,"from":1},"惠州":{"to":0,"from":2},"time":"summary"}]
$(function(){
    var regionStatArray=[];

    var bindEvent = function(){

        $(".regionStat-view-mode").click(function(){
            $(".regionStat-view-mode").removeClass("btn-primary");
            $(".regionStat-view-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");

            getRegionData();
        });

        $(".regionStat-region-mode").click(function(){
            $(".regionStat-region-mode").removeClass("btn-primary");
            $(".regionStat-region-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            getRegionData();
        });

        $(".regionStat-usertype-mode").click(function(){
            $(".regionStat-usertype-mode").removeClass("btn-primary");
            $(".regionStat-usertype-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");
            getRegionData();
        });

        $("#regionStat-region-confirm").click(function(){
            debugger;
            // getRegionDataTest2();
            getRegionData();
        });
    }
 /******************
  * regionStat 数据总览  bengin
  *****************/    

    var getRegionParam = function(){
        var param = {};
        param.viewmode = $(".regionStat-view-mode.btn-primary").data("viewmode");
        param.regionmode = $(".regionStat-region-mode.btn-primary").data("regionmode");
        param.usertype = $(".regionStat-usertype-mode.btn-primary").data("usertype");
        
        if($("#regionStat-date-from").val().length>0){
            console.log(getDate($("#regionStat-date-from").val()));
            try{
                param.from = + getDate($("#regionStat-date-from").val());
            }catch(e){
                return null;
                showTips("起始时间格式不对");
            }
        }

        if($("#regionStat-date-to").val().length>0){
            try{
                param.to = + getDate($("#regionStat-date-to").val());
            }catch(e){
                return null;
                showTips("结束时间格式不对");
            }
        }

        if($("#regionStat-input-search").val().trim()==""){
            param.region = "all";
        }else{
            param.region = $("#regionStat-input-search").val().trim();
        }

        debugger;
        return param;
    }

    var renderRegion = function(array){
        $("#regionStatTable tbody").empty();
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
                    cont += '<span class="region-item">' + v2.region + "[" + v2.from + "," + v2.to + "]" + '</span>';
            });

            // if(v.time != "summary"){
            $("#regionStatTable tbody").append(html.replace("{%tmp%}",cont));
        });

        

    }

    var showRegionChart = function(){
        var chartData = {};
        chartData.labels = [];
        chartData.datasets = [
            {
                fillColor : "rgba(220,220,220,0.5)",
                strokeColor : "rgba(220,220,220,1)",
                pointColor : "rgba(220,220,220,1)",
                pointStrokeColor : "#fff",
                data : [],
                label: "抓取数量",
                name: "toAddMessageCount"
            },
            {
                fillColor : "rgba(255,0,0,0.5)",
                strokeColor : "rgba(255,0,0,1)",
                pointColor : "rgba(255,0,0,1)",
                pointStrokeColor : "#fff",
                data : [],
                label: "忽略数量",
                name:"toAddMessageIgnoreCount"
            },
            {
                fillColor : "rgba(151,187,205,0.5)",
                strokeColor : "rgba(151,187,205,1)",
                pointColor : "rgba(151,187,205,1)",
                pointStrokeColor : "#fff",
                data : [],
                label:"完成数量",
                name:"toAddMessageDoneCount"
            }
            // },
            // {
            //     fillColor : "rgba(0,255,0,0.5)",
            //     strokeColor : "rgba(0,255,0,1)",
            //     pointColor : "rgba(0,255,0,1)",
            //     pointStrokeColor : "#fff",
            //     data : [],
            //     label: "addedMessageCount"
            // }
        ];

        $.each(regionStatArray,function(k,v){
            if(v.time !="summary" || regionStatArray.length<=2){
                chartData.labels.push(v.time);
                chartData.datasets[0].data.push(v.toAddMessageCount);
                chartData.datasets[1].data.push(v.toAddMessageIgnoreCount);
                chartData.datasets[2].data.push(v.toAddMessageDoneCount);  
                // chartData.datasets[3].data.push(v.addedMessageCount);
            }
        });
        $("#regionStatCanvasCantainer").empty();
        $("#regionStatCanvasCantainer").append('<canvas id="regionStatCanvas"></canvas>');
        $("#regionStatCanvas").attr("height",400);
        $("#regionStatCanvas").attr("width",chartData.labels.length * 50 + 100);
        var ctx = $("#regionStatCanvas").get(0).getContext("2d");
        new Chart(ctx).Line(chartData,{
            multiTooltipTemplate:"<%=datasetLabel%>:<%= value %>"
        });

        
    }

    var getRegionData= function(){
        var url = "http://115.29.8.74:9289/stat/summary";
        
        var data = getRegionParam();

        var jqxhr = $.ajax({
            url: url,
            data: data,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    regionStatArray = parseSummaryArray(data);
                    renderRegion(regionStatArray);
                    // showRegionChart(regionStatArray);
                });
            },

            error: function(data) {
                errLog && errLog("getRegionData() error");
            }
        });
    }




    // getRegionDataTest();
    getRegionData();

    getRegionDataTest2 = function(){
        // regionStatArray = parseSummaryArray(_d);
        renderRegion(_d);
    }
     /******************
      * summary 数据总览  end
      *****************/  

    bindEvent();
});
