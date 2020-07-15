/**
 * Created by moonjay on 2020/04/10.
 */
//时间
function fn(){
    var time = new Date();
    var str= "";
    var div = document.getElementById("time");
	var hour = document.getElementById("hours");
//    console.log(time);
    var year = time.getFullYear();
    var mon = time.getMonth()+1;
    var day = time.getDate();
    var h = time.getHours();
    var m = time.getMinutes();
    var s = time.getSeconds();
    var week = time.getDay();
    switch (week){
        case 0:week="日";
            break;
        case 1:week="一";
            break;
        case 2:week="二";
            break;
        case 3:week="三";
            break;
        case 4:week="四";
            break;
        case 5:week="五";
            break;
        case 6:week="六";
            break;
    }
    str = year +"年"+todate(mon)+"月"+todate(day)+"日"+"&nbsp;"+todate(h)+":"+todate(m)+":"+todate(s)+"&nbsp;"+"星期"+week;
    div.innerHTML = str;
	if(h < 6){
		hour.innerHTML = "凌晨好";
	} else if(h < 11){
		hour.innerHTML = "上午好";
	} else if(h < 13){
		hour.innerHTML = "中午好";
	} else if(h < 18){
		hour.innerHTML = "下午好";
	} else if(h < 21){
		hour.innerHTML = "晚上好";
	} else {
		hour.innerHTML = "深夜好";
	}
}
setInterval("fn()","1000");  // 一秒执行一次
function todate(n){
    if(n<=9){
        return n = "0"+n;
    }
    else{
        return n =""+n;
    }
}